import json
import datetime
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils.knn_classifier import KNNAnomalyDetector
from .db_utils import save_traffic_and_incidents  # pyright: ignore[reportMissingImports]

# Scapy capture imports
from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP
from collections import defaultdict, deque
import time
from asgiref.sync import sync_to_async

def _port_to_service(port: int | None) -> str | None:
    if port is None:
        return None
    mapping = {
        80: "http",
        443: "https",
        53: "dns",
        22: "ssh",
        21: "ftp",
        25: "smtp",
        110: "pop3",
        143: "imap",
        3389: "rdp",
        3306: "mysql",
        5432: "postgres",
    }
    return mapping.get(int(port))

def _classify_attack_type(rate: float, is_sm_ips_ports: int, proto: str, state: str, 
                          service: str, spkts: int, dpkts: int, sjit: float, djit: float) -> str:
    """Classify the type of attack based on network flow characteristics."""
    # IP/Port Spoofing
    if is_sm_ips_ports == 1:
        return "IP/Port Spoofing"
    
    # DoS/DDoS attacks - High packet rate and count
    if proto == "TCP":
        if state in ("SYN", "SA"):
            return "DoS/SYN_Flood"
        if rate > 500 and (spkts > 1000 or dpkts > 1000):
            return "DoS/Flood"
    
    # DNS Amplification/Anomaly
    if service == "dns" and rate > 50:
        return "DNS_Anomaly"
    
    # HTTP/HTTPS-based attacks
    if service in ("http", "https"):
        if rate > 80:
            return "HTTP_Anomaly"
        if spkts > 500 or dpkts > 500:
            return "HTTP_Flood"
    
    # Port Scanning/Reconnaissance
    if (spkts > 100 or dpkts > 100) and rate > 200 and (sjit > 5000 or djit > 5000):
        return "Port_Scanning"
    
    # Backdoor/Command & Control - Periodic patterns
    if (20 < spkts < 100 and 20 < dpkts < 100) and (sjit < 100 and djit < 100):
        return "Backdoor/C2"
    
    # Exploits - Variable packet patterns
    if rate > 50 and (spkts != dpkts):
        return "Exploit"
    
    # Fuzzing - Many small packets with high jitter
    if spkts > 50 and (sjit > 1000 or djit > 1000):
        return "Fuzzing"
    
    # Shellcode/Payload execution - Specific packet patterns
    if spkts < 20 and dpkts < 20 and rate > 100:
        return "Shellcode_Execution"
    
    # Generic intrusion attempt
    return "Generic_Attack"

# Instantiate the machine learning model ONCE when the server starts.
# This ensures we use the same trained model for all connections.
import os
from django.conf import settings

# Initialize KNN detector with saved model
model_dir = os.path.join(settings.BASE_DIR, '..', '..')
model_path = os.path.join(model_dir, 'knn_model_cic2018.pkl')
scaler_path = os.path.join(model_dir, 'scaler_cic2018.pkl')

try:
    anomaly_detector = KNNAnomalyDetector(model_path, scaler_path=scaler_path)
except Exception as e:
    print("Error loading anomaly detector:", e)
    # (will be used for packet collection, not classification)
    anomaly_detector = None

# Per-flow state for CIC-IDS2018 Top 20 features
# key = (ipA, portA, ipB, portB, protocol) where (A,portA) < (B,portB) lexicographically
flow_stats = defaultdict(lambda: {
    "start_ts": None,
    "last_s_ts": None,
    
    "Total Fwd Packets": 0,
    "Fwd Packets Length Total": 0,
    "Fwd Packet Length Max": 0,
    "Fwd Seg Size Min": 999999,
    "Fwd Header Length": 0,
    "Init Fwd Win Bytes": -1,
    "Fwd IAT Total": 0.0,
    "Fwd IAT Min": 999999.0,
    
    "Subflow Bwd Packets": 0,
    "Bwd Packets Length Total": 0,
    "Bwd Header Length": 0,
    "Init Bwd Win Bytes": -1,
    
    "RST Flag Count": 0,
    "ECE Flag Count": 0,
    
    # UI mapping fields backward compatibility
    "sbytes": 0, "dbytes": 0,
    "spkts": 0, "dpkts": 0,
    "last_emit_ts": 0,
})

# Rolling window of recent "connections/events" (deprecated, kept small for dummy UI vars)
recent_events = deque(maxlen=10)
# Live buffer of enriched items for REST exposure
live_buffer = deque(maxlen=1000)

# Global tracker for detecting brute-force, DoS floods, or scanning across multiple fresh sockets.
# key: source_ip -> {count: int, start_ts: float, unique_ports: set, banned_until: float}
global_ip_connection_tracker = defaultdict(lambda: {"count": 0, "start_ts": 0.0, "unique_ports": set(), "udp_count": 0, "tcp_lengths": []})

class TrafficConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.keep_sniffing = True
        self.shared_blocked_ips = set()
        # Queue for throttled outbound messages (produced by sniffing thread)
        self.out_queue: asyncio.Queue = asyncio.Queue()
        # Decoupled Background Task: Silently sync the Database Blocklist to RAM every 2 seconds
        self.db_task = asyncio.create_task(self.db_sync_loop())
        # Background task to drain the queue and send at 1 msg/sec
        self.sender_task = asyncio.create_task(self.send_from_queue())
        # Store the main event loop to use for scheduling from the sniffing thread
        self.main_loop = asyncio.get_running_loop()
        # Start the sniffing process in a separate, non-blocking thread
        self.task = self.main_loop.run_in_executor(None, self.sniff_packets)
        print("WebSocket connection accepted. Starting live packet capture (Scapy)...")

    async def disconnect(self, close_code):
        self.keep_sniffing = False
        if getattr(self, "task", None):
            self.task.cancel()
        if getattr(self, "sender_task", None):
            self.sender_task.cancel()
        if getattr(self, "db_task", None):
            self.db_task.cancel()
        print(f"WebSocket disconnected with code: {close_code}. Scapy thread stopping...")

    async def db_sync_loop(self) -> None:
        """Silently run parallel to everything else, maintaining an accurate Live Blocklist in RAM"""
        try:
            while self.keep_sniffing:
                try:
                    from .models import ThreatIncident
                    blocked_qs = await sync_to_async(list)(ThreatIncident.objects.filter(status='Blocked').values_list('source_ip', flat=True))
                    self.shared_blocked_ips = set(blocked_qs)
                except Exception as e:
                    pass
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            return

    async def send_from_queue(self) -> None:
        """Continuously send one packet per second from the outbound queue.
        This runs on the main asyncio loop and does not block packet capture.
        """
        try:
            while True:
                data = await self.out_queue.get()
                
                # Late-Stage Purge: If overlapping packets were buffered into the queue BEFORE the firewall
                # physical block was completed, drop them instantly here. This prevents the UI from slowly
                # dripping 40 queued packets for 40 seconds straight, creating an illusion of an ongoing attack.
                if data.get("source_ip") in getattr(self, "shared_blocked_ips", set()):
                    continue
                    
                # Send traffic to client (flat dict with top-level timestamp)
                await self.send(text_data=json.dumps(data))
                # Persist to DB and emit incident live if created
                try:
                    incident = await save_traffic_and_incidents(data)
                    if incident:
                        # Send incident as a flat dict with a _type so the frontend can treat it
                        # the same way as traffic rows (it will have a top-level timestamp)
                        incident["_type"] = "incident"
                        await self.send(text_data=json.dumps(incident))
                except Exception as e:
                    print(f"Error saving traffic/incidents: {e}")
                # Throttle to 1 message per second to avoid crashing the browser frontend
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            # Task is being cancelled on disconnect; exit gracefully
            return

    def sniff_packets(self):
        # Create a new event loop for this background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print("Scapy packet sniffing thread started.")

        def handle_packet(pkt):
            try:
                if IP not in pkt:
                    return
                ip_layer = pkt[IP]
                
                # Math Drop: Silently discard packets from identically shared `self.shared_blocked_ips`
                if ip_layer.src in getattr(self, "shared_blocked_ips", set()):
                    return

                if TCP in pkt:
                    protocol_str = "TCP"
                elif UDP in pkt:
                    protocol_str = "UDP"
                else:
                    protocol_str = "IP"

                # Length fallback: prefer IP header length, else raw bytes length
                try:
                    length_val = int(ip_layer.len)
                except Exception:
                    length_val = int(len(bytes(pkt)))

                # Extract transport ports if present
                sport = None
                dport = None
                if protocol_str == "TCP":
                    sport = int(pkt[TCP].sport)
                    dport = int(pkt[TCP].dport)
                elif protocol_str == "UDP":
                    sport = int(pkt[UDP].sport)
                    dport = int(pkt[UDP].dport)

                features = {
                    "src_ip": ip_layer.src,
                    "dst_ip": ip_layer.dst,
                    "protocol": protocol_str,
                    "length": length_val,
                    "timestamp": datetime.datetime.now().timestamp(),
                }

                status = "Normal"
                severity = "Low"
                probs = []
                pred_idx = 0
                pred_prob = 0.0
                attack_type_detected = None

                # Build canonical key
                left = (ip_layer.src, sport or 0)
                right = (ip_layer.dst, dport or 0)
                if left <= right:
                    a_ip, a_port, b_ip, b_port = left[0], left[1], right[0], right[1]
                    fwd = True  # current packet goes A->B
                else:
                    a_ip, a_port, b_ip, b_port = right[0], right[1], left[0], left[1]
                    fwd = False  # current packet goes B->A
                key = (a_ip, a_port, b_ip, b_port, protocol_str)

                now_ts = features["timestamp"]
                st = flow_stats[key]
                if st["start_ts"] is None:
                    st["start_ts"] = now_ts

                # Tracker logic moved down correctly

                # TTL per direction (kept for backward UI comp)
                ttl_val = int(getattr(ip_layer, "ttl", 0))

                # Header lengths & Window
                try:
                    header_len = int(ip_layer.ihl) * 4
                except Exception:
                    header_len = 20
                
                win = -1
                if protocol_str == "TCP":
                    tcp = pkt[TCP]
                    flags = int(tcp.flags)
                    if flags & 0x04: st["RST Flag Count"] += 1
                    if flags & 0x40: st["ECE Flag Count"] += 1
                    header_len += int(tcp.dataofs) * 4
                    win = int(tcp.window)
                elif protocol_str == "UDP":
                    header_len += 8

                seg_size = header_len

                # Update counters by direction
                if fwd:
                    st["spkts"] += 1
                    st["sbytes"] += length_val
                    st["Total Fwd Packets"] += 1
                    st["Fwd Packets Length Total"] += length_val
                    if length_val > st["Fwd Packet Length Max"]:
                        st["Fwd Packet Length Max"] = length_val
                    if seg_size < st["Fwd Seg Size Min"]:
                        st["Fwd Seg Size Min"] = seg_size
                    st["Fwd Header Length"] += header_len
                    if st["Init Fwd Win Bytes"] == -1:
                        st["Init Fwd Win Bytes"] = win
                    
                    if st["last_s_ts"] is not None:
                        dt = now_ts - st["last_s_ts"]
                        st["Fwd IAT Total"] += dt
                        if dt < st["Fwd IAT Min"]:
                            st["Fwd IAT Min"] = dt
                    st["last_s_ts"] = now_ts
                else:
                    st["dpkts"] += 1
                    st["dbytes"] += length_val
                    st["Subflow Bwd Packets"] += 1
                    st["Bwd Packets Length Total"] += length_val
                    st["Bwd Header Length"] += header_len
                    if st["Init Bwd Win Bytes"] == -1:
                        st["Init Bwd Win Bytes"] = win

                # Derived metrics
                dur = max(0.0, now_ts - (st["start_ts"] or now_ts))
                total_pkts = st["spkts"] + st["dpkts"]
                rate = (total_pkts / dur) if dur > 0 else 0.0

                # Service and state
                service = _port_to_service(sport) or _port_to_service(dport)
                is_sm_ips_ports = int((ip_layer.src == ip_layer.dst) and ((sport or 0) == (dport or 0)))
                state = None
                if protocol_str == "TCP":
                    tcp = pkt[TCP]
                    flags = int(tcp.flags)
                    if flags & 0x04: state = "RST"
                    elif (flags & 0x01): state = "FIN"
                    elif (flags & 0x12) == 0x12: state = "SA"
                    elif (flags & 0x02): state = "SYN"
                    elif (flags & 0x10): state = "ACK"
                elif protocol_str == "UDP":
                    state = "CON"

                # Track global NEW connection rate per IP
                # Normal web traffic opens 1-4 connections and sends hundreds of ACKs.
                # DoS tools (like donisator) open dozens of isolated connections (SYNs).
                ip_tracker = global_ip_connection_tracker[ip_layer.src]
                # Stateful Attack Detection
                is_dos_flood = now_ts < ip_tracker.get("banned_until", 0.0)
                is_port_scan = (now_ts < ip_tracker.get("banned_until", 0.0)) and (len(ip_tracker["unique_ports"]) >= 8)

                if now_ts - ip_tracker["start_ts"] > 1.0:
                    ip_tracker["count"] = 0
                    ip_tracker["udp_count"] = 0
                    ip_tracker["tcp_lengths"] = []
                    ip_tracker["unique_ports"] = set()
                    ip_tracker["start_ts"] = now_ts
                
                # Port Scanning Tracker (Vertical Scan)
                if dport:
                    ip_tracker["unique_ports"].add(dport)
                
                if len(ip_tracker["unique_ports"]) >= 8: 
                    # If an IP hits >= 8 unique ports in a window, flag it as a scan
                    if not is_port_scan:
                        print(f"[SECURITY] Port Scan Detected from {ip_layer.src} ({len(ip_tracker['unique_ports'])} unique ports)")
                    ip_tracker["banned_until"] = now_ts + 30.0 # Long ban for reconnaissance
                    is_port_scan = True
                
                # TCP SYN Flood tracking (low threshold because SYNs should be rare)
                if state == "SYN":
                    ip_tracker["count"] += 1
                    if ip_tracker["count"] > 10:
                        ip_tracker["banned_until"] = now_ts + 5.0
                        is_dos_flood = True
                        
                # Robotic Payload Flood Tracking (Catches donisator.py generic TCP payloads)
                # Normal network browsing utilizes highly varied packet lengths (e.g. 54b ACKs + 1500b Data).
                # DoS spam scripts emit identical payload lengths repetitively.
                if protocol_str == "TCP":
                    lengths = ip_tracker.get("tcp_lengths", [])
                    lengths.append(length_val)
                    ip_tracker["tcp_lengths"] = lengths
                    # If we receive 5 identical generic TCP payload packets between 70b and 500b in 1 sec
                    # We bound it <500b so we don't accidentally ban legitimate bulk MTU downloads (like 1410b or 1460b video chunks)
                    if len(lengths) >= 5 and len(set(lengths)) == 1 and 70 < lengths[0] < 500:
                        ip_tracker["banned_until"] = now_ts + 5.0
                        is_dos_flood = True
                        
                # UDP Flood tracking (QUIC video streaming often hits 1000+ packets/sec)
                if protocol_str == "UDP":
                    ip_tracker["udp_count"] = ip_tracker.get("udp_count", 0) + 1
                    if ip_tracker["udp_count"] > 500:
                        ip_tracker["banned_until"] = now_ts + 5.0
                        is_dos_flood = True


                # Rate limiting logic
                last_emit = st.get("last_emit_ts", 0)
                if total_pkts > 1 and (now_ts - last_emit < 1.0) and (total_pkts % 100 != 0):
                    return

                st["last_emit_ts"] = now_ts
                
                # CIC-IDS2018 Features computation
                fwd_pkts = st["Total Fwd Packets"]
                bwd_pkts = st["Subflow Bwd Packets"]
                fwd_bytes = st["Fwd Packets Length Total"]
                bwd_bytes = st["Bwd Packets Length Total"]
                fwd_seg_size_min = 0 if st["Fwd Seg Size Min"] == 999999 else st["Fwd Seg Size Min"]
                
                bwd_pkts_s = bwd_pkts / dur if dur > 0 else 0
                avg_fwd_segment_size = fwd_bytes / fwd_pkts if fwd_pkts > 0 else 0
                fwd_iat_mean = st["Fwd IAT Total"] / (fwd_pkts - 1) if fwd_pkts > 1 else 0
                fwd_iat_min = 0 if st["Fwd IAT Min"] == 999999.0 else st["Fwd IAT Min"]
                
                flow_features = {
                    'Fwd Seg Size Min': fwd_seg_size_min,
                    'Fwd Header Length': st["Fwd Header Length"],
                    'Subflow Fwd Bytes': fwd_bytes,
                    'Bwd Header Length': st["Bwd Header Length"],
                    'Init Fwd Win Bytes': max(-1, st["Init Fwd Win Bytes"]),
                    'Total Fwd Packets': fwd_pkts,
                    'Fwd Packets Length Total': fwd_bytes,
                    'RST Flag Count': st["RST Flag Count"],
                    'ECE Flag Count': st["ECE Flag Count"],
                    'Fwd Packet Length Max': st["Fwd Packet Length Max"],
                    'Subflow Bwd Packets': bwd_pkts,
                    'Avg Fwd Segment Size': avg_fwd_segment_size,
                    'Bwd Packets Length Total': bwd_bytes,
                    'Bwd Packets/s': bwd_pkts_s,
                    'Init Bwd Win Bytes': max(-1, st["Init Bwd Win Bytes"]),
                    'Fwd IAT Total': st["Fwd IAT Total"],
                    'Subflow Bwd Bytes': bwd_bytes,
                    'Fwd IAT Mean': fwd_iat_mean,
                    'Fwd Packet Length Mean': avg_fwd_segment_size,
                    'Fwd IAT Min': fwd_iat_min,
                }

                if anomaly_detector is not None:
                    try:
                        # Hybrid Rule: Prevent ML False Positives on "Immature Flows"
                        # The CIC-IDS2018 model expects mature network flows. Single isolated packets 
                        # (like background keep-alives or ACKs) mathematically skew to False Positives.
                        is_trusted_bg = False
                        
                        # DISABLED for DoS Demo: Prevent ML False Positives on "Immature Flows"
                        # if total_pkts < 4 and dur < 0.5:
                        #     is_trusted_bg = True
                            
                        # DISABLED for DoS Demo: Whitelist standard web/app ports without massive traffic spikes to prevent feedback loops
                        # Ports: 53 (DNS), 68 (DHCP), 80 (HTTP), 443 (HTTPS), 8000 (Django WS), 5173 (Vite HMR)
                        # if state in ["ACK", "FIN", "RST"] and rate < 500:
                        #     if (dport in [53, 68, 80, 443, 8000, 5173] or sport in [53, 68, 80, 443, 8000, 5173]):
                        #         is_trusted_bg = True
                                
                        # Whitelist MDNS / Local Broadcasts (prevents MDNS being tagged as DoS)
                        if ip_layer.dst == "224.0.0.251" or ip_layer.dst == "255.255.255.255":
                            is_trusted_bg = True

                        # Intra-LAN Noise Filter: Trust low-rate local traffic
                        # Windows SMB/NetBios background chatter (150-byte pings) often gets tagged as DoS by ML
                        # DISABLED: User is running a slow DoS attack (e.g., 26 pkts/sec) that gets caught by this filter.
                        # if ip_layer.src.startswith(("192.168.", "10.", "172.")) and ip_layer.dst.startswith(("192.168.", "10.", "172.")):
                        #     if rate < 50 and total_pkts < 100:
                        #         is_trusted_bg = True

                        if is_trusted_bg:
                            result = {
                                'label': 'Normal', 'prediction': 0, 'confidence': 0.99,
                                'probabilities': {'normal': 0.99, 'anomalous': 0.01}
                            }
                        else:
                            # Get prediction from KNN model
                            result = anomaly_detector.predict(flow_features)

                        pred_label = result.get('label', 'Normal')
                        pred_prob = result.get('confidence', 0.0)
                        
                        # Override ML for high-rate connection floods
                        # Flow-based models (like CIC-IDS2018) often predict 'Benign' for 1-packet DoS flows.
                        # Reduced threshold to 10 to match the very slow rate (~16 pkts/sec) generated by donisator.py
                        if is_dos_flood or is_port_scan:
                            pred_label = "Port_Scanning" if is_port_scan else "DoS"
                            result['label'] = pred_label
                            pred_prob = 1.0
                            result['prediction'] = 1
                        
                        # Refined False Positive Suppression:
                        if pred_label not in ("Normal", "Benign"):
                            # Relaxed Infiltration rule: 50KB was way too high for reconnaissance phases.
                            # Lowered to 2KB or High Confidence to catch real exploits.
                            if pred_label == "Infiltration" and (pred_prob < 0.90 and (fwd_bytes + bwd_bytes) < 2000):
                                pred_label = "Benign"
                                result['label'] = "Benign"
                                pred_prob = 1.0 - pred_prob
                                result['prediction'] = 0
                            # Relaxed DoS confidence threshold
                            elif pred_label == "DoS" and pred_prob < 0.75:
                                pred_label = "Benign"
                                result['label'] = "Benign"
                                pred_prob = 1.0 - pred_prob
                                result['prediction'] = 0
                            # Allow specific attack labels to pass through easier
                            elif pred_label not in ("DoS", "Infiltration", "Benign") and pred_prob < 0.70:
                                pred_label = "Benign"
                                result['label'] = "Benign"
                                pred_prob = 1.0 - pred_prob # Flip confidence back
                                result['prediction'] = 0
                            
                        # Standardize visual outputs
                        if pred_label == 'Benign':
                            status = 'Benign'
                        else:
                            status = pred_label
                            
                        severity = "Critical" if status not in ("Normal", "Benign") else "Low"
                        pred_idx = result.get('prediction', 0)
                        probs = [
                            result.get('probabilities', {}).get('normal', 0.0),
                            result.get('probabilities', {}).get('anomalous', 0.0)
                        ]
                        
                        # Classify attack type if anomalous
                        if status not in ("Normal", "Benign") and status == "Anomalous":
                            attack_type_detected = _classify_attack_type(
                                rate, is_sm_ips_ports, protocol_str, str(state), str(service), 
                                st["spkts"], st["dpkts"], st.get("sjit", 0), st.get("djit", 0)
                            )
                        elif status not in ("Normal", "Benign"):
                            attack_type_detected = status # Direct model class, e.g. "DoS"
                    except Exception as e:
                        print("KNN Prediction Error:", e)
                        status, severity, probs, pred_idx, pred_prob = "Normal", "Low", [], 0, 0.0

                # Derive numeric label from model prediction for UI/API: 0=normal, 1=anomalous/blocked
                try:
                    label_val = 0 if int(pred_idx) == 0 else 1
                except Exception:
                    label_val = 0

                data = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "source_ip": ip_layer.src,
                    "destination_ip": ip_layer.dst,
                    "protocol": protocol_str,
                    "proto": protocol_str.lower(),
                    "bytes": length_val,
                    "status": status,
                    "severity": severity,
                    "probs": probs,
                    "pred_idx": pred_idx,
                    "pred_prob": pred_prob,
                    "label": label_val,
                    "attack_type": attack_type_detected,
                    # Extended metrics (best-effort live approximation)
                    # Inject our CIC-IDS2018 Top 20 features dynamically
                    "dur": dur,
                    "spkts": st["spkts"],
                    "dpkts": st["dpkts"],
                    "rate": rate,
                    "service": service,
                    "state": state,
                    "is_sm_ips_ports": is_sm_ips_ports,
                    "fwd_seg_size_min": flow_features.get("Fwd Seg Size Min"),
                    "fwd_header_len": flow_features.get("Fwd Header Length"),
                    "subflow_fwd_bytes": flow_features.get("Subflow Fwd Bytes"),
                    "bwd_header_len": flow_features.get("Bwd Header Length"),
                    "init_fwd_win": flow_features.get("Init Fwd Win Bytes"),
                    "total_fwd_packets": flow_features.get("Total Fwd Packets"),
                    "fwd_packets_len_total": flow_features.get("Fwd Packets Length Total"),
                    "rst_flag_cnt": flow_features.get("RST Flag Count"),
                    "ece_flag_cnt": flow_features.get("ECE Flag Count"),
                    "fwd_packet_len_max": flow_features.get("Fwd Packet Length Max"),
                    "subflow_bwd_packets": flow_features.get("Subflow Bwd Packets"),
                    "avg_fwd_seg_size": flow_features.get("Avg Fwd Segment Size"),
                    "bwd_packets_len_total": flow_features.get("Bwd Packets Length Total"),
                    "bwd_packets_s": flow_features.get("Bwd Packets/s"),
                    "init_bwd_win": flow_features.get("Init Bwd Win Bytes"),
                    "fwd_iat_total": flow_features.get("Fwd IAT Total"),
                    "subflow_bwd_bytes": flow_features.get("Subflow Bwd Bytes"),
                    "fwd_iat_mean": flow_features.get("Fwd IAT Mean"),
                    "fwd_packet_len_mean": flow_features.get("Fwd Packet Length Mean"),
                    "fwd_iat_min": flow_features.get("Fwd IAT Min"),
                }

                # Add to live buffer for REST exposure
                try:
                    live_buffer.append(dict(data))
                except Exception:
                    pass

                # Enqueue for async, throttled sending on the main loop
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.out_queue.put(data), self.main_loop
                    )
                except RuntimeError:
                    # Event loop is shutting down or closed (e.g., during reload/stop).
                    # Skip scheduling the coroutine to avoid 'cannot schedule new futures'
                    return
                except Exception as e:
                    # Log and continue; we don't want a background packet to crash the sniff thread
                    print(f"Failed to schedule outbound send: {e}")
            except Exception as e:
                pass # Suppress mid-shutdown parsing errors
                
        def should_stop(pkt):
            return not getattr(self, "keep_sniffing", False)

        # Start Scapy sniffing (requires admin privileges and Npcap on Windows)
        try:
            sniff(filter="ip", prn=handle_packet, stop_filter=should_stop, store=False)
        except Exception as e:
            print(f"Scapy sniffing terminated: {e}")
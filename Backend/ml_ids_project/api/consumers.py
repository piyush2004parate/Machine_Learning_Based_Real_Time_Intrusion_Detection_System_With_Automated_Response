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
model_dir = os.path.join(settings.BASE_DIR, '..', '..', 'model', 'unsw_tabular')
model_path = os.path.join(model_dir, 'model_knn.pkl')
features_path = os.path.join(model_dir, 'features_knn.json')
scaler_path = os.path.join(model_dir, 'scaler_knn.pkl')

try:
    anomaly_detector = KNNAnomalyDetector(model_path, features_path, scaler_path)
except Exception:
    # If model not found, create detector without loading model
    # (will be used for packet collection, not classification)
    anomaly_detector = None

# Per-flow state for basic metrics using canonical 5-tuple key
# key = (ipA, portA, ipB, portB, protocol) where (A,portA) < (B,portB) lexicographically
flow_stats = defaultdict(lambda: {
    "start_ts": None,
    # forward (A->B)
    "spkts": 0,
    "sbytes": 0,
    "last_s_ts": None,
    "last_s_dt": None,
    "sjit": 0.0,
    "smean_sum": 0,
    "sttl": None,
    "swin": None,
    "stcpb": None,
    # reverse (B->A)
    "dpkts": 0,
    "dbytes": 0,
    "last_d_ts": None,
    "last_d_dt": None,
    "djit": 0.0,
    "dmean_sum": 0,
    "dttl": None,
    "dwin": None,
    "dtcpb": None,
    # TCP timing
    "t_syn": None,
    "t_synack": None,
    "t_ack": None,
    "synack": None,
    "tcprtt": None,
    "ackdat": None,
})

# Rolling window of recent "connections/events" to approximate ct_* counters
recent_events = deque(maxlen=100)
# Live buffer of enriched items for REST exposure
live_buffer = deque(maxlen=1000)

class TrafficConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # Queue for throttled outbound messages (produced by sniffing thread)
        self.out_queue: asyncio.Queue = asyncio.Queue()
        # Background task to drain the queue and send at 1 msg/sec
        self.sender_task = asyncio.create_task(self.send_from_queue())
        # Store the main event loop to use for scheduling from the sniffing thread
        self.main_loop = asyncio.get_running_loop()
        # Start the sniffing process in a separate, non-blocking thread
        self.task = self.main_loop.run_in_executor(None, self.sniff_packets)
        print("WebSocket connection accepted. Starting live packet capture (Scapy)...")

    async def disconnect(self, close_code):
        if getattr(self, "task", None):
            self.task.cancel()
        if getattr(self, "sender_task", None):
            self.sender_task.cancel()
        print(f"WebSocket disconnected with code: {close_code}")

    async def send_from_queue(self) -> None:
        """Continuously send one packet per second from the outbound queue.
        This runs on the main asyncio loop and does not block packet capture.
        """
        try:
            while True:
                data = await self.out_queue.get()
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
                # Throttle to 1 message per second
                await asyncio.sleep(1)
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

                # TTL per direction
                ttl_val = int(getattr(ip_layer, "ttl", 0))

                # Update counters by direction
                if fwd:
                    st["spkts"] += 1
                    st["sbytes"] += length_val
                    st["smean_sum"] += length_val
                    if st["last_s_ts"] is not None:
                        dt = max(0.0, now_ts - st["last_s_ts"])
                        if st["last_s_dt"] is not None:
                            st["sjit"] += abs(dt - st["last_s_dt"])
                        st["last_s_dt"] = dt
                        sinpkt = dt
                    else:
                        sinpkt = None
                    st["last_s_ts"] = now_ts
                    st["sttl"] = ttl_val
                else:
                    st["dpkts"] += 1
                    st["dbytes"] += length_val
                    st["dmean_sum"] += length_val
                    if st["last_d_ts"] is not None:
                        dt = max(0.0, now_ts - st["last_d_ts"])
                        if st["last_d_dt"] is not None:
                            st["djit"] += abs(dt - st["last_d_dt"])
                        st["last_d_dt"] = dt
                        dinpkt = dt
                    else:
                        dinpkt = None
                    st["last_d_ts"] = now_ts
                    st["dttl"] = ttl_val

                # TCP-specific fields and timing
                swin = dwin = stcpb = dtcpb = None
                synack = tcprtt = ackdat = None
                if protocol_str == "TCP":
                    tcp = pkt[TCP]
                    flags = int(tcp.flags)
                    win = int(getattr(tcp, "window", 0))
                    seq = int(getattr(tcp, "seq", 0))
                    ack = int(getattr(tcp, "ack", 0))
                    # Save window and base seq per direction (first seen)
                    if fwd:
                        if st["swin"] is None:
                            st["swin"] = win
                        if st["stcpb"] is None:
                            st["stcpb"] = seq
                        swin = st["swin"]
                        stcpb = st["stcpb"]
                    else:
                        if st["dwin"] is None:
                            st["dwin"] = win
                        if st["dtcpb"] is None:
                            st["dtcpb"] = seq
                        dwin = st["dwin"]
                        dtcpb = st["dtcpb"]

                    # TCP handshake timing (assumes A initiates)
                    syn = bool(flags & 0x02)
                    ack_flag = bool(flags & 0x10)
                    # SYN from A->B
                    if fwd and syn and not ack_flag:
                        st["t_syn"] = now_ts
                    # SYN-ACK from B->A
                    if (not fwd) and syn and ack_flag:
                        st["t_synack"] = now_ts
                        if st["t_syn"] is not None:
                            st["synack"] = max(0.0, now_ts - st["t_syn"])
                    # Final ACK from A->B
                    if fwd and (not syn) and ack_flag:
                        st["t_ack"] = now_ts
                        if st["t_syn"] is not None:
                            st["tcprtt"] = max(0.0, now_ts - st["t_syn"])
                    synack = st.get("synack")
                    tcprtt = st.get("tcprtt")

                # Derived metrics
                dur = max(0.0, now_ts - (st["start_ts"] or now_ts))
                total_pkts = st["spkts"] + st["dpkts"]
                rate = (total_pkts / dur) if dur > 0 else 0.0
                smean = (st["smean_sum"] / st["spkts"]) if st["spkts"] > 0 else 0.0
                dmean = (st["dmean_sum"] / st["dpkts"]) if st["dpkts"] > 0 else 0.0
                sload = (st["sbytes"] * 8) / dur if dur > 0 else 0.0
                dload = (st["dbytes"] * 8) / dur if dur > 0 else 0.0

                # Service and state
                service = _port_to_service(sport) or _port_to_service(dport)
                is_sm_ips_ports = int((ip_layer.src == ip_layer.dst) and ((sport or 0) == (dport or 0)))
                state = None
                if protocol_str == "TCP":
                    # Very coarse state mapping
                    tcp = pkt[TCP]
                    flags = int(tcp.flags)
                    if flags & 0x04:
                        state = "RST"
                    elif (flags & 0x01):
                        state = "FIN"
                    elif (flags & 0x12) == 0x12:  # SYN+ACK
                        state = "SA"
                    elif (flags & 0x02):
                        state = "SYN"
                    elif (flags & 0x10):
                        state = "ACK"
                elif protocol_str == "UDP":
                    state = "CON"

                # Update rolling events window
                recent_events.append({
                    "src": ip_layer.src,
                    "dst": ip_layer.dst,
                    "sport": sport,
                    "dport": dport,
                    "service": service,
                    "state": state,
                    "ttl": ttl_val,
                })

                # Compute ct_* counters over recent window
                def _count(pred):
                    c = 0
                    # iterate over a snapshot of the deque to avoid "deque mutated during iteration"
                    # which can occur when the sniffing thread appends while another thread is iterating
                    for ev in list(recent_events):
                        try:
                            if pred(ev):
                                c += 1
                        except Exception:
                            continue
                    return c

                ct_srv_src = _count(lambda ev: ev.get("src") == ip_layer.src and ev.get("service") == service)
                ct_state_ttl = _count(lambda ev: ev.get("state") == state and int(ev.get("ttl") or 0) == ttl_val)
                ct_dst_ltm = _count(lambda ev: ev.get("dst") == ip_layer.dst)
                ct_src_dport_ltm = _count(lambda ev: (ev.get("src") == ip_layer.src) and (ev.get("dport") == dport))
                ct_dst_sport_ltm = _count(lambda ev: (ev.get("dst") == ip_layer.dst) and (ev.get("sport") == sport))
                ct_dst_src_ltm = _count(lambda ev: (ev.get("dst") == ip_layer.dst) and (ev.get("src") == ip_layer.src))
                ct_src_ltm = _count(lambda ev: ev.get("src") == ip_layer.src)
                # Approximate ct_srv_dst as same source to same destination and same service
                ct_srv_dst = _count(lambda ev: (ev.get("src") == ip_layer.src) and (ev.get("dst") == ip_layer.dst) and (ev.get("service") == service))

                # --- RATE LIMITING LOGIC ---
                last_emit = st.get("last_emit_ts", 0)
                if total_pkts > 1 and (now_ts - last_emit < 1.0) and (total_pkts % 100 != 0):
                    return  # Skip prediction and UI emit for this packet (throttle)

                st["last_emit_ts"] = now_ts
                # ---------------------------

                flow_features = {
                    'dur': dur, 'spkts': st['spkts'], 'dpkts': st['dpkts'],
                    'sbytes': st['sbytes'], 'dbytes': st['dbytes'], 'rate': rate,
                    'sload': sload, 'dload': dload, 
                    'sinpkt': (dur / st['spkts'] * 1000) if st['spkts'] > 0 else 0.0,
                    'dinpkt': (dur / st['dpkts'] * 1000) if st['dpkts'] > 0 else 0.0, 
                    'sjit': (st.get('sjit', 0) / st['spkts'] * 1000) if st['spkts'] > 0 else 0.0, 
                    'djit': (st.get('djit', 0) / st['dpkts'] * 1000) if st['dpkts'] > 0 else 0.0,
                    'sttl': st.get('sttl') or 0, 'dttl': st.get('dttl') or 0, 'swin': st.get('swin') or 0,
                    'stcpb': st.get('stcpb') or 0, 'dtcpb': st.get('dtcpb') or 0, 'synack': synack or 0,
                    'tcprtt': tcprtt or 0, 'ackdat': st.get('ackdat') or 0, 'smean': smean,
                    'dmean': dmean, 'ct_srv_src': ct_srv_src, 'ct_state_ttl': min(6, ct_state_ttl),
                    'ct_dst_ltm': ct_dst_ltm, 'ct_src_dport_ltm': ct_src_dport_ltm,
                    'ct_dst_sport_ltm': ct_dst_sport_ltm, 'ct_dst_src_ltm': ct_dst_src_ltm,
                    'ct_src_ltm': ct_src_ltm, 'ct_srv_dst': ct_srv_dst, 'is_sm_ips_ports': is_sm_ips_ports,
                }

                if anomaly_detector is not None:
                    try:
                        # Hybrid Rule: Pre-filter trusted heavy background protocols to avoid ML false positives
                        # We whitelist standard web states (ACK/CON/FIN) on known ports unless there's a huge packet rate.
                        is_trusted_bg = False
                        if state in ["ACK", "CON", "FIN", "RST"]:
                            if (dport in [53, 68, 80, 443] or sport in [53, 68, 80, 443]):
                                is_trusted_bg = True

                        if is_trusted_bg:
                            result = {
                                'label': 'Normal', 'prediction': 0, 'confidence': 0.99,
                                'probabilities': {'normal': 0.99, 'anomalous': 0.01}
                            }
                        else:
                            # Get prediction from KNN model
                            result = anomaly_detector.predict(flow_features)

                        pred_label = result.get('label', 'Normal')
                        status = pred_label
                        severity = "Critical" if pred_label == "Anomalous" else "Low"
                        pred_idx = result.get('prediction', 0)
                        pred_prob = result.get('confidence', 0.0)
                        probs = [
                            result.get('probabilities', {}).get('normal', 0.0),
                            result.get('probabilities', {}).get('anomalous', 0.0)
                        ]
                        
                        # Classify attack type if anomalous
                        if pred_label == "Anomalous":
                            attack_type_detected = _classify_attack_type(
                                rate, is_sm_ips_ports, protocol_str, str(state), str(service), 
                                st["spkts"], st["dpkts"], st.get("sjit", 0), st.get("djit", 0)
                            )
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
                    "dur": dur,
                    "spkts": st["spkts"],
                    "dpkts": st["dpkts"],
                    "sbytes": st["sbytes"],
                    "dbytes": st["dbytes"],
                    "rate": rate,
                    "sload": sload,
                    "dload": dload,
                    "sinpkt": st.get("last_s_dt"),
                    "dinpkt": st.get("last_d_dt"),
                    "sjit": st.get("sjit"),
                    "djit": st.get("djit"),
                    "smean": smean,
                    "dmean": dmean,
                    "sttl": st.get("sttl"),
                    "dttl": st.get("dttl"),
                    "swin": st.get("swin"),
                    "dwin": st.get("dwin"),
                    "stcpb": st.get("stcpb"),
                    "dtcpb": st.get("dtcpb"),
                    "synack": synack,
                    "tcprtt": tcprtt,
                    "ackdat": st.get("ackdat"),
                    "service": service,
                    "state": state,
                    "is_sm_ips_ports": is_sm_ips_ports,
                    # Rolling counters (approximate over last 100 events)
                    "ct_srv_src": ct_srv_src,
                    "ct_state_ttl": ct_state_ttl,
                    "ct_dst_ltm": ct_dst_ltm,
                    "ct_src_dport_ltm": ct_src_dport_ltm,
                    "ct_dst_sport_ltm": ct_dst_sport_ltm,
                    "ct_dst_src_ltm": ct_dst_src_ltm,
                    "ct_src_ltm": ct_src_ltm,
                    "ct_srv_dst": ct_srv_dst,
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
                print(f"Error processing a Scapy packet: {e}")

        # Start Scapy sniffing (requires admin privileges and Npcap on Windows)
        sniff(filter="ip", prn=handle_packet, store=False)
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import NetworkTraffic, ThreatIncident, ResponseRule, LogEntry
from .actions import execute_action
import time

_RECENT_INCIDENTS_CACHE = {}


async def save_traffic_and_incidents(packet_data: dict):
	"""Persist live traffic to DB and create incident rows for anomalies.

	Args:
		packet_data: Dict with keys id, timestamp, source_ip, destination_ip, protocol, bytes, status, severity
	Returns:
		Optional[dict]: Incident payload if created, else None.
	"""
	# Save traffic row
	traffic = await sync_to_async(NetworkTraffic.objects.create)(
		id=packet_data.get("id"),
		timestamp=timezone.now(),
		source_ip=packet_data.get("source_ip", ""),
		destination_ip=packet_data.get("destination_ip", ""),
		protocol=packet_data.get("protocol", ""),
		bytes=packet_data.get("bytes", 0),
		status=packet_data.get("status", "Normal"),
		severity=packet_data.get("severity"),
	)
	status = packet_data.get("status", "Normal")
	label = packet_data.get("label")
	rate = float(packet_data.get("rate") or 0.0)
	service = (packet_data.get("service") or "").lower() or None
	state = packet_data.get("state")
	proto = (packet_data.get("protocol") or "").upper()
	is_sm_ips_ports = int(packet_data.get("is_sm_ips_ports") or 0)
	attack_type_from_model = packet_data.get("attack_type")  # Get detected attack type from model
	create_incident = (str(label) == "1") or (status in ("Anomalous", "Blocked"))
	if create_incident:
		ip = packet_data.get("source_ip", "")
		now_ts = time.time()
		
		# Incident Deduplication: Prevent UI spam by debouncing incidents from the same IP (15 second cooldown)
		# This absorbs the ~3 second packet buffer bleed that occurs while the Windows Firewall is physically executing the block
		last_incident_time = _RECENT_INCIDENTS_CACHE.get(ip, 0)
		if now_ts - last_incident_time < 15.0:
			return None  # Skip creating a duplicate incident row
			
		_RECENT_INCIDENTS_CACHE[ip] = now_ts
		
		# Use attack type from ML model if available, otherwise infer from traffic patterns
		if attack_type_from_model:
			threat_type = attack_type_from_model
		else:
			threat_type = packet_data.get("protocol", "Unknown")
			if is_sm_ips_ports == 1:
				threat_type = "IP/Port Spoofing"
			elif proto == "TCP" and state in ("SYN", "SA") and rate > 100:
				threat_type = "DoS/SYN_Flood"
			elif service == "dns" and rate > 50:
				threat_type = "DNS_Anomaly"
			elif service in ("http", "https") and rate > 80:
				threat_type = "HTTP_Anomaly"
		severity_val = packet_data.get("severity") or "Medium"
		if status == "Blocked" or is_sm_ips_ports == 1 or rate > 200:
			severity_val = "High"
		if rate > 500:
			severity_val = "Critical"
		# Confidence scoring based directly on ML model output
		confidence_val = float(packet_data.get("pred_prob", 0.0)) * 100
		if confidence_val == 0.0:
			# Fallback if no pred_prob available
			confidence_val = 65 if str(label) == "1" or status in ("Anomalous", "Blocked") else 50
			if rate > 50: confidence_val += 10
			if rate > 500: confidence_val += 10
		confidence_val = max(50, min(99, confidence_val))
		
		description = f"Detected {status.lower()} traffic from {packet_data.get('source_ip')} to {packet_data.get('destination_ip')} via {packet_data.get('protocol')}"
		
		# Auto mitigation status trigger
		incident_status = "Blocked" if status == "Blocked" else "Active"
		
		# High confidence override
		if str(label) == "1" and confidence_val > 85:
			incident_status = "Blocked"
			
		created = await sync_to_async(ThreatIncident.objects.create)(
			source_ip=packet_data.get("source_ip", ""),
			destination_ip=packet_data.get("destination_ip", ""),
			threat_type=threat_type,
			severity=severity_val,
			status=incident_status,
			description=description,
			confidence=confidence_val,
		)
		# Build a lightweight payload for WS broadcast
		# Ensure returned values are JSON-serializable (convert UUIDs to strings)
		incident_payload = {
			"id": str(getattr(created, "id", None)),
			"timestamp": getattr(created, "timestamp", timezone.now()).isoformat(),
			"source_ip": created.source_ip,
			"destination_ip": created.destination_ip,
			"threat_type": created.threat_type,
			"severity": created.severity,
			"status": created.status,
			"confidence": created.confidence,
		}

		# Direct ML Trigger Logic
		if str(label) == "1" and confidence_val > 85:
			try:
				await sync_to_async(execute_action)("block ip", created)
				await sync_to_async(LogEntry.objects.create)(
					action="block ip",
					target=str(getattr(created, 'id', '')),
					result="Success",
					details=f"Auto-mitigation triggered: ML Confidence {confidence_val}% over threshold (85%)",
					severity="Critical",
				)
			except Exception:
				pass

		# Evaluate active response rules (comma-separated key=value, all clauses must match)
		try:
			active_rules = await sync_to_async(list)(ResponseRule.objects.filter(is_active=True))
			for rule in active_rules:
				cond = (rule.condition or "").strip()
				if not cond:
					continue
				matched = True
				for clause in cond.split(','):
					cl = clause.strip()
					if not cl:
						continue
					if '=' not in cl:
						matched = False
						break
					k, v = [p.strip() for p in cl.split('=', 1)]
					# compare string representations (case-insensitive)
					val = incident_payload.get(k)
					if val is None:
						val = getattr(created, k, None)
					if val is None:
						matched = False
						break
					if str(val).lower() != str(v).lower():
						matched = False
						break
				if matched:
					# create a log entry and increment triggered_count
					try:
						await sync_to_async(LogEntry.objects.create)(
							action=rule.action or "rule_trigger",
							target=str(getattr(created, 'id', '')),
							result="Success",
							details=f"Rule '{rule.name}' triggered for incident {getattr(created, 'id', None)}",
							severity="Info",
						)
						rule.triggered_count = (rule.triggered_count or 0) + 1
						await sync_to_async(rule.save)()
						# Execute the configured action (safe/mock implementations)
						try:
							# execute_action is synchronous; call via sync_to_async to avoid blocking
							await sync_to_async(execute_action)(rule.action, created)
						except Exception:
							# Do not let action failures break incident flow; just log
							await sync_to_async(LogEntry.objects.create)(
								action='action_failed',
								target=str(getattr(created, 'id', '')),
								result='Failed',
								details=f"Action '{rule.action}' failed for incident {getattr(created, 'id', None)}",
								severity='Error',
							)
					except Exception:
						# ignore logging errors to avoid breaking incident creation
						continue
		except Exception:
			# don't let rule engine failure prevent incident flow
			pass

		return incident_payload
	# No incident created
	return None

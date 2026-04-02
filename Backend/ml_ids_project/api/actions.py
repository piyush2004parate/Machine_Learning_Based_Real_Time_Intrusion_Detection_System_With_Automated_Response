"""
Mock action implementations for automated response rules.

These are safe, local-side effects used for demo/testing:
- Block IP: writes blocked IP to `logs/blocked_ips.txt`
- Alert Admin: writes a message to `logs/actions.log` (placeholders for webhooks/email)
- Isolate Device: writes to `logs/isolated_devices.txt`
- Quarantine: writes to `logs/quarantined.txt`

Replace or extend these implementations with real integrations (firewall APIs,
notification services) when deploying in production.
"""
from pathlib import Path
from datetime import datetime
import json

HERE = Path(__file__).resolve().parent
LOGS_DIR = HERE.parent.parent / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _append_log(filename: str, payload: str) -> None:
    path = LOGS_DIR / filename
    ts = datetime.utcnow().isoformat()
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {payload}\n")


def block_ip(incident) -> dict:
    ip = getattr(incident, 'source_ip', None) or incident.get('source_ip') if isinstance(incident, dict) else None
    if not ip:
        return {'result': 'failed', 'reason': 'no source_ip'}
    _append_log('blocked_ips.txt', f'Blocked IP: {ip}')
    _append_log('actions.log', f"Block IP executed for {ip}")
    return {'result': 'ok', 'ip': ip}


def alert_admin(incident) -> dict:
    # Placeholder for sending email/Slack/webhook. For now, log to actions.log
    details = json.dumps({
        'source_ip': getattr(incident, 'source_ip', None) or (incident.get('source_ip') if isinstance(incident, dict) else None),
        'threat_type': getattr(incident, 'threat_type', None) or (incident.get('threat_type') if isinstance(incident, dict) else None),
    })
    _append_log('actions.log', f'Alert Admin: {details}')
    return {'result': 'ok'}


def isolate_device(incident) -> dict:
    ip = getattr(incident, 'source_ip', None) or (incident.get('source_ip') if isinstance(incident, dict) else None)
    _append_log('isolated_devices.txt', f'Isolated device: {ip}')
    _append_log('actions.log', f'Isolate Device executed for {ip}')
    return {'result': 'ok', 'ip': ip}


def quarantine_traffic(incident) -> dict:
    ip = getattr(incident, 'source_ip', None) or (incident.get('source_ip') if isinstance(incident, dict) else None)
    _append_log('quarantined.txt', f'Quarantined traffic for: {ip}')
    _append_log('actions.log', f'Quarantine executed for {ip}')
    return {'result': 'ok', 'ip': ip}


def execute_action(action_type: str, incident) -> dict:
    """Dispatch to the appropriate action implementation.

    action_type is expected to be one of the user-visible strings stored in
    `ResponseRule.action` (e.g. 'Block IP', 'Alert Admin'). Matching is case-insensitive.
    """
    if not action_type:
        return {'result': 'failed', 'reason': 'no action specified'}
    key = action_type.strip().lower()
    if key == 'block ip':
        return block_ip(incident)
    if key == 'alert admin':
        return alert_admin(incident)
    if key == 'isolate device':
        return isolate_device(incident)
    if key == 'quarantine':
        return quarantine_traffic(incident)
    # Fallback: log unknown action
    _append_log('actions.log', f'Unknown action requested: {action_type} for incident {getattr(incident, "id", None)}')
    return {'result': 'failed', 'reason': 'unknown_action'}

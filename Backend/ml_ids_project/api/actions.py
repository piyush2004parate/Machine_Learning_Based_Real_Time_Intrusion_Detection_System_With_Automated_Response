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
import subprocess

HERE = Path(__file__).resolve().parent
LOGS_DIR = HERE.parent.parent / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_BLOCKED_IPS_CACHE = set()

def _append_log(filename: str, payload: str) -> None:
    path = LOGS_DIR / filename
    ts = datetime.utcnow().isoformat()
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {payload}\n")


def block_ip(incident) -> dict:
    ip = getattr(incident, 'source_ip', None) or (incident.get('source_ip') if isinstance(incident, dict) else None)
    if not ip:
        return {'result': 'failed', 'reason': 'no source_ip'}
        
    if ip in _BLOCKED_IPS_CACHE:
        return {'result': 'ok', 'ip': ip, 'status': 'already_blocked'}
        
    try:
        # Step 1: Block INBOUND (Attacker -> You)
        cmd_in = f'netsh advfirewall firewall add rule name="IDS_Block_IN_{ip}" dir=in interface=any action=block remoteip={ip}'
        subprocess.run(cmd_in, shell=True, capture_output=True, check=True)
        
        # Step 2: Block OUTBOUND (You -> Attacker)
        # This stops the host from sending defensive responses/ACKs to the blocked IP
        cmd_out = f'netsh advfirewall firewall add rule name="IDS_Block_OUT_{ip}" dir=out interface=any action=block remoteip={ip}'
        subprocess.run(cmd_out, shell=True, capture_output=True, check=True)
        
        _BLOCKED_IPS_CACHE.add(ip)
        _append_log('blocked_ips.txt', f'Actually Blocked IP (In/Out) via Windows Firewall: {ip}')
        _append_log('actions.log', f"FULL ISOLATION executed securely in Windows Firewall for {ip}")
        return {'result': 'ok', 'ip': ip, 'status': 'isolated_in_firewall'}
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else str(e)
        if "requires elevation" in err_msg.lower() or "administrator" in err_msg.lower() or e.returncode == 1:
            _append_log('actions.log', f"CRITICAL: Permission Denied blocking {ip}. RUN BACKEND AS ADMINISTRATOR.")
            return {'result': 'failed', 'reason': 'requires_admin_privileges', 'details': 'Please run the Python Backend as Administrator'}
        _append_log('actions.log', f"Failed to block IP {ip} in Windows Firewall. Error: {err_msg}")
        return {'result': 'failed', 'reason': 'firewall_command_failed', 'details': err_msg}
    except Exception as e:
        _append_log('actions.log', f"Failed to execute firewall command for {ip}: {e}")
        return {'result': 'failed', 'reason': str(e)}

def unblock_ip(ip: str) -> dict:
    if not ip:
        return {'result': 'failed', 'reason': 'no source_ip'}
        
    try:
        # Remove both Inbound and Outbound rules
        subprocess.run(f'netsh advfirewall firewall delete rule name="IDS_Block_IN_{ip}"', shell=True, capture_output=True)
        subprocess.run(f'netsh advfirewall firewall delete rule name="IDS_Block_OUT_{ip}"', shell=True, capture_output=True)
        
        if ip in _BLOCKED_IPS_CACHE:
            _BLOCKED_IPS_CACHE.remove(ip)
            
        _append_log('actions.log', f"Unblock IP executed securely in Windows Firewall for {ip}")
        return {'result': 'ok', 'ip': ip, 'status': 'unblocked_in_firewall'}
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if e.stderr else str(e)
        _append_log('actions.log', f"Failed to unblock IP {ip} in Windows Firewall: {err_msg}")
        return {'result': 'failed', 'reason': 'firewall_command_failed', 'details': err_msg}
    except Exception as e:
        _append_log('actions.log', f"Failed to execute unblock firewall command for {ip}: {e}")
        return {'result': 'failed', 'reason': str(e)}

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

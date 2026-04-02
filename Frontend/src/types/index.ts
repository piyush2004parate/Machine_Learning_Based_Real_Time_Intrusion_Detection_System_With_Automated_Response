export interface NetworkTraffic {
  id: string;
  timestamp: Date;
  source_ip: string;
  destination_ip: string;
  protocol: string;
  bytes: number;
  status: 'Normal' | 'Anomalous' | 'Blocked';
  severity?: 'Low' | 'Medium' | 'High' | 'Critical';
}

export interface ThreatIncident {
  id: string;
  timestamp: Date;
  source_ip: string;
  destination_ip: string;
  threat_type: 'Malware' | 'Phishing' | 'Anomaly' | 'Encrypted Threats' | 'DDoS' | 'Port Scan';
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  status: 'Active' | 'Blocked' | 'Investigating' | 'Resolved' | 'False Positive';
  description: string;
  confidence: number;
}

export interface SystemMetrics {
  totalPackets: number;
  activeThreats: number;
  blockedIps: number;
  falsePositives: number;
}

export interface ResponseRule {
  id: string;
  name: string;
  condition: string;
  action: 'Block IP' | 'Isolate Device' | 'Alert Admin' | 'Quarantine';
  is_active: boolean;
  created_at: Date;
  triggered_count: number;
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  action: string;
  target: string;
  result: 'Success' | 'Failed';
  details: string;
  severity: 'Info' | 'Warning' | 'Error';
}
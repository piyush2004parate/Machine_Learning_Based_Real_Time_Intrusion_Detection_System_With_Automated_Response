import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  ResponsiveContainer,
} from 'recharts';
import { MetricCard } from '../components/UI/MetricCard';
import { Package, Shield, Ban, AlertTriangle } from 'lucide-react';
import { ThreatIncident, NetworkTraffic } from '../types';
import { useToast } from '../hooks/useToast';

type ProtocolDataItem = {
  name: string;
  value: number;
  color: string;
};

const protocolColors: { [key: string]: string } = {
  TCP: '#00F5FF',
  UDP: '#FF6B35',
  ICMP: '#FFD700',
  HTTP: '#8A2BE2',
  FTP: '#32CD32',
  Other: '#A9A9A9',
};

export const Dashboard: React.FC = () => {
  const { showToast } = useToast();
  const [incidents, setIncidents] = useState<ThreatIncident[]>([]);
  const [metrics, setMetrics] = useState({
    totalPackets: 0,
    activeThreats: 0,
    blockedIps: 0,
    falsePositives: 0,
  });
  const [trafficData, setTrafficData] = useState<{ hour: string; packets: number; threats: number }[]>([]);
  const [protocolData, setProtocolData] = useState<ProtocolDataItem[]>([]);
  const [threatData, setThreatData] = useState<{ name: string; count: number }[]>([]);

  const fetchData = useCallback(async () => {
    try {
      const incidentsResponse = await axios.get<ThreatIncident[]>('http://127.0.0.1:8000/api/incidents/');
      const trafficResponse = await axios.get<NetworkTraffic[]>('http://127.0.0.1:8000/api/traffic/?limit=1000');

      const incidentsFetched = incidentsResponse.data;
      const traffic = trafficResponse.data;

      setIncidents(incidentsFetched);

      // 1. Calculate Metrics
      const activeThreats = incidentsFetched.filter(i => i.status === 'Active').length;
      const blockedIps = incidentsFetched.filter(i => i.status === 'Blocked').length;
      const falsePositives = incidentsFetched.filter(i => i.status === 'False Positive').length;

      setMetrics({
        totalPackets: traffic.length,
        activeThreats,
        blockedIps,
        falsePositives,
      });

      // 2. Process data for charts
      // Threat Categories Chart
      const threatCounts = incidentsFetched.reduce((acc: Record<string, number>, curr) => {
        acc[curr.threat_type] = (acc[curr.threat_type] || 0) + 1;
        return acc;
      }, {});
      setThreatData(Object.keys(threatCounts).map(key => ({ name: key, count: threatCounts[key] })));
      
      // Protocol Distribution Chart
      const protocolCounts = traffic.reduce((acc: { [key: string]: number }, curr) => {
        const protocol = protocolColors[curr.protocol] ? curr.protocol : 'Other';
        acc[protocol] = (acc[protocol] || 0) + 1;
        return acc;
      }, {});
      setProtocolData(Object.keys(protocolCounts).map(key => ({
        name: key,
        value: protocolCounts[key],
        color: protocolColors[key],
      })));

      // Live Traffic Chart (last 24 hours)
      const now = new Date();
      const trafficByHour: { [hour: string]: { hour: string; packets: number; threats: number } } = {};

      for (let i = 23; i >= 0; i--) {
        const date = new Date(now.getTime() - i * 60 * 60 * 1000);
        const hourKey = `${date.getHours().toString().padStart(2, '0')}:00`;
        trafficByHour[hourKey] = { hour: hourKey, packets: 0, threats: 0 };
      }

      traffic.forEach(packet => {
        const packetDate = new Date(packet.timestamp);
        if (now.getTime() - packetDate.getTime() < 24 * 60 * 60 * 1000) {
          const hourKey = `${packetDate.getHours().toString().padStart(2, '0')}:00`;
          if (trafficByHour[hourKey]) {
            trafficByHour[hourKey].packets += 1;
          }
        }
      });

      incidentsFetched.forEach(incident => {
        const incidentDate = new Date(incident.timestamp);
        if (now.getTime() - incidentDate.getTime() < 24 * 60 * 60 * 1000) {
          const hourKey = `${incidentDate.getHours().toString().padStart(2, '0')}:00`;
          if (trafficByHour[hourKey]) {
            trafficByHour[hourKey].threats += 1;
          }
        }
      });
      
      setTrafficData(Object.values(trafficByHour));

    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      showToast('error', 'Could not refresh dashboard data.');
    }
  }, [showToast]);

  useEffect(() => {
    fetchData(); // Fetch data initially
    const intervalId = setInterval(fetchData, 10000); // Refresh every 10 seconds

    return () => clearInterval(intervalId); // Cleanup on unmount
  }, [fetchData]);

  // Subscribe to live incidents via the same WebSocket used for traffic
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.hostname;
    const ws = new WebSocket(`${protocol}://${host}:8000/ws/traffic/`);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg && msg._type === 'incident' && msg.data) {
          const inc: ThreatIncident = msg.data;
          setIncidents((prev) => {
            const next = [inc, ...prev];
            // Update metrics
            const activeThreats = next.filter(i => i.status === 'Active').length;
            const blockedIps = next.filter(i => i.status === 'Blocked').length;
            const falsePositives = next.filter(i => i.status === 'False Positive').length;
            setMetrics((m) => ({ ...m, activeThreats, blockedIps, falsePositives }));
            // Update threat categories
            const counts = next.reduce((acc: Record<string, number>, curr) => {
              acc[curr.threat_type] = (acc[curr.threat_type] || 0) + 1;
              return acc;
            }, {} as Record<string, number>);
            setThreatData(Object.keys(counts).map(key => ({ name: key, count: counts[key] })));
            // Update threats-by-hour in traffic chart
            setTrafficData((prevTraffic) => {
              const d = new Date(inc.timestamp);
              const hourKey = `${d.getHours().toString().padStart(2, '0')}:00`;
              return prevTraffic.map(row => row.hour === hourKey ? { ...row, threats: row.threats + 1 } : row);
            });
            return next;
          });
        }
      } catch (e) {
        // ignore non-JSON payloads
      }
    };

    return () => ws.close();
  }, []);


  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Packets (1k)"
          value={metrics.totalPackets.toLocaleString()}
          icon={Package}
          color="cyan"
        />
        <MetricCard
          title="Active Threats"
          value={metrics.activeThreats}
          icon={Shield}
          color="red"
        />
        <MetricCard
          title="Blocked IPs"
          value={metrics.blockedIps}
          icon={Ban}
          color="yellow"
        />
        <MetricCard
          title="False Positives"
          value={metrics.falsePositives}
          icon={AlertTriangle}
          color="green"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Network Traffic (24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trafficData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
              />
              <Line
                type="monotone"
                dataKey="packets"
                stroke="#00F5FF"
                strokeWidth={2}
                dot={false}
                name="Packets"
              />
              <Line
                type="monotone"
                dataKey="threats"
                stroke="#FF6B35"
                strokeWidth={2}
                dot={false}
                name="Threats"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Protocol Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={protocolData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={5}
                dataKey="value"
                nameKey="name"
              >
                {protocolData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap justify-center mt-4 gap-4">
            {protocolData.map((entry, index) => (
              <div key={index} className="flex items-center">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-300">{entry.name} ({entry.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Threat Categories</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={threatData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F3F4F6'
              }}
              formatter={(value) => [value, 'Count']}
            />
            <Bar dataKey="count" fill="#00F5FF" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

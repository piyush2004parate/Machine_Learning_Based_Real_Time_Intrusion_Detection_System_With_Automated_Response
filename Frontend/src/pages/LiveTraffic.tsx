import React, { useEffect, useState } from 'react';
import { useToast } from '../hooks/useToast';
import { Play, Pause } from 'lucide-react';

interface NetworkTraffic {
  id: number;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  protocol: string;
  bytes: number;
  status: 'normal' | 'anomalous' | 'blocked';
  severity?: 'low' | 'medium' | 'high';
  // Optional extended flow metrics (may be undefined in live WS payload)
  dur?: number;
  service?: string;
  state?: string;
  spkts?: number;
  dpkts?: number;
  sbytes?: number;
  dbytes?: number;
  rate?: number;
  sttl?: number;
  dttl?: number;
  sload?: number;
  dload?: number;
  sinpkt?: number;
  dinpkt?: number;
  sjit?: number;
  djit?: number;

  smean?: number;
  dmean?: number;
  ct_srv_src?: number;
  ct_state_ttl?: number;
  ct_dst_ltm?: number;
  ct_src_dport_ltm?: number;
  ct_dst_sport_ltm?: number;
  ct_dst_src_ltm?: number;
  ct_src_ltm?: number;
  ct_srv_dst?: number;
  is_sm_ips_ports?: number;
  label?: number; // 0 normal, 1 malicious
}

export const LiveTraffic: React.FC = () => {
  const [traffic, setTraffic] = useState<NetworkTraffic[]>([]);
  const { showToast } = useToast();
  const [isPaused, setIsPaused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    if (isPaused) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.hostname;
    const port = 8000; // match Daphne server
    const ws = new WebSocket(`${protocol}://${host}:${port}/ws/traffic/`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      showToast('success', 'Live traffic feed connected');
    };

    ws.onmessage = (event) => {
      const newTraffic = JSON.parse(event.data);
      setTraffic((prevTraffic) => [newTraffic, ...prevTraffic]);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    // ws.onerror = (error) => {
    //   console.error('WebSocket error:', error);
    //   showToast('error', 'Live traffic feed disconnected. Check the server and your network connection.');
    // };

    return () => {
      ws.close();
    };
  }, [showToast, isPaused]);

  const apiBase = `${window.location.protocol === 'https:' ? 'https' : 'http'}://${window.location.hostname}:8000/api`;

  const handleClear = async () => {
    try {
      setIsBusy(true);
      const res = await fetch(`${apiBase}/traffic/clear/`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to clear');
      setTraffic([]);
      showToast('success', 'All traffic records deleted');
    } catch (e) {
      console.error(e);
      showToast('error', 'Failed to clear traffic');
    } finally {
      setIsBusy(false);
    }
  };

  const handleSearch = async () => {
    try {
      setIsBusy(true);
      const res = await fetch(`${apiBase}/traffic/search/?q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      setTraffic(data);
      showToast('success', `Loaded ${data.length} matching records`);
    } catch (e) {
      console.error(e);
      showToast('error', 'Search failed');
    } finally {
      setIsBusy(false);
    }
  };

  const getStatusBadge = (status: NetworkTraffic['status']) => {
    const colors = {
      normal: 'bg-green-500/20 text-green-400',
      anomalous: 'bg-yellow-500/20 text-yellow-400',
      blocked: 'bg-red-500/20 text-red-400',
    };
    return <span className={`px-2 py-1 rounded-full text-xs ${colors[status]}`}>{status}</span>;
  };

  return (
    <div className="bg-gray-900 text-white p-6 rounded-lg shadow-lg">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <h2 className="text-2xl font-bold">Live Network Traffic</h2>
        <div className="flex items-center gap-2">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search IP, protocol, status, severity"
            className="px-3 py-2 bg-gray-800 rounded-md outline-none border border-gray-700 w-72"
          />
          <button
            onClick={handleSearch}
            disabled={isBusy}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-md disabled:opacity-50"
          >
            Search
          </button>
          <button
            onClick={handleClear}
            disabled={isBusy}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-md disabled:opacity-50"
          >
            Clear All
          </button>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="flex items-center px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg"
          >
            {isPaused ? <Play className="mr-2" /> : <Pause className="mr-2" />}
            {isPaused ? 'Resume Feed' : 'Pause Feed'}
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="p-2">Time</th>
              <th className="p-2">Source IP</th>
              <th className="p-2">Destination IP</th>
              <th className="p-2">Protocol</th>
              <th className="p-2">Bytes</th>
              <th className="p-2">Status</th>
              <th className="p-2">Severity</th>
              <th className="p-2">dur</th>
              <th className="p-2">proto</th>
              <th className="p-2">service</th>
              <th className="p-2">state</th>
              <th className="p-2">spkts</th>
              <th className="p-2">dpkts</th>
              <th className="p-2">sbytes</th>
              <th className="p-2">dbytes</th>
              <th className="p-2">rate</th>
              <th className="p-2">sttl</th>
              <th className="p-2">dttl</th>
              <th className="p-2">sload</th>
              <th className="p-2">dload</th>
              <th className="p-2">sinpkt</th>
              <th className="p-2">dinpkt</th>
              <th className="p-2">sjit</th>
              <th className="p-2">djit</th>
              <th className="p-2">smean</th>
              <th className="p-2">dmean</th>
              <th className="p-2">ct_srv_src</th>
              <th className="p-2">ct_state_ttl</th>
              <th className="p-2">ct_dst_ltm</th>
              <th className="p-2">ct_src_dport_ltm</th>
              <th className="p-2">ct_dst_sport_ltm</th>
              <th className="p-2">ct_dst_src_ltm</th>
              <th className="p-2">ct_src_ltm</th>
              <th className="p-2">ct_srv_dst</th>
              <th className="p-2">is_sm_ips_ports</th>
              <th className="p-2">label</th>
            </tr>
          </thead>
          <tbody>
            {traffic.map((t) => (
              <tr key={t.id} className="border-b border-gray-800">
                <td className="p-2">{new Date(t.timestamp).toLocaleTimeString()}</td>
                <td className="p-2">{t.source_ip}</td>
                <td className="p-2">{t.destination_ip}</td>
                <td className="p-2">{t.protocol}</td>
                <td className="p-2">{t.bytes}</td>
                <td className="p-2">{getStatusBadge(t.status)}</td>
                <td className="p-2">{t.severity || '-'}</td>
                <td className="p-2">{t.dur ?? '-'}</td>
                <td className="p-2">{t.proto || t.protocol || '-'}</td>
                <td className="p-2">{t.service ?? '-'}</td>
                <td className="p-2">{t.state ?? '-'}</td>
                <td className="p-2">{t.spkts ?? '-'}</td>
                <td className="p-2">{t.dpkts ?? '-'}</td>
                <td className="p-2">{t.sbytes ?? '-'}</td>
                <td className="p-2">{t.dbytes ?? '-'}</td>
                <td className="p-2">{t.rate ?? '-'}</td>
                <td className="p-2">{t.sttl ?? '-'}</td>
                <td className="p-2">{t.dttl ?? '-'}</td>
                <td className="p-2">{t.sload ?? '-'}</td>
                <td className="p-2">{t.dload ?? '-'}</td>
                <td className="p-2">{t.sinpkt ?? '-'}</td>
                <td className="p-2">{t.dinpkt ?? '-'}</td>
                <td className="p-2">{t.sjit ?? '-'}</td>
                <td className="p-2">{t.djit ?? '-'}</td>
                <td className="p-2">{t.smean ?? '-'}</td>
                <td className="p-2">{t.dmean ?? '-'}</td>
                <td className="p-2">{t.ct_srv_src ?? '-'}</td>
                <td className="p-2">{t.ct_state_ttl ?? '-'}</td>
                <td className="p-2">{t.ct_dst_ltm ?? '-'}</td>
                <td className="p-2">{t.ct_src_dport_ltm ?? '-'}</td>
                <td className="p-2">{t.ct_dst_sport_ltm ?? '-'}</td>
                <td className="p-2">{t.ct_dst_src_ltm ?? '-'}</td>
                <td className="p-2">{t.ct_src_ltm ?? '-'}</td>
                <td className="p-2">{t.ct_srv_dst ?? '-'}</td>
                <td className="p-2">{t.is_sm_ips_ports ?? '-'}</td>
                <td className="p-2">{t.label ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
;

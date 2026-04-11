import React, { useEffect, useState } from 'react';
import { useToast } from '../hooks/useToast';
import { Search, Pause, Play } from 'lucide-react';
import { Modal } from '../components/UI/Modal';

interface NetworkTraffic {
  id: number;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  protocol: string;
  bytes: number;
  status: 'normal' | 'anomalous' | 'blocked';
  severity?: 'low' | 'medium' | 'high' | 'critical' | string;
  dur?: number;
  service?: string;
  state?: string;
  spkts?: number;
  dpkts?: number;
  rate?: number;
  is_sm_ips_ports?: number;
  label?: number; // 0 normal, 1 malicious
  fwd_seg_size_min?: number;
  fwd_header_len?: number;
  subflow_fwd_bytes?: number;
  bwd_header_len?: number;
  init_fwd_win?: number;
  total_fwd_packets?: number;
  fwd_packets_len_total?: number;
  rst_flag_cnt?: number;
  ece_flag_cnt?: number;
  fwd_packet_len_max?: number;
  subflow_bwd_packets?: number;
  avg_fwd_seg_size?: number;
  bwd_packets_len_total?: number;
  bwd_packets_s?: number;
  init_bwd_win?: number;
  fwd_iat_total?: number;
  subflow_bwd_bytes?: number;
  fwd_iat_mean?: number;
  fwd_packet_len_mean?: number;
  fwd_iat_min?: number;
}

export const LiveTraffic: React.FC = () => {
  const [traffic, setTraffic] = useState<NetworkTraffic[]>([]);
  const { showToast } = useToast();
  const [isPaused, setIsPaused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const [selectedTraffic, setSelectedTraffic] = useState<NetworkTraffic | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toLocaleTimeString());

  useEffect(() => {
    if (isPaused) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.hostname;
    const port = 8000;
    const ws = new WebSocket(`${protocol}://${host}:${port}/ws/traffic/`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      showToast('success', 'Live traffic feed connected');
    };

    ws.onmessage = (event) => {
      const newTraffic = JSON.parse(event.data);
      if (newTraffic._type === 'incident') return; // Prevent incident rows from crashing the traffic table
      setTraffic((prevTraffic) => [newTraffic, ...prevTraffic]);
      setLastUpdated(new Date().toLocaleTimeString());
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, [showToast, isPaused]);

  const apiBase = `${window.location.protocol === 'https:' ? 'https' : 'http'}://${window.location.hostname}:8000/api`;

  const handleRefresh = async () => {
    try {
      setIsBusy(true);
      const res = await fetch(`${apiBase}/traffic/search/?q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error('Refresh failed');
      const data = await res.json();
      setTraffic(data);
      setLastUpdated(new Date().toLocaleTimeString());
      showToast('success', `Refreshed feed. Loaded ${data.length} records.`);
    } catch (e) {
      console.error(e);
      showToast('error', 'Refresh failed');
    } finally {
      setIsBusy(false);
    }
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return <span className="inline-flex items-center px-4 py-1.5 rounded-full text-xs font-semibold bg-gray-500/20 text-gray-400 border border-gray-500/30">-</span>;
    switch (status.toLowerCase()) {
      case 'normal':
      case 'benign':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-600/30 text-gray-300 border border-gray-500/30 shadow-sm">Benign</span>;
      case 'anomalous':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 shadow-sm">Anomalous</span>;
      case 'blocked':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30 shadow-sm">Blocked</span>;
      default:
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-600/30 text-gray-300 border border-gray-500/30">{status}</span>;
    }
  };

  const getSeverityBadge = (severity?: string) => {
    if (!severity) return <span className="text-gray-500">-</span>;
    switch (severity.toLowerCase()) {
      case 'low':
        return <span className="inline-flex justify-center items-center px-3 py-1 min-w-[70px] rounded-full text-[11px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 tracking-wider shadow-sm">LOW</span>;
      case 'medium':
        return <span className="inline-flex justify-center items-center px-3 py-1 min-w-[70px] rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 tracking-wider shadow-sm">MEDIUM</span>;
      case 'high':
        return <span className="inline-flex justify-center items-center px-3 py-1 min-w-[70px] rounded-full text-[11px] font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30 tracking-wider shadow-sm">HIGH</span>;
      case 'critical':
        return <span className="inline-flex justify-center items-center px-3 py-1 min-w-[70px] rounded-full text-[11px] font-bold bg-red-600/30 text-red-500 border border-red-500/50 tracking-wider shadow-sm animate-pulse">CRITICAL</span>;
      default:
        return <span className="text-gray-500">-</span>;
    }
  };

  const filteredTraffic = traffic.filter(t =>
    (t.source_ip || '').includes(searchQuery) ||
    (t.destination_ip || '').includes(searchQuery) ||
    (t.protocol || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.status || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full">
      {/* Header & Actions */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-6">
        <div>
          <h1 className="text-[24px] font-bold text-white tracking-tight flex items-center gap-3">
            Live Network Traffic
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
          </h1>
          <p className="text-sm text-gray-400 mt-1 font-medium tracking-wide">Last updated: {lastUpdated}</p>
        </div>
        <div className="flex gap-3 mt-4 md:mt-0">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-5 py-2 text-sm font-semibold rounded-lg shadow-lg border backdrop-blur-md transition-all duration-300 flex items-center gap-2 hover:-translate-y-0.5 ${
              isPaused 
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30 shadow-amber-900/20' 
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30 shadow-emerald-900/20'
            }`}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            {isPaused ? 'Resume Feed' : 'Pause Feed'}
          </button>
          <button
            onClick={handleRefresh}
            disabled={isBusy}
            className="px-5 py-2 bg-gray-800/80 hover:bg-gray-700/80 text-cyan-400 hover:text-cyan-300 border border-gray-700 hover:border-cyan-500/50 text-sm font-semibold rounded-lg shadow-lg backdrop-blur-md transition-all duration-300 flex items-center gap-2 disabled:opacity-50 hover:-translate-y-0.5"
          >
            Refresh Data
          </button>
        </div>
      </div>

      {/* Main Table Container */}
      <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl overflow-hidden">
        {/* Toolbar */}
        <div className="p-5 border-b border-gray-700/50 flex flex-col md:flex-row justify-between items-center gap-5 bg-gray-800/50">
          {/* Status Formatted Toggle Indicators */}
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <div className="flex items-center gap-2 px-4 py-1.5 bg-gray-800/80 rounded-full border border-gray-700/60 shadow-inner">
              <div className="w-2.5 h-2.5 bg-gray-400 rounded-full"></div>
              <span className="text-gray-300 font-medium">Benign <span className="text-gray-500 ml-1">({traffic.filter(t => (t.status || '').toLowerCase() === 'normal' || (t.status || '').toLowerCase() === 'benign').length})</span></span>
            </div>
            <div className="flex items-center gap-2 px-4 py-1.5 bg-yellow-900/20 rounded-full border border-yellow-700/30 shadow-inner">
              <div className="w-2.5 h-2.5 bg-yellow-500 rounded-full shadow-[0_0_8px_rgba(234,179,8,0.6)]"></div>
              <span className="text-yellow-500 font-medium">Anomalous <span className="text-yellow-700 ml-1">({traffic.filter(t => (t.status || '').toLowerCase() === 'anomalous').length})</span></span>
            </div>
            <div className="flex items-center gap-2 px-4 py-1.5 bg-red-900/20 rounded-full border border-red-700/30 shadow-inner">
              <div className="w-2.5 h-2.5 bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse"></div>
              <span className="text-red-400 font-medium">Blocked <span className="text-red-800 ml-1">({traffic.filter(t => (t.status || '').toLowerCase() === 'blocked').length})</span></span>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative w-full md:max-w-xs group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 group-focus-within:text-cyan-400 transition-colors" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-900/50 border border-gray-700 text-sm text-gray-200 rounded-lg py-2 pl-9 pr-4 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all shadow-inner placeholder-gray-500"
            />
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto min-h-[400px]">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-gray-800/80">
              <tr className="text-gray-400 text-[11px] font-bold tracking-widest uppercase border-b border-gray-700/50 shadow-sm">
                <th className="py-4 px-6">Time</th>
                <th className="py-4 px-6">Source IP</th>
                <th className="py-4 px-6">Destination IP</th>
                <th className="py-4 px-6">Protocol</th>
                <th className="py-4 px-6">Bytes</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {filteredTraffic.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setSelectedTraffic(t)}
                  className="hover:bg-cyan-900/10 transition-all cursor-pointer group"
                >
                  <td className="py-4 px-6 text-gray-400 group-hover:text-cyan-100 transition-colors font-mono text-[13px]">{t.timestamp ? new Date(t.timestamp).toLocaleTimeString([], { hour12: false }) : '-'}</td>
                  <td className="py-4 px-6 font-mono text-cyan-400/80 group-hover:text-cyan-300 transition-colors font-medium">{t.source_ip || '-'}</td>
                  <td className="py-4 px-6 font-mono text-cyan-400/80 group-hover:text-cyan-300 transition-colors font-medium">{t.destination_ip || '-'}</td>
                  <td className="py-4 px-6 text-gray-400 font-semibold group-hover:text-white transition-colors">{t.protocol || '-'}</td>
                  <td className="py-4 px-6 text-emerald-400/80 font-mono group-hover:text-emerald-300 transition-colors">{t.bytes !== undefined && t.bytes !== null ? t.bytes.toLocaleString() : '-'}</td>
                  <td className="py-4 px-6">{getStatusBadge(t.status)}</td>
                  <td className="py-4 px-6">{getSeverityBadge(t.severity)}</td>
                </tr>
              ))}
              {filteredTraffic.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-gray-500 font-medium">No live traffic matching criteria.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer Pagination */}
        <div className="p-5 border-t border-gray-700/50 flex justify-between items-center text-sm text-gray-400 bg-[#212633]">
          <div>Showing 1-{Math.min(filteredTraffic.length, 15)} of {filteredTraffic.length} results</div>
          <div className="flex gap-2">
            <button className="px-5 py-2 border border-gray-600 rounded-md hover:bg-gray-700 hover:text-white transition-colors">Previous</button>
            <button className="px-5 py-2 bg-[#2B3243] border border-gray-600 rounded-md hover:bg-gray-600 hover:text-white transition-colors text-white">Next</button>
          </div>
        </div>
      </div>

      {/* Expandable ML Modal */}
      <Modal
        isOpen={!!selectedTraffic}
        onClose={() => setSelectedTraffic(null)}
        title="Deep Packet Inspection Matrix (CIC-IDS2018)"
        size="lg"
      >
        {selectedTraffic && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 bg-[#1E222D] p-6 rounded-lg overflow-y-auto max-h-[60vh] border border-gray-700 shadow-xl">
              {[
                { label: "Duration", value: selectedTraffic.dur !== undefined ? selectedTraffic.dur.toFixed(2) : '-' },
                { label: "Label Flag", value: selectedTraffic.label !== undefined ? (selectedTraffic.label === 1 ? 'Malicious (1)' : 'Normal (0)') : '-' },
                { label: "State", value: selectedTraffic.state ?? '-' },
                { label: "Fwd Pkts", value: selectedTraffic.spkts ?? '-' },
                { label: "Bwd Pkts", value: selectedTraffic.dpkts ?? '-' },
                { label: "Rate", value: selectedTraffic.rate !== undefined ? selectedTraffic.rate.toFixed(2) : '-' },
                { label: "Fwd Seg Size Min", value: selectedTraffic.fwd_seg_size_min ?? '-' },
                { label: "Fwd Header Len", value: selectedTraffic.fwd_header_len ?? '-' },
                { label: "Subflow Fwd Bytes", value: selectedTraffic.subflow_fwd_bytes ?? '-' },
                { label: "Bwd Header Len", value: selectedTraffic.bwd_header_len ?? '-' },
                { label: "Init Fwd Win", value: selectedTraffic.init_fwd_win ?? '-' },
                { label: "Total Fwd Pkts", value: selectedTraffic.total_fwd_packets ?? '-' },
                { label: "Fwd Pkts Len Total", value: selectedTraffic.fwd_packets_len_total ?? '-' },
                { label: "RST Flag Cnt", value: selectedTraffic.rst_flag_cnt ?? '-' },
                { label: "ECE Flag Cnt", value: selectedTraffic.ece_flag_cnt ?? '-' },
                { label: "Fwd Pkt Len Max", value: selectedTraffic.fwd_packet_len_max ?? '-' },
                { label: "Subflow Bwd Pkts", value: selectedTraffic.subflow_bwd_packets ?? '-' },
                { label: "Avg Fwd Seg Size", value: selectedTraffic.avg_fwd_seg_size !== undefined ? selectedTraffic.avg_fwd_seg_size.toFixed(2) : '-' },
                { label: "Bwd Pkts Len Total", value: selectedTraffic.bwd_packets_len_total ?? '-' },
                { label: "Bwd Pkts/s", value: selectedTraffic.bwd_packets_s !== undefined ? selectedTraffic.bwd_packets_s.toFixed(2) : '-' },
                { label: "Init Bwd Win", value: selectedTraffic.init_bwd_win ?? '-' },
                { label: "Fwd IAT Total", value: selectedTraffic.fwd_iat_total !== undefined ? selectedTraffic.fwd_iat_total.toFixed(4) : '-' },
                { label: "Subflow Bwd Bytes", value: selectedTraffic.subflow_bwd_bytes ?? '-' },
                { label: "Fwd IAT Mean", value: selectedTraffic.fwd_iat_mean !== undefined ? selectedTraffic.fwd_iat_mean.toFixed(4) : '-' },
                { label: "Fwd Pkt Len Mean", value: selectedTraffic.fwd_packet_len_mean !== undefined ? selectedTraffic.fwd_packet_len_mean.toFixed(2) : '-' },
                { label: "Fwd IAT Min", value: selectedTraffic.fwd_iat_min !== undefined ? selectedTraffic.fwd_iat_min.toFixed(4) : '-' }
              ].map((stat, idx) => (
                <div key={idx} className="bg-[#242A38] p-3 rounded-md border border-gray-700/50 shadow-sm">
                  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">{stat.label}</label>
                  <p className="text-sm font-medium text-blue-50">{stat.value}</p>
                </div>
              ))}
            </div>
            <div className="flex justify-end pt-4">
              <button
                onClick={() => setSelectedTraffic(null)}
                className="px-6 py-2.5 bg-[#2B3243] hover:bg-gray-600 text-white rounded-md transition-colors shadow-sm font-medium text-sm"
              >
                Dismiss Selection
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

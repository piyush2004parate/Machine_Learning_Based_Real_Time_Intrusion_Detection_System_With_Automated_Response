import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DataTable } from '../components/UI/DataTable';
import { Modal } from '../components/UI/Modal';
import { ThreatIncident } from '../types';
import { format } from 'date-fns';
import { Eye, Shield, Ban, CheckCircle, Unlock } from 'lucide-react';
import { useToast } from '../hooks/useToast';

export const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<ThreatIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<ThreatIncident | null>(null);
  const { showToast } = useToast();

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await axios.get<ThreatIncident[]>('http://127.0.0.1:8000/api/incidents/');
        setIncidents(response.data);
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
        showToast('error', 'Could not load incident data.');
      }
    };

    fetchIncidents();
  }, [showToast]);

  const getSeverityBadge = (severity: ThreatIncident['severity']) => {
    const styles: Record<string, string> = {
      Low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      Medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      High: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      Critical: 'bg-red-600/20 text-red-500 border-red-500/50 animate-pulse',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-[11px] font-bold tracking-widest uppercase border shadow-sm ${styles[severity]}`}>
        {severity}
      </span>
    );
  };

  const getStatusBadge = (status: ThreatIncident['status']) => {
    const styles: Record<string, string> = {
      Active: 'bg-red-500/20 text-red-500 border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.4)]',
      Blocked: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      Investigating: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
      Resolved: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.3)]',
      'False Positive': 'bg-gray-600/30 text-gray-400 border-gray-500/30',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const handleUpdateIncidentStatus = async (incident: ThreatIncident, status: string) => {
    try {
      await axios.patch(`http://127.0.0.1:8000/api/incidents/${incident.id}/`, { status });
      setIncidents(prev =>
        prev.map(i =>
          i.id === incident.id ? { ...i, status: status as ThreatIncident['status'] } : i
        )
      );
      showToast('success', `Incident status updated to ${status}`);
    } catch (error) {
      console.error(`Failed to update incident status to ${status}:`, error);
      showToast('error', `Could not update incident status.`);
    }
  };

  const handleBlockIp = (incident: ThreatIncident) => {
    handleUpdateIncidentStatus(incident, 'Blocked');
    showToast('success', `IP ${incident.source_ip} has been blocked`);
  };

  const handleUnblockIp = async (incident: ThreatIncident) => {
    try {
      await axios.post(`http://127.0.0.1:8000/api/incidents/${incident.id}/unblock/`);
      setIncidents(prev =>
        prev.map(i =>
          i.id === incident.id ? { ...i, status: 'Resolved' } : i
        )
      );
      showToast('success', `IP ${incident.source_ip} has been successfully unblocked!`);
    } catch (error) {
      console.error(`Failed to unblock IP ${incident.source_ip}:`, error);
      showToast('error', `Could not unblock IP. Is the server running as Admin?`);
    }
  };

  const handleIsolateDevice = (incident: ThreatIncident) => {
    handleUpdateIncidentStatus(incident, 'Blocked');
    showToast('success', `Device ${incident.source_ip} has been isolated`);
  };

  const handleMarkFalsePositive = (incident: ThreatIncident) => {
    handleUpdateIncidentStatus(incident, 'False Positive');
  };

  const columns = [
    {
      key: 'id' as keyof ThreatIncident,
      header: 'ID',
      render: (item: ThreatIncident) => (typeof item.id === 'string' ? item.id.split('-')[0] : 'N/A'),
      sortable: true,
    },
    {
      key: 'timestamp' as keyof ThreatIncident,
      header: 'Time',
      render: (item: ThreatIncident) => format(new Date(item.timestamp), 'MMM dd, HH:mm'),
      sortable: true,
    },
    {
      key: 'source_ip' as keyof ThreatIncident,
      header: 'Source IP',
      sortable: true,
    },
    {
      key: 'destination_ip' as keyof ThreatIncident,
      header: 'Destination IP',
      sortable: true,
    },
    {
      key: 'threat_type' as keyof ThreatIncident,
      header: 'Threat Type',
      sortable: true,
    },
    {
      key: 'severity' as keyof ThreatIncident,
      header: 'Severity',
      render: (item: ThreatIncident) => getSeverityBadge(item.severity),
      sortable: true,
    },
    {
      key: 'status' as keyof ThreatIncident,
      header: 'Status',
      render: (item: ThreatIncident) => getStatusBadge(item.status),
      sortable: true,
    },
    {
      key: 'confidence' as keyof ThreatIncident,
      header: 'Confidence',
      render: (item: ThreatIncident) => (
        <div className="w-[85px]">
          <div className="w-full bg-gray-800 rounded-full h-1.5 mb-1 overflow-hidden">
            <div className="bg-cyan-400 h-1.5 rounded-full shadow-[0_0_10px_rgba(34,211,238,0.8)]" style={{ width: `${item.confidence}%` }}></div>
          </div>
          <span className="text-[10.5px] font-bold text-cyan-400/90 tracking-wider">{item.confidence}% ML</span>
        </div>
      ),
      sortable: true,
    },
  {
    key: 'actions' as keyof ThreatIncident,
    header: 'Actions',
        render: (item: ThreatIncident) => (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedIncident(item)}
              className="p-1.5 bg-gray-800 border border-gray-700 hover:border-cyan-500/50 rounded-full text-cyan-400 hover:bg-cyan-900/30 transition-all shadow-sm group"
              title="View Details"
            >
              <Eye className="h-4 w-4 group-hover:scale-110 transition-transform" />
            </button>
            {item.status === 'Active' && (
              <>
                <button
                  onClick={() => handleBlockIp(item)}
                  className="p-1.5 bg-gray-800 border border-gray-700 hover:border-red-500/50 rounded-full text-red-500 hover:bg-red-900/30 transition-all shadow-sm group"
                  title="Block IP"
                >
                  <Ban className="h-4 w-4 group-hover:scale-110 transition-transform" />
                </button>
                <button
                  onClick={() => handleIsolateDevice(item)}
                  className="p-1.5 bg-gray-800 border border-gray-700 hover:border-orange-500/50 rounded-full text-orange-400 hover:bg-orange-900/30 transition-all shadow-sm group"
                  title="Isolate Device"
                >
                  <Shield className="h-4 w-4 group-hover:scale-110 transition-transform" />
                </button>
                <button
                  onClick={() => handleMarkFalsePositive(item)}
                  className="p-1.5 bg-gray-800 border border-gray-700 hover:border-gray-400/50 rounded-full text-gray-400 hover:text-white hover:bg-gray-700 transition-all shadow-sm group"
                  title="Mark as False Positive"
                >
                  <CheckCircle className="h-4 w-4 group-hover:scale-110 transition-transform" />
                </button>
              </>
            )}
            {item.status === 'Blocked' && (
              <button
                onClick={() => handleUnblockIp(item)}
                className="p-1.5 bg-gray-800 border border-gray-700 hover:border-emerald-500/50 rounded-full text-emerald-400 hover:bg-emerald-900/30 transition-all shadow-sm group"
                title="Unblock IP"
              >
                <Unlock className="h-4 w-4 group-hover:scale-110 transition-transform" />
              </button>
            )}
          </div>
        ),
        sortable: false,
      },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-[24px] font-bold text-white tracking-tight flex items-center gap-3">
            Security Incidents
          </h2>
          <p className="text-sm text-gray-400 mt-1 font-medium tracking-wide">Detected threats and anomalous activities</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[13px] font-medium">
          <div className="flex items-center gap-2 px-4 py-1.5 bg-red-900/20 border border-red-500/30 rounded-full shadow-inner">
            <div className="w-2.5 h-2.5 bg-red-500 rounded-full shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse"></div>
            <span className="text-red-400">Active <span className="ml-1 text-red-500/80">({incidents.filter(i => i.status === 'Active').length})</span></span>
          </div>
          <div className="flex items-center gap-2 px-4 py-1.5 bg-amber-900/20 border border-amber-500/30 rounded-full shadow-inner">
            <div className="w-2.5 h-2.5 bg-orange-500 rounded-full shadow-[0_0_8px_rgba(249,115,22,0.6)]"></div>
            <span className="text-orange-400">Blocked <span className="ml-1 text-orange-500/80">({incidents.filter(i => i.status === 'Blocked').length})</span></span>
          </div>
          <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-900/20 border border-emerald-500/30 rounded-full shadow-inner">
            <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
            <span className="text-emerald-400">Resolved <span className="ml-1 text-emerald-500/80">({incidents.filter(i => i.status === 'Resolved').length})</span></span>
          </div>
        </div>
      </div>

      <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-900/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10">
          <DataTable
            data={incidents}
            columns={columns}
            searchable
            pageSize={10}
          />
        </div>
      </div>

      <Modal
        isOpen={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title="Incident Details"
        size="lg"
      >
        {selectedIncident && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Incident ID
                </label>
                <p className="text-white">{selectedIncident.id}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Timestamp
                </label>
                <p className="text-white">{format(new Date(selectedIncident.timestamp), 'PPpp')}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Source IP
                </label>
                <p className="text-white font-mono">{selectedIncident.source_ip}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Destination IP
                </label>
                <p className="text-white font-mono">{selectedIncident.destination_ip}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Threat Type
                </label>
                <p className="text-white">{selectedIncident.threat_type}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Confidence Level
                </label>
                <p className="text-white">{selectedIncident.confidence}%</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Severity
                </label>
                <div>{getSeverityBadge(selectedIncident.severity)}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Status
                </label>
                <div>{getStatusBadge(selectedIncident.status)}</div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Description
              </label>
              <p className="text-white bg-gray-700 p-3 rounded-lg">
                {selectedIncident.description}
              </p>
            </div>

            {selectedIncident.status === 'Active' && (
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-700">
                <button
                  onClick={() => {
                    handleMarkFalsePositive(selectedIncident);
                    setSelectedIncident(null);
                  }}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                >
                  Mark as False Positive
                </button>
                <button
                  onClick={() => {
                    handleIsolateDevice(selectedIncident);
                    setSelectedIncident(null);
                  }}
                  className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
                >
                  <Shield className="h-4 w-4 mr-2 inline" />
                  Isolate Device
                </button>
                <button
                  onClick={() => {
                    handleBlockIp(selectedIncident);
                    setSelectedIncident(null);
                  }}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  <Ban className="h-4 w-4 mr-2 inline" />
                  Block IP
                </button>
              </div>
            )}
            {selectedIncident.status === 'Blocked' && (
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-700">
                <button
                  onClick={() => {
                    handleUnblockIp(selectedIncident);
                    setSelectedIncident(null);
                  }}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors shadow-lg shadow-green-500/20"
                >
                  <Unlock className="h-4 w-4 mr-2 inline" />
                  Unblock IP
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
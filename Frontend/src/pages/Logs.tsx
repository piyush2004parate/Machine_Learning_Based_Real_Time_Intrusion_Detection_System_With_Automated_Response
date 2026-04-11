import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DataTable } from '../components/UI/DataTable';
import { LogEntry } from '../types';
import { format } from 'date-fns';
import { Download, Calendar } from 'lucide-react';
import { useToast } from '../hooks/useToast';

export const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [severityFilter, setSeverityFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');
  const { showToast } = useToast();

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get<LogEntry[]>('http://127.0.0.1:8000/api/logs/');
        setLogs(response.data);
      } catch (error) {
        console.error("Failed to fetch logs:", error);
        showToast('error', 'Could not load log data.');
      }
    };

    fetchLogs();
  }, [showToast]);

  const getSeverityBadge = (severity: LogEntry['severity']) => {
    const styles: Record<string, string> = {
      Info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
      Warning: 'bg-amber-500/20 text-amber-500 border border-amber-500/30',
      Error: 'bg-red-500/20 text-red-500 border border-red-500/50 shadow-[0_0_8px_rgba(239,68,68,0.4)]',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider shadow-sm ${styles[severity]}`}>
        {severity}
      </span>
    );
  };

  const getResultBadge = (result: LogEntry['result']) => {
    const styles: Record<string, string> = {
      Success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_8px_rgba(16,185,129,0.3)]',
      Failed: 'bg-red-500/20 text-red-500 border border-red-500/30',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider shadow-sm ${styles[result]}`}>
        {result}
      </span>
    );
  };

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Action', 'Target', 'Result', 'Severity', 'Details'];
    const csvContent = [
      headers.join(','),
      ...filteredLogs.map(log =>
        [
          format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss'),
          log.action,
          log.target,
          log.result,
          log.severity,
          `"${log.details}"`
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security-logs-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    showToast('success', 'Logs exported successfully');
  };

  const filteredLogs = logs.filter(log => {
    const logDate = new Date(log.timestamp);
    if (severityFilter !== 'all' && log.severity !== severityFilter) return false;
    if (actionFilter !== 'all' && log.action !== actionFilter) return false;
    if (dateRange.start && logDate < new Date(dateRange.start)) return false;
    if (dateRange.end && logDate > new Date(dateRange.end)) return false;
    return true;
  });

  const columns = [
    {
      key: 'timestamp' as keyof LogEntry,
      header: 'Timestamp',
      render: (item: LogEntry) => format(new Date(item.timestamp), 'MMM dd, HH:mm:ss'),
      sortable: true,
    },
    {
      key: 'action' as keyof LogEntry,
      header: 'Action',
      sortable: true,
    },
    {
      key: 'target' as keyof LogEntry,
      header: 'Target',
      render: (item: LogEntry) => (
        <span className="font-mono text-[13px] text-cyan-400/80 max-w-[150px] truncate block" title={item.target}>{item.target}</span>
      ),
      sortable: true,
    },
    {
      key: 'result' as keyof LogEntry,
      header: 'Result',
      render: (item: LogEntry) => getResultBadge(item.result),
      sortable: true,
    },
    {
      key: 'severity' as keyof LogEntry,
      header: 'Severity',
      render: (item: LogEntry) => getSeverityBadge(item.severity),
      sortable: true,
    },
    {
      key: 'details' as keyof LogEntry,
      header: 'Details',
      render: (item: LogEntry) => (
        <span className="text-[13px] text-gray-400 max-w-[200px] truncate block" title={item.details}>
          {item.details}
        </span>
      ),
      sortable: false,
    },
  ];

  const uniqueActions = [...new Set(logs.map(log => log.action))];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-[24px] font-bold text-white tracking-tight flex items-center gap-3">Logs & Reports</h2>
          <p className="text-sm text-gray-400 mt-1 font-medium tracking-wide">Security event logs and system activities</p>
        </div>

        <button
          onClick={handleExportCSV}
          className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 rounded-lg shadow-[0_0_15px_rgba(16,185,129,0.2)] transition-all font-semibold text-sm hover:-translate-y-0.5"
        >
          <Download className="h-4 w-4" />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between mb-6 gap-4">
          <h3 className="text-lg font-bold text-white tracking-wide">Security Logs</h3>
          
          <div className="flex flex-wrap items-center gap-3 bg-gray-800/50 p-2 rounded-xl border border-gray-700/50 shadow-inner">
            <div className="flex items-center space-x-2 px-2 border-r border-gray-700">
              <Calendar className="h-4 w-4 text-cyan-500" />
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="bg-transparent border-none text-gray-300 text-sm focus:outline-none focus:ring-0 [&::-webkit-calendar-picker-indicator]:filter-invert"
              />
              <span className="text-gray-500 text-xs">to</span>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="bg-transparent border-none text-gray-300 text-sm focus:outline-none focus:ring-0"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1.5 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-300 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            >
              <option value="all">All Severities</option>
              <option value="Info">Info</option>
              <option value="Warning">Warning</option>
              <option value="Error">Error</option>
            </select>

            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-3 py-1.5 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-300 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
            >
              <option value="all">All Actions</option>
              {uniqueActions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-4 text-[13px] font-medium text-cyan-400">
          Showing {filteredLogs.length} of {logs.length} log entries
        </div>

        <DataTable
          data={filteredLogs}
          columns={columns}
          searchable
          pageSize={10}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Summary Card */}
        <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-900/20 rounded-full blur-2xl group-hover:bg-emerald-900/30 transition-colors"></div>
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6 relative z-10">Log Summary</h3>
          <div className="space-y-5 relative z-10">
            <div className="flex items-end justify-between border-b border-gray-700/50 pb-3">
              <span className="text-gray-400 font-medium text-sm">Total Entries</span>
              <span className="text-white font-bold text-2xl">{logs.length}</span>
            </div>
            <div className="flex items-end justify-between border-b border-gray-700/50 pb-3">
              <span className="text-gray-400 font-medium text-sm">Success Rate</span>
              <span className="text-emerald-400 font-bold text-2xl drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]">
                {logs.length > 0 ? Math.round((logs.filter(l => l.result === 'Success').length / logs.length) * 100) : 0}%
              </span>
            </div>
            <div className="flex items-end justify-between">
              <span className="text-gray-400 font-medium text-sm">Errors</span>
              <span className="text-red-500 font-bold text-2xl">
                {logs.filter(l => l.severity === 'Error').length}
              </span>
            </div>
          </div>
        </div>

        {/* Most Common Actions Category Card */}
        <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-900/20 rounded-full blur-2xl group-hover:bg-blue-900/30 transition-colors"></div>
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6 relative z-10">Most Common Actions</h3>
          <div className="space-y-4 relative z-10">
            {uniqueActions.slice(0, 5).map(action => (
              <div key={action} className="flex justify-between items-center group/item hover:bg-gray-800/50 p-2 -mx-2 rounded-lg transition-colors">
                <span className="text-cyan-400 text-[13px] font-medium">{action}</span>
                <span className="text-white font-bold bg-gray-800 px-3 py-1 rounded-full text-xs border border-gray-700 group-hover/item:border-cyan-500/50 transition-colors">
                  {logs.filter(l => l.action === action).length}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Mini-feed Card */}
        <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-900/20 rounded-full blur-2xl group-hover:bg-purple-900/30 transition-colors"></div>
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6 relative z-10">Recent Activity</h3>
          <div className="space-y-4 relative z-10">
            {logs.slice(0, 5).map((log, index) => (
              <div key={log.id} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`w-2.5 h-2.5 rounded-full ${log.severity === 'Error' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]' : 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.6)]'}`}></div>
                  {index !== 4 && <div className="flex-1 w-px bg-gray-700/50 my-1"></div>}
                </div>
                <div className="-mt-1.5 pb-2">
                  <p className="text-[13px] text-white font-medium">{log.action}</p>
                  <p className="text-[11px] font-mono text-gray-500 mt-0.5">
                    {format(new Date(log.timestamp), 'MMM dd, HH:mm')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
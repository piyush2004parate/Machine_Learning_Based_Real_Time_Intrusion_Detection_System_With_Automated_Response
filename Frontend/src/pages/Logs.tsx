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
    const colors = {
      Info: 'bg-blue-500',
      Warning: 'bg-yellow-500',
      Error: 'bg-red-500',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${colors[severity]}`}>
        {severity}
      </span>
    );
  };

  const getResultBadge = (result: LogEntry['result']) => {
    const colors = {
      Success: 'bg-green-500',
      Failed: 'bg-red-500',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${colors[result]}`}>
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
        <span className="font-mono text-sm">{item.target}</span>
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
        <span className="text-sm text-gray-300 max-w-xs truncate">
          {item.details}
        </span>
      ),
      sortable: false,
    },
  ];

  const uniqueActions = [...new Set(logs.map(log => log.action))];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Logs & Reports</h2>
          <p className="text-gray-400">Security event logs and system activities</p>
        </div>

        <button
          onClick={handleExportCSV}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Security Logs</h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
              <span className="text-gray-400">to</span>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              <option value="all">All Severities</option>
              <option value="Info">Info</option>
              <option value="Warning">Warning</option>
              <option value="Error">Error</option>
            </select>

            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-3 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
            >
              <option value="all">All Actions</option>
              {uniqueActions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mb-4 text-sm text-gray-400">
          Showing {filteredLogs.length} of {logs.length} log entries
        </div>

        <DataTable
          data={filteredLogs}
          columns={columns}
          searchable
          pageSize={15}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Log Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Entries</span>
              <span className="text-white font-semibold">{logs.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Success Rate</span>
              <span className="text-green-400 font-semibold">
                {logs.length > 0 ? Math.round((logs.filter(l => l.result === 'Success').length / logs.length) * 100) : 0}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Errors</span>
              <span className="text-red-400 font-semibold">
                {logs.filter(l => l.severity === 'Error').length}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Most Common Actions</h3>
          <div className="space-y-3">
            {uniqueActions.slice(0, 5).map(action => (
              <div key={action} className="flex justify-between">
                <span className="text-gray-400 text-sm">{action}</span>
                <span className="text-white font-semibold">
                  {logs.filter(l => l.action === action).length}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {logs.slice(0, 5).map(log => (
              <div key={log.id} className="border-l-2 border-cyan-400 pl-3">
                <p className="text-sm text-white">{log.action}</p>
                <p className="text-xs text-gray-400">
                  {format(new Date(log.timestamp), 'MMM dd, HH:mm')}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
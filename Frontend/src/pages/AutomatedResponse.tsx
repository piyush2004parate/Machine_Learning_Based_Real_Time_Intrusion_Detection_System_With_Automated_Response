import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DataTable } from '../components/UI/DataTable';
import { ResponseRule } from '../types';
import { format } from 'date-fns';
import { ToggleLeft, ToggleRight, Plus, Trash2, RotateCcw, Shield } from 'lucide-react';
import { useToast } from '../hooks/useToast';

export const AutomatedResponse: React.FC = () => {
  const [rules, setRules] = useState<ResponseRule[]>([]);
  const [autoResponseEnabled, setAutoResponseEnabled] = useState(true);
  const [whitelistIps, setWhitelistIps] = useState<string[]>([]);
  const [newWhitelistIp, setNewWhitelistIp] = useState('');
  const { showToast } = useToast();

  useEffect(() => {
    const fetchRules = async () => {
      try {
        const response = await axios.get<ResponseRule[]>('http://127.0.0.1:8000/api/rules/');
        setRules(response.data);
      } catch (error) {
        console.error("Failed to fetch rules:", error);
        showToast('error', 'Could not load response rules.');
      }
    };
    fetchRules();
  }, [showToast]);

  const toggleRule = async (ruleId: string) => {
    const ruleToUpdate = rules.find(r => r.id === ruleId);
    if (!ruleToUpdate) return;
    try {
      const newStatus = !ruleToUpdate.is_active;
      await axios.patch(`http://127.0.0.1:8000/api/rules/${ruleId}/`, { is_active: newStatus });
      setRules(prev =>
        prev.map(rule =>
          rule.id === ruleId ? { ...rule, is_active: newStatus } : rule
        )
      );
      showToast('success', `Rule "${ruleToUpdate.name}" ${newStatus ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error(`Failed to toggle rule status:`, error);
      showToast('error', 'Could not update rule status.');
    }
  };

  const handleRollback = async (ruleId: string) => {
    const ruleToUpdate = rules.find(r => r.id === ruleId);
    if (!ruleToUpdate || ruleToUpdate.triggered_count === 0) return;
    try {
      await axios.patch(`http://127.0.0.1:8000/api/rules/${ruleId}/`, { triggered_count: 0 });
      setRules(prev =>
        prev.map(r =>
          r.id === ruleId ? { ...r, triggered_count: 0 } : r
        )
      );
      showToast('success', `Rolled back ${ruleToUpdate.triggered_count} actions for "${ruleToUpdate.name}"`);
    } catch (error) {
      console.error(`Failed to rollback actions:`, error);
      showToast('error', 'Could not rollback actions.');
    }
  };

  const addWhitelistIp = () => {
    // You would need to implement a backend endpoint for this
    if (newWhitelistIp && !whitelistIps.includes(newWhitelistIp)) {
      setWhitelistIps(prev => [...prev, newWhitelistIp]);
      setNewWhitelistIp('');
      showToast('success', `Added ${newWhitelistIp} to whitelist`);
    }
  };

  const removeWhitelistIp = (ip: string) => {
    // And an endpoint for this as well
    setWhitelistIps(prev => prev.filter(i => i !== ip));
    showToast('info', `Removed ${ip} from whitelist`);
  };

  const getActionBadge = (action: ResponseRule['action']) => {
    const styles: Record<string, string> = {
      'Block IP': 'bg-red-500/20 text-red-500 border border-red-500/30',
      'Isolate Device': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
      'Alert Admin': 'bg-amber-500/20 text-amber-500 border border-amber-500/30',
      'Quarantine': 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider shadow-sm ${styles[action]}`}>
        {action}
      </span>
    );
  };

  const columns = [
    {
      key: 'name' as keyof ResponseRule,
      header: 'Rule Name',
      sortable: true,
    },
    {
      key: 'condition' as keyof ResponseRule,
      header: 'Condition',
      render: (item: ResponseRule) => (
        <code className="text-xs bg-gray-700 px-2 py-1 rounded text-cyan-300">
          {item.condition}
        </code>
      ),
      sortable: false,
    },
    {
      key: 'action' as keyof ResponseRule,
      header: 'Action',
      render: (item: ResponseRule) => getActionBadge(item.action),
      sortable: true,
    },
    {
      key: 'is_active' as keyof ResponseRule,
      header: 'Status',
      render: (item: ResponseRule) => (
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={item.is_active}
            onChange={() => toggleRule(item.id)}
          />
          <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500 hover:shadow-[0_0_10px_rgba(6,182,212,0.3)] transition-all"></div>
          <span className={`ml-3 text-sm font-medium ${item.is_active ? 'text-cyan-400' : 'text-gray-500'}`}>
            {item.is_active ? 'Active' : 'Inactive'}
          </span>
        </label>
      ),
      sortable: true,
    },
    {
      key: 'triggered_count' as keyof ResponseRule,
      header: 'Triggered',
      render: (item: ResponseRule) => `${item.triggered_count} times`,
      sortable: true,
    },
    {
      key: 'created_at' as keyof ResponseRule,
      header: 'Created',
      render: (item: ResponseRule) => format(new Date(item.created_at), 'MMM dd, yyyy'),
      sortable: true,
    },
    {
      key: 'id' as keyof ResponseRule,
      header: 'Actions',
      render: (item: ResponseRule) => (
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleRollback(item.id)}
            className="p-1 text-blue-400 hover:text-blue-300 transition-colors"
            title="Rollback Actions"
            disabled={item.triggered_count === 0}
          >
            <RotateCcw className={`h-4 w-4 ${item.triggered_count === 0 ? 'opacity-50' : ''}`} />
          </button>
        </div>
      ),
      sortable: false,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-[24px] font-bold text-white tracking-tight flex items-center gap-3">Automated Response</h2>
          <p className="text-sm text-gray-400 mt-1 font-medium tracking-wide">Configure and manage automated security responses</p>
        </div>

        <div className="flex items-center space-x-4 bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 p-3 rounded-xl shadow-xl">
          <div className="flex items-center space-x-3 px-2">
            <span className={`font-semibold text-sm tracking-wide ${autoResponseEnabled ? 'text-emerald-400' : 'text-gray-400'}`}>
              Master Auto-Response
            </span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={autoResponseEnabled}
                onChange={() => {
                  setAutoResponseEnabled(!autoResponseEnabled);
                  showToast(
                    autoResponseEnabled ? 'warning' : 'success',
                    `Auto-response system ${autoResponseEnabled ? 'disabled' : 'enabled'}`
                  );
                }}
              />
              <div className="w-14 h-7 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-emerald-500 hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all drop-shadow-md"></div>
            </label>
          </div>
        </div>
      </div>

      {!autoResponseEnabled && (
        <div className="bg-amber-900/20 border border-amber-500/30 rounded-xl p-4 shadow-lg backdrop-blur-md">
          <div className="flex items-center">
            <Shield className="h-5 w-5 text-amber-500 mr-3" />
            <p className="text-amber-400/90 text-sm font-medium">
              Automated response system is disabled. Security incidents will require manual intervention.
            </p>
          </div>
        </div>
      )}

      <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white tracking-wide">Response Rules</h3>
          <button className="flex items-center space-x-2 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 shadow-[0_0_15px_rgba(8,145,178,0.4)] text-white rounded-lg transition-all font-semibold text-sm hover:-translate-y-0.5">
            <Plus className="h-4 w-4" />
            <span>Add Rule</span>
          </button>
        </div>

        <DataTable
          data={rules}
          columns={columns}
          searchable
          pageSize={10}
        />
      </div>

      <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-cyan-900/10 rounded-full blur-3xl pointer-events-none"></div>
        <h3 className="text-lg font-bold text-white mb-2 relative z-10">IP Whitelist</h3>
        <p className="text-sm text-gray-400 mb-6 font-medium relative z-10">Trusted IPs that bypass automated responses</p>

        <div className="flex items-center mb-6 max-w-md relative z-10 shadow-lg rounded-lg overflow-hidden border border-gray-700/50">
          <input
            type="text"
            placeholder="Enter IP address..."
            value={newWhitelistIp}
            onChange={(e) => setNewWhitelistIp(e.target.value)}
            className="flex-1 px-4 py-3 bg-gray-900/50 text-white placeholder-gray-500 font-mono text-sm focus:outline-none focus:bg-gray-900/80 transition-colors"
          />
          <button
            onClick={addWhitelistIp}
            className="px-6 py-3 bg-gray-800 hover:bg-cyan-600 text-cyan-400 hover:text-white border-l border-gray-700/50 transition-all font-semibold text-sm"
          >
            Add IP
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 relative z-10">
          {whitelistIps.map((ip, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-gray-800/80 border border-gray-700/50 shadow-inner px-4 py-3 rounded-lg group hover:border-cyan-500/30 transition-colors"
            >
              <span className="font-mono text-gray-300 text-sm group-hover:text-cyan-100 transition-colors">{ip}</span>
              <button
                onClick={() => removeWhitelistIp(ip)}
                className="p-1.5 rounded-full text-gray-500 hover:bg-red-500/20 hover:text-red-400 transition-all"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
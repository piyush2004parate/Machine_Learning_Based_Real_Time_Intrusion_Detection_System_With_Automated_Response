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
    const colors = {
      'Block IP': 'bg-red-500',
      'Isolate Device': 'bg-orange-500',
      'Alert Admin': 'bg-yellow-500',
      'Quarantine': 'bg-purple-500',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${colors[action]}`}>
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
        <button
          onClick={() => toggleRule(item.id)}
          className="flex items-center space-x-2 text-sm"
        >
          {item.is_active ? (
            <ToggleRight className="h-5 w-5 text-green-400" />
          ) : (
            <ToggleLeft className="h-5 w-5 text-gray-400" />
          )}
          <span className={item.is_active ? 'text-green-400' : 'text-gray-400'}>
            {item.is_active ? 'Active' : 'Inactive'}
          </span>
        </button>
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Automated Response</h2>
          <p className="text-gray-400">Configure and manage automated security responses</p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <span className="text-gray-300">Auto-Response System</span>
            <button
              onClick={() => {
                setAutoResponseEnabled(!autoResponseEnabled);
                showToast(
                  autoResponseEnabled ? 'warning' : 'success',
                  `Auto-response system ${autoResponseEnabled ? 'disabled' : 'enabled'}`
                );
              }}
              className="flex items-center"
            >
              {autoResponseEnabled ? (
                <ToggleRight className="h-6 w-6 text-green-400" />
              ) : (
                <ToggleLeft className="h-6 w-6 text-gray-400" />
              )}
            </button>
          </div>
        </div>
      </div>

      {!autoResponseEnabled && (
        <div className="bg-yellow-900 border border-yellow-600 rounded-lg p-4">
          <div className="flex items-center">
            <Shield className="h-5 w-5 text-yellow-400 mr-3" />
            <p className="text-yellow-300">
              Automated response system is disabled. Security incidents will require manual intervention.
            </p>
          </div>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Response Rules</h3>
          <button className="flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors">
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

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">IP Whitelist</h3>
        <p className="text-gray-400 mb-4">Trusted IPs that bypass automated responses</p>

        <div className="flex items-center space-x-3 mb-4">
          <input
            type="text"
            placeholder="Enter IP address..."
            value={newWhitelistIp}
            onChange={(e) => setNewWhitelistIp(e.target.value)}
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <button
            onClick={addWhitelistIp}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            Add IP
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {whitelistIps.map((ip, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded-lg"
            >
              <span className="font-mono text-gray-300">{ip}</span>
              <button
                onClick={() => removeWhitelistIp(ip)}
                className="text-red-400 hover:text-red-300 transition-colors"
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
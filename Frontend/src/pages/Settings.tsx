import React, { useState } from 'react';
import { Bell, Mail, MessageSquare, Slack, Save, User, Shield, Gauge } from 'lucide-react';
import { useToast } from '../hooks/useToast';

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    // Thresholds
    anomalyThreshold: 75,
    threatThreshold: 85,
    autoBlockThreshold: 95,
    
    // Notifications
    emailNotifications: true,
    slackNotifications: false,
    telegramNotifications: false,
    emailAddress: 'admin@company.com',
    slackWebhook: '',
    telegramBotToken: '',
    
    // System
    autoRefreshInterval: 5,
    logRetentionDays: 30,
    maxConcurrentScans: 10,
    
    // User settings
    darkMode: true,
    showTooltips: true,
    compactMode: false,
  });

  const { showToast } = useToast();

  const handleSave = () => {
    // In a real app, this would save to backend
    showToast('success', 'Settings saved successfully');
  };

  const updateSetting = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[24px] font-bold text-white tracking-tight flex items-center gap-3">Settings</h2>
          <p className="text-sm text-gray-400 mt-1 font-medium tracking-wide">Configure system preferences and security thresholds</p>
        </div>
        
        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-all font-semibold text-sm shadow-[0_0_15px_rgba(8,145,178,0.4)] hover:-translate-y-0.5"
        >
          <Save className="h-4 w-4" />
          <span>Save Configuration</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Thresholds */}
        <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 p-6 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-900/10 rounded-full blur-2xl group-hover:bg-cyan-900/20 transition-colors pointer-events-none"></div>
          <div className="flex items-center mb-6 relative z-10">
            <div className="p-2 bg-gray-800 rounded-lg mr-3 shadow-inner border border-gray-700">
              <Gauge className="h-5 w-5 text-cyan-400" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">Detection Thresholds</h3>
          </div>

          <div className="space-y-8 relative z-10">
            <div className="group/slider">
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm font-semibold text-gray-300">Anomaly Detection</label>
                <span className="text-xs font-bold text-cyan-400 bg-cyan-900/30 px-2.5 py-1 rounded-full border border-cyan-500/30">{settings.anomalyThreshold}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="100"
                value={settings.anomalyThreshold}
                onChange={(e) => updateSetting('anomalyThreshold', parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 shadow-inner"
              />
            </div>

            <div className="group/slider">
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm font-semibold text-gray-300">Threat Classification</label>
                <span className="text-xs font-bold text-amber-400 bg-amber-900/30 px-2.5 py-1 rounded-full border border-amber-500/30">{settings.threatThreshold}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="100"
                value={settings.threatThreshold}
                onChange={(e) => updateSetting('threatThreshold', parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-amber-500 shadow-inner"
              />
            </div>

            <div className="group/slider">
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm font-semibold text-gray-300">Auto-Block Confidence</label>
                <span className="text-xs font-bold text-red-500 bg-red-900/30 px-2.5 py-1 rounded-full border border-red-500/30">{settings.autoBlockThreshold}%</span>
              </div>
              <input
                type="range"
                min="80"
                max="100"
                value={settings.autoBlockThreshold}
                onChange={(e) => updateSetting('autoBlockThreshold', parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-red-500 shadow-inner"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 p-6 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-900/10 rounded-full blur-2xl group-hover:bg-purple-900/20 transition-colors pointer-events-none"></div>
          <div className="flex items-center mb-6 relative z-10">
            <div className="p-2 bg-gray-800 rounded-lg mr-3 shadow-inner border border-gray-700">
              <Bell className="h-5 w-5 text-purple-400" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">Notifications</h3>
          </div>

          <div className="space-y-5 relative z-10">
            <div className={`p-4 rounded-xl border transition-all ${settings.emailNotifications ? 'bg-gray-800/80 border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.1)]' : 'bg-gray-800/40 border-gray-700/50'}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Mail className={`h-4 w-4 mr-3 ${settings.emailNotifications ? 'text-cyan-400' : 'text-gray-500'}`} />
                  <span className={`text-sm font-semibold ${settings.emailNotifications ? 'text-white' : 'text-gray-400'}`}>Email Alerts</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.emailNotifications}
                    onChange={(e) => updateSetting('emailNotifications', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500 peer-checked:shadow-[0_0_10px_rgba(6,182,212,0.4)] transition-all"></div>
                </label>
              </div>

              {settings.emailNotifications && (
                <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <input
                    type="email"
                    placeholder="admin@company.com"
                    value={settings.emailAddress}
                    onChange={(e) => updateSetting('emailAddress', e.target.value)}
                    className="w-full px-4 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-white font-mono text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all shadow-inner"
                  />
                </div>
              )}
            </div>

            <div className={`p-4 rounded-xl border transition-all flex items-center justify-between ${settings.slackNotifications ? 'bg-gray-800/80 border-emerald-500/30' : 'bg-gray-800/40 border-gray-700/50'}`}>
              <div className="flex items-center">
                <Slack className={`h-4 w-4 mr-3 ${settings.slackNotifications ? 'text-emerald-400' : 'text-gray-500'}`} />
                <span className={`text-sm font-semibold ${settings.slackNotifications ? 'text-white' : 'text-gray-400'}`}>Slack Webhook</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.slackNotifications}
                  onChange={(e) => updateSetting('slackNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500 peer-checked:shadow-[0_0_10px_rgba(16,185,129,0.4)] transition-all"></div>
              </label>
            </div>

            <div className={`p-4 rounded-xl border transition-all flex items-center justify-between ${settings.telegramNotifications ? 'bg-gray-800/80 border-blue-500/30' : 'bg-gray-800/40 border-gray-700/50'}`}>
              <div className="flex items-center">
                <MessageSquare className={`h-4 w-4 mr-3 ${settings.telegramNotifications ? 'text-blue-400' : 'text-gray-500'}`} />
                <span className={`text-sm font-semibold ${settings.telegramNotifications ? 'text-white' : 'text-gray-400'}`}>Telegram Bot</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.telegramNotifications}
                  onChange={(e) => updateSetting('telegramNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500 peer-checked:shadow-[0_0_10px_rgba(59,130,246,0.4)] transition-all"></div>
              </label>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 p-6 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-900/10 rounded-full blur-2xl group-hover:bg-emerald-900/20 transition-colors pointer-events-none"></div>
          <div className="flex items-center mb-6 relative z-10">
            <div className="p-2 bg-gray-800 rounded-lg mr-3 shadow-inner border border-gray-700">
              <Shield className="h-5 w-5 text-emerald-400" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">System Settings</h3>
          </div>

          <div className="space-y-5 relative z-10">
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Auto-refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={settings.autoRefreshInterval}
                onChange={(e) => updateSetting('autoRefreshInterval', parseInt(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all shadow-inner"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Log Retention (days)
              </label>
              <input
                type="number"
                min="1"
                max="365"
                value={settings.logRetentionDays}
                onChange={(e) => updateSetting('logRetentionDays', parseInt(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all shadow-inner"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-2">
                Max Concurrent Scans
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={settings.maxConcurrentScans}
                onChange={(e) => updateSetting('maxConcurrentScans', parseInt(e.target.value))}
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all shadow-inner"
              />
            </div>
          </div>
        </div>

        {/* User Preferences */}
        <div className="bg-gray-900/60 backdrop-blur-xl border border-gray-700/50 p-6 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-900/10 rounded-full blur-2xl group-hover:bg-amber-900/20 transition-colors pointer-events-none"></div>
          <div className="flex items-center mb-6 relative z-10">
            <div className="p-2 bg-gray-800 rounded-lg mr-3 shadow-inner border border-gray-700">
              <User className="h-5 w-5 text-amber-400" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">User Preferences</h3>
          </div>

          <div className="space-y-4 relative z-10">
            <div className="flex items-center justify-between p-4 bg-gray-800/40 rounded-xl border border-gray-700/50">
              <span className="text-sm font-semibold text-gray-300">Show ML Tooltips</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.showTooltips}
                  onChange={(e) => updateSetting('showTooltips', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500 peer-checked:shadow-[0_0_10px_rgba(245,158,11,0.4)] transition-all"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-800/40 rounded-xl border border-gray-700/50">
              <span className="text-sm font-semibold text-gray-300">Compact Dashboard View</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.compactMode}
                  onChange={(e) => updateSetting('compactMode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500 peer-checked:shadow-[0_0_10px_rgba(245,158,11,0.4)] transition-all"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
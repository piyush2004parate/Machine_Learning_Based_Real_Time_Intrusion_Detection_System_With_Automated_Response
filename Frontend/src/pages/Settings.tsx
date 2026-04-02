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
      <div>
        <h2 className="text-2xl font-bold text-white">Settings</h2>
        <p className="text-gray-400">Configure system preferences and security thresholds</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Thresholds */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex items-center mb-4">
            <Gauge className="h-5 w-5 text-cyan-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">Detection Thresholds</h3>
          </div>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Anomaly Detection Sensitivity: {settings.anomalyThreshold}%
              </label>
              <input
                type="range"
                min="50"
                max="100"
                value={settings.anomalyThreshold}
                onChange={(e) => updateSetting('anomalyThreshold', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Less Sensitive</span>
                <span>More Sensitive</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Threat Classification Threshold: {settings.threatThreshold}%
              </label>
              <input
                type="range"
                min="60"
                max="100"
                value={settings.threatThreshold}
                onChange={(e) => updateSetting('threatThreshold', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Auto-Block Threshold: {settings.autoBlockThreshold}%
              </label>
              <input
                type="range"
                min="80"
                max="100"
                value={settings.autoBlockThreshold}
                onChange={(e) => updateSetting('autoBlockThreshold', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex items-center mb-4">
            <Bell className="h-5 w-5 text-cyan-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">Notifications</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Mail className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-gray-300">Email Notifications</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.emailNotifications}
                  onChange={(e) => updateSetting('emailNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
              </label>
            </div>

            {settings.emailNotifications && (
              <div className="ml-6">
                <input
                  type="email"
                  placeholder="Email address"
                  value={settings.emailAddress}
                  onChange={(e) => updateSetting('emailAddress', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Slack className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-gray-300">Slack Notifications</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.slackNotifications}
                  onChange={(e) => updateSetting('slackNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <MessageSquare className="h-4 w-4 text-gray-400 mr-2" />
                <span className="text-gray-300">Telegram Notifications</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.telegramNotifications}
                  onChange={(e) => updateSetting('telegramNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-cyan-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">System Settings</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Auto-refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={settings.autoRefreshInterval}
                onChange={(e) => updateSetting('autoRefreshInterval', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Log Retention (days)
              </label>
              <input
                type="number"
                min="1"
                max="365"
                value={settings.logRetentionDays}
                onChange={(e) => updateSetting('logRetentionDays', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Max Concurrent Scans
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={settings.maxConcurrentScans}
                onChange={(e) => updateSetting('maxConcurrentScans', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
          </div>
        </div>

        {/* User Preferences */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
          <div className="flex items-center mb-4">
            <User className="h-5 w-5 text-cyan-400 mr-2" />
            <h3 className="text-lg font-semibold text-white">User Preferences</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Show Tooltips</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.showTooltips}
                  onChange={(e) => updateSetting('showTooltips', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-300">Compact Mode</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.compactMode}
                  onChange={(e) => updateSetting('compactMode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-cyan-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
        >
          <Save className="h-4 w-4" />
          <span>Save Settings</span>
        </button>
      </div>
    </div>
  );
};
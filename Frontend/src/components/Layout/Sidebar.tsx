import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Shield, 
  BarChart3, 
  Activity, 
  AlertTriangle, 
  Settings, 
  FileText,
  Zap
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: BarChart3 },
  { name: 'Live Traffic', href: '/traffic', icon: Activity },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Auto Response', href: '/response', icon: Zap },
  { name: 'Logs & Reports', href: '/logs', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <div className="bg-gray-900 text-white w-64 min-h-screen flex flex-col border-r border-gray-700">
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-cyan-400" />
          <div>
            <h1 className="text-xl font-bold">SecureWatch</h1>
            <p className="text-xs text-gray-400">ML-IDS Dashboard</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-cyan-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          <div className="flex justify-between items-center mb-1">
            <span>System Status</span>
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          </div>
          <p>All systems operational</p>
        </div>
      </div>
    </div>
  );
};
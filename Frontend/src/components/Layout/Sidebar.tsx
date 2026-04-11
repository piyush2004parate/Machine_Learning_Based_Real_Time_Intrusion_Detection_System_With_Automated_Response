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
    <div className="bg-gray-900 text-white w-64 min-h-screen flex flex-col border-r border-gray-800 z-10 shadow-2xl shadow-black/50">
      <div className="p-6 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
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
              `flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300 group ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-600/90 to-blue-600/90 text-white shadow-lg shadow-cyan-900/20 border border-cyan-500/30'
                  : 'text-gray-400 hover:bg-gray-800/80 hover:text-cyan-400 hover:scale-[1.02]'
              }`
            }
          >
            <item.icon className="mr-3 h-5 w-5 flex-shrink-0 opacity-80 group-hover:opacity-100 transition-opacity" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800 bg-gray-900/50">
        <div className="bg-gray-800/50 rounded-xl p-3 border border-gray-700/50">
          <div className="flex justify-between items-center mb-1 text-xs text-gray-400 font-medium">
            <span>System Status</span>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></div>
            </div>
          </div>
          <p className="text-xs text-emerald-400/90 font-semibold tracking-wide">All systems operational</p>
        </div>
      </div>
    </div>
  );
};
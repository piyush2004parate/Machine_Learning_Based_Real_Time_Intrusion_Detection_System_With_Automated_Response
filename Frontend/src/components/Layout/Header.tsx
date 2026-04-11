import React from 'react';
import { Bell, User, Moon, Sun, Search } from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({ darkMode, toggleDarkMode }) => {
  return (
    <header className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 sticky top-0 z-50 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white tracking-tight">
            Network Security Dashboard
          </h2>
          <p className="text-sm text-gray-400 font-medium tracking-wide">
            Real-time ML threat detection
          </p>
        </div>

        {/* Search Bar */}
        <div className="hidden md:flex flex-1 max-w-md mx-6">
          <div className="relative w-full group">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400 group-focus-within:text-cyan-400 transition-colors" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-700 rounded-lg leading-5 bg-gray-800/50 text-gray-300 placeholder-gray-500 focus:outline-none focus:bg-gray-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 sm:text-sm transition-all duration-300"
              placeholder="Search IPs, protocols, or events..."
            />
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={toggleDarkMode}
            className="p-2 text-gray-400 hover:text-cyan-400 hover:bg-gray-800 rounded-lg transition-all duration-300"
          >
            {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          <div className="relative">
            <button className="p-2 text-gray-400 hover:text-cyan-400 hover:bg-gray-800 rounded-lg transition-all duration-300">
              <Bell className="h-5 w-5" />
            </button>
            <div className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full ring-2 ring-gray-900 animate-pulse"></div>
          </div>

          <div className="flex items-center space-x-3 pl-4 border-l border-gray-700/50">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-white">Admin User</p>
              <p className="text-xs text-cyan-400/80 font-medium">Security Administrator</p>
            </div>
            <div className="w-9 h-9 bg-gradient-to-tr from-cyan-600 to-blue-500 rounded-full flex items-center justify-center shadow-lg shadow-cyan-500/20 border border-cyan-400/30 cursor-pointer hover:shadow-cyan-500/40 transition-shadow">
              <User className="h-4 w-4 text-white" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
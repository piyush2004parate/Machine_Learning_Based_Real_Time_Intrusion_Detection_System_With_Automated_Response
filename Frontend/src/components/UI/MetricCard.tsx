import React from 'react';
import { DivideIcon as LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'cyan' | 'green' | 'red' | 'yellow' | 'blue';
}

export const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  color = 'cyan' 
}) => {
  const colorClasses = {
    cyan: 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20 group-hover:bg-cyan-500/20 group-hover:ring-cyan-500/30',
    green: 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20 group-hover:bg-emerald-500/20 group-hover:ring-emerald-500/30',
    red: 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20 group-hover:bg-red-500/20 group-hover:ring-red-500/30',
    yellow: 'bg-yellow-500/10 text-yellow-400 ring-1 ring-yellow-500/20 group-hover:bg-yellow-500/20 group-hover:ring-yellow-500/30',
    blue: 'bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20 group-hover:bg-blue-500/20 group-hover:ring-blue-500/30',
  };

  return (
    <div className="bg-gray-900/60 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50 shadow-2xl relative overflow-hidden group hover:border-gray-600/50 transition-all duration-300 transform hover:-translate-y-1">
      {/* Decorative gradient blob */}
      <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-20 ${colorClasses[color].split(' ')[0]}`}></div>
      
      <div className="flex items-center justify-between relative z-10">
        <div className="flex-1">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
            {title}
          </p>
          <p className="mt-2 text-4xl font-bold text-white tracking-tight drop-shadow-sm">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend && (
            <div className="mt-4 flex items-center bg-gray-800/50 w-fit px-2.5 py-1 rounded-full border border-gray-700/50">
              <span className={`text-xs font-bold flex items-center ${trend.isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {trend.isPositive ? '↑ +' : '↓ '}{trend.value}%
              </span>
              <span className="text-gray-400/80 text-[10px] ml-2 uppercase font-semibold">from last hour</span>
            </div>
          )}
        </div>
        <div className={`p-4 rounded-xl transition-all duration-300 shadow-inner ${colorClasses[color]}`}>
          <Icon className="h-7 w-7 drop-shadow-md" strokeWidth={2.5} />
        </div>
      </div>
    </div>
  );
};
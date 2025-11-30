import React from 'react';
import { Phone, Settings, Users, FileText, CreditCard, History, PhoneForwarded } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Sidebar({ activeTab, setActiveTab, userRole, userProfile }) {
  const menuItems = [
    { id: 'calls', label: 'Make Call', icon: Phone, roles: ['admin', 'user'] },
    { id: 'spoofing', label: 'SIP Spoofing', icon: PhoneForwarded, roles: ['admin', 'user'], requireSpoofing: true },
    { id: 'history', label: 'Call History', icon: History, roles: ['admin', 'user'] },
    { id: 'users', label: 'User Management', icon: Users, roles: ['admin'] },
    { id: 'payments', label: 'Top Up Balance', icon: CreditCard, roles: ['admin', 'user'] },
    { id: 'settings', label: 'Settings', icon: Settings, roles: ['admin', 'user'] },
  ];

  const filteredMenu = menuItems.filter(item => {
    // Check role
    if (!item.roles.includes(userRole)) return false;
    
    // Check spoofing permission
    if (item.requireSpoofing) {
      // Admin always can use spoofing
      if (userRole === 'admin') return true;
      // Regular user needs permission
      return userProfile?.can_use_spoofing === true;
    }
    
    return true;
  });

  return (
    <aside className="sidebar w-64 h-[calc(100vh-4rem)] p-4" data-testid="sidebar">
      <nav className="space-y-2">
        {filteredMenu.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              data-testid={`menu-${item.id}`}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all',
                activeTab === item.id
                  ? 'bg-[#00FF7F]/10 text-[#00FF7F] neon-border'
                  : 'text-gray-400 hover:bg-[#00FF7F]/5 hover:text-[#00FF7F]'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
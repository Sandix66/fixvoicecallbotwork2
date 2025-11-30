import React from 'react';
import { Button } from './ui/button';
import { LogOut, Wallet, User } from 'lucide-react';

export default function StatusBar({ userProfile, onLogout }) {
  return (
    <div className="status-bar h-16 px-6 flex items-center justify-between" data-testid="status-bar">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-[#00FF7F] neon-glow">CallBot Research</h1>
        <span className="text-xs text-gray-400">v1.0.0</span>
      </div>

      <div className="flex items-center gap-6">
        {/* Balance */}
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00FF7F]/10" data-testid="balance-display">
          <Wallet className="w-4 h-4 text-[#00FF7F]" />
          <span className="text-sm font-semibold text-[#00FF7F]">
            ${userProfile?.balance?.toFixed(2) || '0.00'}
          </span>
        </div>

        {/* User Info */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-white" data-testid="username">{userProfile?.username}</p>
            <p className="text-xs text-gray-400">{userProfile?.role}</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-[#00FF7F]/20 flex items-center justify-center">
            <User className="w-5 h-5 text-[#00FF7F]" />
          </div>
        </div>

        {/* Logout */}
        <Button
          onClick={onLogout}
          variant="outline"
          size="sm"
          className="btn-secondary"
          data-testid="logout-button"
        >
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
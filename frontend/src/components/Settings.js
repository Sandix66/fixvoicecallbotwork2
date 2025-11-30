import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import { Lock, User, Mail, Shield } from 'lucide-react';

export default function Settings() {
  const { userProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await api.post('/users/change-password', {
        old_password: passwordData.oldPassword,
        new_password: passwordData.newPassword
      });
      
      toast.success('Password changed successfully');
      setPasswordData({
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error('Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Settings</h2>
        <p className="text-gray-400">Manage your account settings and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Information */}
        <Card className="glass-effect border-[#00FF7F]/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <User className="w-5 h-5 text-[#00FF7F]" />
              Profile Information
            </CardTitle>
            <CardDescription className="text-gray-400">
              Your account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-gray-300 flex items-center gap-2">
                <User className="w-4 h-4" />
                Username
              </Label>
              <Input
                value={userProfile?.username || ''}
                disabled
                className="input-field"
                data-testid="username-display"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-300 flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Email
              </Label>
              <Input
                value={userProfile?.email || ''}
                disabled
                className="input-field"
                data-testid="email-display"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-300 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Role
              </Label>
              <Input
                value={userProfile?.role || ''}
                disabled
                className="input-field"
                data-testid="role-display"
              />
            </div>

            <p className="text-xs text-gray-500 mt-4">
              Contact admin to update your username or email
            </p>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card className="glass-effect border-[#00FF7F]/20">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Lock className="w-5 h-5 text-[#00FF7F]" />
              Change Password
            </CardTitle>
            <CardDescription className="text-gray-400">
              Update your password to keep your account secure
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="old-password" className="text-gray-300">
                  Current Password
                </Label>
                <Input
                  id="old-password"
                  type="password"
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, oldPassword: e.target.value }))}
                  required
                  className="input-field"
                  data-testid="old-password-input"
                  placeholder="Enter current password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-gray-300">
                  New Password
                </Label>
                <Input
                  id="new-password"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                  required
                  className="input-field"
                  data-testid="new-password-input"
                  placeholder="Enter new password"
                  minLength={6}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password" className="text-gray-300">
                  Confirm New Password
                </Label>
                <Input
                  id="confirm-password"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  required
                  className="input-field"
                  data-testid="confirm-password-input"
                  placeholder="Confirm new password"
                  minLength={6}
                />
              </div>

              <Button
                type="submit"
                className="w-full btn-primary"
                disabled={loading}
                data-testid="change-password-button"
              >
                {loading ? 'Updating...' : 'Change Password'}
              </Button>

              <p className="text-xs text-gray-500">
                Password must be at least 6 characters long
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

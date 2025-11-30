import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { UserPlus, Trash2, Wallet, Edit } from 'lucide-react';

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddUser, setShowAddUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    username: '',
    role: 'user'
  });
  const [editUser, setEditUser] = useState({
    email: '',
    password: '',
    username: ''
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users/all');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', newUser);
      toast.success('User created successfully');
      setShowAddUser(false);
      setNewUser({ email: '', password: '', username: '', role: 'user' });
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error('Failed to create user');
    }
  };

  const handleDeleteUser = async (uid) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    
    try {
      await api.delete(`/users/${uid}`);
      toast.success('User deleted successfully');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Failed to delete user');
    }
  };

  const handleUpdateBalance = async (uid, currentBalance) => {
    const newBalance = prompt(`Enter new balance for user (current: $${currentBalance}):`);
    if (!newBalance) return;

    try {
      await api.put(`/users/${uid}/balance`, { amount: parseFloat(newBalance) });
      toast.success('Balance updated successfully');
      fetchUsers();
    } catch (error) {
      console.error('Error updating balance:', error);
      toast.error('Failed to update balance');
    }
  };

  const handleOpenEditUser = (user) => {
    setEditingUser(user);
    setEditUser({
      email: user.email,
      username: user.username,
      password: ''
    });
    setShowEditUser(true);
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        username: editUser.username,
        email: editUser.email
      };
      
      // Only send password if it's been changed
      if (editUser.password) {
        updateData.password = editUser.password;
      }

      await api.put(`/users/${editingUser.uid}`, updateData);
      toast.success('User updated successfully');
      setShowEditUser(false);
      setEditingUser(null);
      setEditUser({ email: '', password: '', username: '' });
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error('Failed to update user');
    }
  };

  if (loading) {
    return <div className="text-center text-[#00FF7F] terminal-text">Loading users...</div>;
  }

  return (
    <div className="space-y-6" data-testid="user-management">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">User Management</h2>
          <p className="text-gray-400">Manage users and their balances</p>
        </div>

        <Dialog open={showAddUser} onOpenChange={setShowAddUser}>
          <DialogTrigger asChild>
            <Button className="btn-primary" data-testid="add-user-button">
              <UserPlus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </DialogTrigger>
          <DialogContent className="glass-effect border-[#00FF7F]/20">
            <DialogHeader>
              <DialogTitle className="text-white">Create New User</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddUser} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new-username" className="text-gray-300">Username</Label>
                <Input
                  id="new-username"
                  value={newUser.username}
                  onChange={(e) => setNewUser(prev => ({ ...prev, username: e.target.value }))}
                  required
                  className="input-field"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-email" className="text-gray-300">Email</Label>
                <Input
                  id="new-email"
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                  required
                  className="input-field"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-gray-300">Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser(prev => ({ ...prev, password: e.target.value }))}
                  required
                  className="input-field"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-role" className="text-gray-300">Role</Label>
                <Select 
                  value={newUser.role} 
                  onValueChange={(value) => setNewUser(prev => ({ ...prev, role: value }))}
                >
                  <SelectTrigger className="input-field">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">User</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" className="w-full btn-primary">
                Create User
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="glass-effect rounded-xl p-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#00FF7F]/20">
                <th className="text-left py-3 px-4 text-sm font-semibold text-[#00FF7F]">Username</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-[#00FF7F]">Email</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-[#00FF7F]">Role</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-[#00FF7F]">Balance</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-[#00FF7F]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.uid} className="border-b border-[#00FF7F]/10 hover:bg-[#00FF7F]/5">
                  <td className="py-3 px-4 text-white">{user.username}</td>
                  <td className="py-3 px-4 text-gray-400">{user.email}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      user.role === 'admin' ? 'bg-[#00FF7F]/20 text-[#00FF7F]' : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-white font-semibold">${user.balance?.toFixed(2)}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="btn-secondary"
                        onClick={() => handleOpenEditUser(user)}
                        data-testid={`edit-user-${user.uid}`}
                      >
                        <Edit className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="btn-secondary"
                        onClick={() => handleUpdateBalance(user.uid, user.balance)}
                      >
                        <Wallet className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="bg-red-500/20 hover:bg-red-500/30 text-red-400"
                        onClick={() => handleDeleteUser(user.uid)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit User Dialog */}
      <Dialog open={showEditUser} onOpenChange={setShowEditUser}>
        <DialogContent className="glass-effect border-[#00FF7F]/20">
          <DialogHeader>
            <DialogTitle className="text-white">Edit User</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditUser} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-username" className="text-gray-300">Username</Label>
              <Input
                id="edit-username"
                value={editUser.username}
                onChange={(e) => setEditUser(prev => ({ ...prev, username: e.target.value }))}
                required
                className="input-field"
                data-testid="edit-username-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-email" className="text-gray-300">Email</Label>
              <Input
                id="edit-email"
                type="email"
                value={editUser.email}
                onChange={(e) => setEditUser(prev => ({ ...prev, email: e.target.value }))}
                required
                className="input-field"
                data-testid="edit-email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-password" className="text-gray-300">New Password</Label>
              <Input
                id="edit-password"
                type="password"
                value={editUser.password}
                onChange={(e) => setEditUser(prev => ({ ...prev, password: e.target.value }))}
                placeholder="Leave empty to keep current password"
                className="input-field"
                data-testid="edit-password-input"
              />
              <p className="text-xs text-gray-500">Leave empty if you don't want to change password</p>
            </div>

            <Button type="submit" className="w-full btn-primary" data-testid="save-user-button">
              Save Changes
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
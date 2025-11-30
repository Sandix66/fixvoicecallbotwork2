import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import StatusBar from '../components/StatusBar';
import CallManagement from '../components/CallManagement';
import Spoofing from '../components/Spoofing';
import CallHistory from './CallHistory';
import UserManagement from '../components/UserManagement';
import Settings from '../components/Settings';
import wsService from '../services/websocket';

export default function Dashboard() {
  const { currentUser, userProfile, signOut, getToken } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('calls');
  const [callEvents, setCallEvents] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = getToken();
    if (!token || !currentUser) {
      navigate('/login');
      return;
    }

    // Connect WebSocket only when userProfile is available
    if (userProfile && !wsConnected) {
      try {
        wsService.connect(userProfile.uid);
        setWsConnected(true);

        // Listen for call events
        const handleCallEvent = (data) => {
          console.log('Call event received:', data);
          setCallEvents(prev => [data, ...prev]);
        };

        wsService.on('call_event', handleCallEvent);

        return () => {
          wsService.off('call_event', handleCallEvent);
          wsService.disconnect();
          setWsConnected(false);
        };
      } catch (error) {
        console.error('WebSocket connection error:', error);
      }
    }
  }, [currentUser, userProfile, navigate, getToken, wsConnected]);

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (!userProfile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-[#00FF7F] terminal-text">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App min-h-screen flex flex-col" data-testid="dashboard">
      <StatusBar userProfile={userProfile} onLogout={handleLogout} />
      
      <div className="flex flex-1">
        <Sidebar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab}
          userRole={userProfile.role}
        />
        
        <main className="flex-1 p-6 overflow-auto">
          {activeTab === 'calls' && <CallManagement />}
          {activeTab === 'spoofing' && <Spoofing />}
          {activeTab === 'history' && <CallHistory />}
          {activeTab === 'users' && userProfile.role === 'admin' && <UserManagement />}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}
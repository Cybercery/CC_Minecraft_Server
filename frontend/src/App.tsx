import React, { useEffect, useState } from 'react';
import { onAuthStateChanged, auth, type User } from './firebase';
import { apiRequest } from './api';
import { AuthModal } from './components/AuthModal';
import { Sidebar } from './components/Sidebar';
import { ServerControl } from './components/ServerControl';
import { MonitoringDashboard } from './components/MonitoringDashboard';
import { BackupsManagement } from './components/BackupsManagement';
import { MinecraftLinking } from './components/MinecraftLinking';
import { UserManagement } from './components/UserManagement';
import { AuditLogsViewer } from './components/AuditLogsViewer';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<{ role: string; email: string; uid: string } | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        try {
          const profileData = await apiRequest('/auth/me');
          setProfile(profileData);
        } catch (e) {
          console.error('Failed to load profile:', e);
          // Fallback profile if backend auth setup has delay
          setProfile({
            uid: currentUser.uid,
            email: currentUser.email || 'user@example.com',
            role: 'User'
          });
        }
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        color: 'var(--text-muted)'
      }}>
        Loading Minecraft Cloud Dashboard...
      </div>
    );
  }

  if (!user || !profile) {
    return <AuthModal />;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        userRole={profile.role} 
        userEmail={profile.email} 
      />

      <main style={{ flex: 1, padding: '36px 48px', overflowY: 'auto' }}>
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
                Welcome back, {profile.email.split('@')[0]}
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '6px' }}>
                Minecraft Server Management, Cloud Storage, and Telemetry Portal
              </p>
            </div>

            <ServerControl userRole={profile.role} />
          </div>
        )}

        {activeTab === 'server' && <ServerControl userRole={profile.role} />}
        {activeTab === 'monitoring' && <MonitoringDashboard />}
        {activeTab === 'backups' && <BackupsManagement userRole={profile.role} />}
        {activeTab === 'minecraft' && <MinecraftLinking />}
        {activeTab === 'users' && <UserManagement currentUid={profile.uid} />}
        {activeTab === 'audit' && <AuditLogsViewer />}
      </main>
    </div>
  );
};

export default App;

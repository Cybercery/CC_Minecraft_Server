import React from 'react';
import { 
  Server, 
  Activity, 
  Archive, 
  Users, 
  Gamepad2, 
  FileText, 
  LogOut, 
  Cpu 
} from 'lucide-react';
import { signOut, auth } from '../firebase';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  userRole: string;
  userEmail: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeTab, 
  setActiveTab, 
  userRole, 
  userEmail 
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity, minRole: 'User' },
    { id: 'server', label: 'Server Control', icon: Server, minRole: 'Operator' },
    { id: 'monitoring', label: 'Live Metrics', icon: Cpu, minRole: 'User' },
    { id: 'backups', label: 'Backups & Storage', icon: Archive, minRole: 'Operator' },
    { id: 'minecraft', label: 'Minecraft Link', icon: Gamepad2, minRole: 'User' },
    { id: 'users', label: 'IAM & RBAC', icon: Users, minRole: 'Administrator' },
    { id: 'audit', label: 'Audit Logs', icon: FileText, minRole: 'Administrator' },
  ];

  const roleWeights: Record<string, number> = {
    'User': 1,
    'Operator': 2,
    'Administrator': 3,
  };

  const currentWeight = roleWeights[userRole] || 1;

  return (
    <aside style={{
      width: '260px',
      background: 'rgba(10, 13, 20, 0.85)',
      backdropFilter: 'blur(20px)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      height: '100vh',
      position: 'sticky',
      top: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 24px 8px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1 0%, #10b981 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          color: 'white',
          fontSize: '1.1rem'
        }}>
          M
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.3px' }}>Cloud Panel</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Paper 1.20.4</div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
        {navItems.map(item => {
          const itemWeight = roleWeights[item.minRole] || 1;
          if (currentWeight < itemWeight) return null;

          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 14px',
                borderRadius: '10px',
                border: 'none',
                background: isActive 
                  ? 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(99,102,241,0.08) 100%)' 
                  : 'transparent',
                color: isActive ? '#a5b4fc' : 'var(--text-muted)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={18} color={isActive ? '#818cf8' : 'currentColor'} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div style={{
        padding: '16px',
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: '12px',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        <div style={{ overflow: 'hidden' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
            {userEmail}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <span className={`badge ${userRole === 'Administrator' ? 'badge-danger' : userRole === 'Operator' ? 'badge-warning' : 'badge-success'}`}>
              {userRole}
            </span>
          </div>
        </div>

        <button 
          onClick={() => signOut(auth)}
          className="btn btn-secondary"
          style={{ width: '100%', padding: '8px 12px', fontSize: '0.8rem' }}
        >
          <LogOut size={14} />
          Sign Out
        </button>
      </div>
    </aside>
  );
};

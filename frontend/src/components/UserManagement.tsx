import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { Users, Shield, UserCheck, AlertCircle } from 'lucide-react';

export const UserManagement: React.FC<{ currentUid: string }> = ({ currentUid }) => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await apiRequest('/users');
      setUsers(data || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (targetUid: string, newRole: string) => {
    try {
      setLoading(true);
      setMessage(null);
      await apiRequest(`/users/${targetUid}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole })
      });
      setMessage(`Role successfully updated to ${newRole}.`);
      await fetchUsers();
    } catch (e: any) {
      setMessage(`Failed to update role: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>IAM & Access Management</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Role-Based Access Control assignments (Administrator, Operator, User)
        </p>
      </div>

      {message && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid var(--border-accent)',
          borderRadius: '10px',
          fontSize: '0.85rem'
        }}>
          {message}
        </div>
      )}

      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <Users size={20} color="#818cf8" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>System Users & Roles</h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                <th style={{ padding: '12px 14px' }}>EMAIL</th>
                <th style={{ padding: '12px 14px' }}>UID</th>
                <th style={{ padding: '12px 14px' }}>CURRENT ROLE</th>
                <th style={{ padding: '12px 14px' }}>LAST LOGIN</th>
                <th style={{ padding: '12px 14px', textAlign: 'right' }}>ASSIGN ROLE</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.uid} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: 'white' }}>
                    {u.email}
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {u.uid.substring(0, 14)}...
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className={`badge ${u.role === 'Administrator' ? 'badge-danger' : u.role === 'Operator' ? 'badge-warning' : 'badge-success'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                  </td>
                  <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                    <select
                      value={u.role}
                      disabled={loading || u.uid === currentUid}
                      onChange={e => handleRoleChange(u.uid, e.target.value)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        background: 'rgba(0,0,0,0.5)',
                        color: 'white',
                        border: '1px solid var(--border-subtle)',
                        fontSize: '0.8rem',
                        cursor: u.uid === currentUid ? 'not-allowed' : 'pointer'
                      }}
                    >
                      <option value="Administrator">Administrator</option>
                      <option value="Operator">Operator</option>
                      <option value="User">User</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

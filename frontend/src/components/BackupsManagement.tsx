import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { Archive, Plus, RotateCcw, CheckCircle, ShieldAlert, FileText, Database } from 'lucide-react';

export const BackupsManagement: React.FC<{ userRole: string }> = ({ userRole }) => {
  const [backups, setBackups] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const data = await apiRequest('/backups?limit=50');
      setBackups(data || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleCreateBackup = async () => {
    try {
      setLoading(true);
      setMessage('Creating new backup archive and synchronizing with MinIO...');
      const res = await apiRequest('/backups/create?backup_type=manual', { method: 'POST' });
      setMessage(`Backup created successfully: ${res.filename}`);
      await fetchBackups();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (backupId: number, filename: string) => {
    if (!confirm(`Are you sure you want to restore "${filename}"? The Minecraft server will be stopped temporarily during the restore.`)) {
      return;
    }
    try {
      setLoading(true);
      setMessage(`Initiating restore of backup ID #${backupId}...`);
      const res = await apiRequest(`/backups/${backupId}/restore`, { method: 'POST' });
      setMessage(res.message || 'Backup restored successfully!');
    } catch (e: any) {
      setMessage(`Restore failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '0 KB';
    const mb = bytes / (1024 * 1024);
    if (mb > 1) return `${mb.toFixed(2)} MB`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const canCreate = userRole === 'Administrator' || userRole === 'Operator';
  const canRestore = userRole === 'Administrator';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>MinIO Backups & Recovery</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Automated S3 object storage snapshots, SHA256 integrity verification, and safe rollback
          </p>
        </div>

        {canCreate && (
          <button 
            onClick={handleCreateBackup} 
            disabled={loading} 
            className="btn btn-primary"
          >
            <Plus size={16} /> Create Backup Now
          </button>
        )}
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
          <Database size={20} color="#818cf8" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Archived Snapshots in MinIO</h3>
        </div>

        {backups.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            No backup archives found. Click "Create Backup Now" to capture the current world state.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                  <th style={{ padding: '12px 14px' }}>FILENAME</th>
                  <th style={{ padding: '12px 14px' }}>TYPE</th>
                  <th style={{ padding: '12px 14px' }}>SIZE</th>
                  <th style={{ padding: '12px 14px' }}>SHA256 CHECKSUM</th>
                  <th style={{ padding: '12px 14px' }}>CREATED AT</th>
                  <th style={{ padding: '12px 14px', textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {backups.map(b => (
                  <tr key={b.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: 'white' }}>
                      {b.filename}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${b.backup_type === 'scheduled' ? 'badge-warning' : 'badge-success'}`}>
                        {b.backup_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      {formatSize(b.size_bytes)}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {b.checksum_sha256.substring(0, 16)}...
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                      {canRestore ? (
                        <button
                          disabled={loading}
                          onClick={() => handleRestore(b.id, b.filename)}
                          className="btn btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                        >
                          <RotateCcw size={14} /> Restore
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Admin Only</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

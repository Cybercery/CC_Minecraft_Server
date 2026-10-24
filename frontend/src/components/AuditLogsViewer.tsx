import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { FileText, Shield, CheckCircle2, XCircle } from 'lucide-react';

export const AuditLogsViewer: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await apiRequest('/auth/audit-logs?limit=100');
      setLogs(data || []);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Security & Administrative Audit Trail</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Immutable activity stream of server lifecycle, backups, RCON executions, and role changes
        </p>
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <Shield size={20} color="#818cf8" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Recent Audit Events</h3>
        </div>

        {logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            No audit events recorded yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                  <th style={{ padding: '12px 14px' }}>TIMESTAMP</th>
                  <th style={{ padding: '12px 14px' }}>ACTOR</th>
                  <th style={{ padding: '12px 14px' }}>ACTION</th>
                  <th style={{ padding: '12px 14px' }}>RESOURCE</th>
                  <th style={{ padding: '12px 14px' }}>STATUS</th>
                  <th style={{ padding: '12px 14px' }}>DETAILS</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '12px 14px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'white', fontWeight: 500 }}>
                      {log.email || log.uid || 'system'}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700, color: '#818cf8' }}>
                      {log.action}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-dim)' }}>
                      {log.resource}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                        {log.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-dim)' }}>
                      {log.details ? JSON.stringify(log.details) : '-'}
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

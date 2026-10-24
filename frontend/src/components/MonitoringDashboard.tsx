import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { Cpu, HardDrive, Activity, Users, RefreshCw } from 'lucide-react';

export const MonitoringDashboard: React.FC = () => {
  const [current, setCurrent] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const curr = await apiRequest('/metrics/current');
      setCurrent(curr);
      const hist = await apiRequest(`/metrics/history?hours=${hours}&limit=100`);
      setHistory(hist);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [hours]);

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 MB';
    const mb = bytes / (1024 * 1024);
    if (mb > 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Telemetry & Live Metrics</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            System resource utilization and historical time-series analytics
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select 
            value={hours} 
            onChange={e => setHours(Number(e.target.value))}
            style={{
              padding: '8px 12px',
              borderRadius: '8px',
              background: 'rgba(0,0,0,0.4)',
              color: 'white',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.85rem'
            }}
          >
            <option value={1}>Last 1 Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last 7 Days</option>
          </select>

          <button onClick={fetchMetrics} disabled={loading} className="btn btn-secondary">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {/* Real-time Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        {/* CPU */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>CPU LOAD</span>
            <Cpu size={18} color="#818cf8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {current?.cpu_percent?.toFixed(1) || 0}%
          </div>
          <div style={{
            height: '6px',
            borderRadius: '3px',
            background: 'rgba(255,255,255,0.1)',
            marginTop: '12px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min(current?.cpu_percent || 0, 100)}%`,
              height: '100%',
              background: (current?.cpu_percent || 0) > 80 ? 'var(--accent-rose)' : 'var(--accent-primary)',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Memory */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>RAM USAGE</span>
            <Activity size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {current?.memory_percent?.toFixed(1) || 0}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            {formatBytes(current?.memory_bytes)} / {formatBytes(current?.memory_total_bytes)}
          </div>
          <div style={{
            height: '6px',
            borderRadius: '3px',
            background: 'rgba(255,255,255,0.1)',
            marginTop: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min(current?.memory_percent || 0, 100)}%`,
              height: '100%',
              background: (current?.memory_percent || 0) > 90 ? 'var(--accent-rose)' : '#34d399',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Disk */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>DISK UTILIZATION</span>
            <HardDrive size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {current?.disk_percent?.toFixed(1) || 0}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            {formatBytes(current?.disk_used_bytes)} / {formatBytes(current?.disk_total_bytes)}
          </div>
          <div style={{
            height: '6px',
            borderRadius: '3px',
            background: 'rgba(255,255,255,0.1)',
            marginTop: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.min(current?.disk_percent || 0, 100)}%`,
              height: '100%',
              background: (current?.disk_percent || 0) > 85 ? 'var(--accent-rose)' : '#f59e0b',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* Players */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>ONLINE PLAYERS</span>
            <Users size={18} color="#06b6d4" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#06b6d4' }}>
            {current?.online_players || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Container status: {current?.is_running ? 'Online' : 'Stopped'}
          </div>
        </div>
      </div>

      {/* Historical Data Feed */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px' }}>
          Historical Telemetry Records
        </h3>

        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            No historical metrics collected yet for this timeframe.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                  <th style={{ padding: '10px 14px' }}>TIMESTAMP (UTC)</th>
                  <th style={{ padding: '10px 14px' }}>CPU</th>
                  <th style={{ padding: '10px 14px' }}>RAM %</th>
                  <th style={{ padding: '10px 14px' }}>DISK %</th>
                  <th style={{ padding: '10px 14px' }}>PLAYERS</th>
                  <th style={{ padding: '10px 14px' }}>STATE</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(-15).reverse().map((m, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace' }}>
                      {new Date(m.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      {m.cpu_percent.toFixed(1)}%
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {m.memory_percent.toFixed(1)}%
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {m.disk_percent.toFixed(1)}%
                    </td>
                    <td style={{ padding: '10px 14px', color: '#34d399', fontWeight: 700 }}>
                      {m.online_players}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span className={`badge ${m.is_running ? 'badge-success' : 'badge-danger'}`} style={{ padding: '2px 8px', fontSize: '0.65rem' }}>
                        {m.is_running ? 'Online' : 'Down'}
                      </span>
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

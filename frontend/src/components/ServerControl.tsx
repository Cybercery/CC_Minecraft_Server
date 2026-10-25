import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { Server, Play, Square, RotateCw, Terminal, Clock, Users, HardDrive, Info } from 'lucide-react';

export const ServerControl: React.FC<{ userRole: string }> = ({ userRole }) => {
  const [status, setStatus] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [rconCmd, setRconCmd] = useState('');
  const [rconOutput, setRconOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [propertiesData, setPropertiesData] = useState<any>(null);
  const [showConfig, setShowConfig] = useState(false);

  const fetchProperties = async () => {
    try {
      const data = await apiRequest('/server/properties');
      setPropertiesData(data);
    } catch (e: any) {
      console.error('Failed to load server properties:', e);
    }
  };

  const fetchStatusAndLogs = async () => {
    try {
      const statusData = await apiRequest('/server/status');
      setStatus(statusData);
      const logsData = await apiRequest('/server/logs?tail=80');
      setLogs(logsData.logs || []);
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatusAndLogs();
    const timer = setInterval(fetchStatusAndLogs, 4000);
    return () => clearInterval(timer);
  }, []);

  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    try {
      setLoading(true);
      setActionMsg(`Sending ${action} request...`);
      await apiRequest(`/server/${action}`, { method: 'POST' });
      setActionMsg(`Server ${action} command completed.`);
      await fetchStatusAndLogs();
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRconSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rconCmd.trim()) return;
    try {
      setLoading(true);
      const res = await apiRequest('/server/rcon', {
        method: 'POST',
        body: JSON.stringify({ command: rconCmd.trim() })
      });
      setRconOutput(`> ${rconCmd}\n${res.response}`);
      setRconCmd('');
    } catch (e: any) {
      setRconOutput(`> ${rconCmd}\nError: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const canControl = userRole === 'Administrator' || userRole === 'Operator';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Minecraft Server Management</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Lifecycle controls, live console terminal, and RCON command dispatch
          </p>
        </div>

        {canControl && (
          <div style={{ display: 'flex', gap: '10px' }}>
            <button 
              disabled={loading || status?.running} 
              onClick={() => handleAction('start')} 
              className="btn btn-primary"
              style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
            >
              <Play size={16} /> Start
            </button>
            <button 
              disabled={loading || !status?.running} 
              onClick={() => handleAction('stop')} 
              className="btn btn-danger"
            >
              <Square size={16} /> Stop
            </button>
            <button 
              disabled={loading} 
              onClick={() => handleAction('restart')} 
              className="btn btn-secondary"
            >
              <RotateCw size={16} /> Restart
            </button>
          </div>
        )}
      </div>

      {actionMsg && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(99, 102, 241, 0.1)',
          border: '1px solid var(--border-accent)',
          borderRadius: '10px',
          fontSize: '0.85rem'
        }}>
          {actionMsg}
        </div>
      )}

      {/* Status Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>STATE</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className={`badge ${status?.running ? 'badge-success' : 'badge-danger'}`}>
              {status?.status || 'UNKNOWN'}
            </span>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>CONTAINER</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace' }}>
            {status?.name || 'cloud-minecraft'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>PLAYERS ONLINE</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            {status?.players_online || 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>AUTH MODE</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className={`badge ${status?.online_mode !== false ? 'badge-success' : 'badge-warning'}`}>
              {status?.online_mode !== false ? 'ONLINE (Mojang)' : 'OFFLINE (Private Dev)'}
            </span>
          </div>
        </div>
      </div>

      {/* Server Mode Configuration & Properties */}
      {canControl && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Info size={18} color="#818cf8" />
              <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Authentication Mode & Server Properties</h3>
            </div>
            <button
              onClick={() => {
                const next = !showConfig;
                setShowConfig(next);
                if (next && !propertiesData) {
                  fetchProperties();
                }
              }}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            >
              {showConfig ? 'Hide Details' : 'Inspect Config'}
            </button>
          </div>

          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.5' }}>
            {status?.online_mode !== false ? (
              <span>
                <strong>Premium Mode Active:</strong> Players authenticate via Mojang/Microsoft session servers. Tamper-proof Mojang UUIDs are assigned and verified.
              </span>
            ) : (
              <span>
                <strong>Offline Testing Mode Active:</strong> Server accepts connections without Mojang authentication for private dev/testing. In-game verification still restricts unverified players until approved on this dashboard.
              </span>
            )}
          </p>

          {showConfig && (
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px', fontSize: '0.85rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>How to Switch Online/Offline Mode:</div>
                <ol style={{ paddingLeft: '20px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <li>Edit <code>.env</code> file: set <code>MINECRAFT_ONLINE_MODE=true</code> (Premium) or <code>MINECRAFT_ONLINE_MODE=false</code> (Offline).</li>
                  <li>Recreate container: <code>docker compose up -d minecraft</code></li>
                  <li><code>server.properties</code> inside the <code>mc_data</code> volume will update automatically via <code>OVERRIDE_SERVER_PROPERTIES=true</code>.</li>
                </ol>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '14px', borderRadius: '8px', fontSize: '0.85rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>Direct CLI Inspection Commands:</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div>
                    <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>Running container:</span>
                    <pre style={{ margin: '4px 0 0 0', padding: '8px', background: 'rgba(0,0,0,0.5)', borderRadius: '6px', fontSize: '0.8rem', color: '#38bdf8' }}>
                      docker exec cloud-minecraft cat /data/server.properties
                    </pre>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>Stopped container (safe inspection of volume):</span>
                    <pre style={{ margin: '4px 0 0 0', padding: '8px', background: 'rgba(0,0,0,0.5)', borderRadius: '6px', fontSize: '0.8rem', color: '#38bdf8' }}>
                      docker run --rm -v minecraft_server_project_mc_data:/data alpine cat /data/server.properties
                    </pre>
                  </div>
                </div>
              </div>

              {propertiesData?.content && (
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>
                    Live server.properties ({propertiesData.source}):
                  </div>
                  <pre style={{
                    maxHeight: '200px',
                    overflowY: 'auto',
                    padding: '12px',
                    background: 'rgba(0,0,0,0.6)',
                    borderRadius: '8px',
                    fontSize: '0.75rem',
                    color: '#94a3b8'
                  }}>
                    {propertiesData.content}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* RCON Console */}
      {canControl && (
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Terminal size={18} color="#818cf8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Execute RCON Command</h3>
          </div>

          <form onSubmit={handleRconSubmit} style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="text"
              value={rconCmd}
              onChange={e => setRconCmd(e.target.value)}
              placeholder="e.g. time set day, op Notch, weather clear"
              style={{
                flex: 1,
                padding: '10px 14px',
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: 'white',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '0.9rem'
              }}
            />
            <button type="submit" disabled={loading} className="btn btn-primary">
              Send
            </button>
          </form>

          {rconOutput && (
            <pre style={{
              marginTop: '14px',
              padding: '12px',
              background: 'rgba(0, 0, 0, 0.6)',
              borderRadius: '8px',
              fontSize: '0.85rem',
              color: '#34d399',
              whiteSpace: 'pre-wrap'
            }}>
              {rconOutput}
            </pre>
          )}
        </div>
      )}

      {/* Real-time Server Log Console */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={18} color="#818cf8" />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Console Output</h3>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            Auto-refreshing every 4s
          </div>
        </div>

        <div style={{
          height: '340px',
          overflowY: 'auto',
          background: 'rgba(0, 0, 0, 0.65)',
          padding: '16px',
          borderRadius: '10px',
          border: '1px solid var(--border-subtle)',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize: '0.8rem',
          color: '#cbd5e1',
          lineHeight: '1.6'
        }}>
          {logs.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', textAlign: 'center', marginTop: '140px' }}>
              No console logs available or server offline.
            </div>
          ) : (
            logs.map((line, idx) => (
              <div key={idx} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {line}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

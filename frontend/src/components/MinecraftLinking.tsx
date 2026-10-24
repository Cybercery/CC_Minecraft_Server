import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api';
import { Gamepad2, Key, CheckCircle2, AlertCircle, RefreshCw, Unlink } from 'lucide-react';

export const MinecraftLinking: React.FC = () => {
  const [linkStatus, setLinkStatus] = useState<any>(null);
  const [codeData, setCodeData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchLinkStatus = async () => {
    try {
      const data = await apiRequest('/minecraft/link');
      setLinkStatus(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLinkStatus();
    const interval = setInterval(fetchLinkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerateCode = async () => {
    try {
      setLoading(true);
      setMessage(null);
      const data = await apiRequest('/minecraft/verification-code', { method: 'POST' });
      setCodeData(data);
    } catch (e: any) {
      setMessage(`Error generating code: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUnlink = async () => {
    if (!confirm('Are you sure you want to unlink your Minecraft account?')) return;
    try {
      setLoading(true);
      const res = await apiRequest('/minecraft/link', { method: 'DELETE' });
      setMessage(res.message);
      setCodeData(null);
      await fetchLinkStatus();
    } catch (e: any) {
      setMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Minecraft Account Link</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Pair your in-game identity with your web cloud credentials to unlock permissions
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

      {/* Link Status Card */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: linkStatus?.linked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Gamepad2 size={24} color={linkStatus?.linked ? '#34d399' : '#fb7185'} />
            </div>

            <div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {linkStatus?.linked ? `Linked to ${linkStatus.minecraft_username}` : 'Not Linked'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                {linkStatus?.linked ? `UUID: ${linkStatus.minecraft_uuid}` : 'No player account linked'}
              </div>
            </div>
          </div>

          <div>
            <span className={`badge ${linkStatus?.linked ? 'badge-success' : 'badge-danger'}`}>
              {linkStatus?.linked ? 'Verified' : 'Unlinked'}
            </span>
          </div>
        </div>

        {linkStatus?.linked ? (
          <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Linked since: {new Date(linkStatus.linked_at).toLocaleString()}
            </div>
            <button 
              onClick={handleUnlink} 
              disabled={loading}
              className="btn btn-danger"
              style={{ padding: '8px 14px', fontSize: '0.8rem' }}
            >
              <Unlink size={14} /> Unlink Account
            </button>
          </div>
        ) : (
          <div style={{ marginTop: '28px', paddingTop: '24px', borderTop: '1px solid var(--border-subtle)' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '10px' }}>
              How to verify in-game:
            </h4>
            <ol style={{ paddingLeft: '20px', fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <li>Click the button below to generate a unique 6-character code.</li>
              <li>Join the Minecraft server at <code>localhost:25565</code>.</li>
              <li>Type <code>/verify &lt;CODE&gt;</code> into chat.</li>
              <li>Your restrictions will lift immediately!</li>
            </ol>

            <div style={{ marginTop: '20px' }}>
              <button 
                onClick={handleGenerateCode} 
                disabled={loading} 
                className="btn btn-primary"
                style={{ padding: '12px 20px' }}
              >
                <Key size={16} /> Generate Verification Code
              </button>
            </div>

            {codeData && (
              <div style={{
                marginTop: '20px',
                padding: '20px',
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid var(--border-accent)',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>
                  YOUR 6-CHARACTER VERIFICATION CODE
                </div>
                <div style={{
                  fontSize: '2.4rem',
                  fontWeight: 900,
                  letterSpacing: '6px',
                  color: '#818cf8',
                  fontFamily: 'JetBrains Mono, monospace'
                }}>
                  {codeData.code}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#fbbf24', marginTop: '8px' }}>
                  Expires at {new Date(codeData.expires_at).toLocaleTimeString()}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '12px' }}>
                  In-game command: <strong>/verify {codeData.code}</strong>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

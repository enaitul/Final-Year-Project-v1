import React, { useState } from 'react';
import { KeyRound, Server, Eye, EyeOff, ShieldCheck } from 'lucide-react';

export function CredentialBar({ credentials, updateCredentials }) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div
      className="glass-card"
      style={{
        padding: '16px 22px',
        marginBottom: 24,
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(6, 182, 212, 0.04) 100%)',
        borderColor: 'rgba(99, 102, 241, 0.22)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: '0 2px 10px rgba(99, 102, 241, 0.3)',
            }}
          >
            <KeyRound size={20} />
          </div>
          <div>
            <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--indigo-400)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              MySQL Connection Configuration
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)' }}>
              Credentials piped directly to isolated test runners; passwords are not permanently stored in code
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Admin User
            </label>
            <input
              type="text"
              className="input-field"
              value={credentials.user}
              onChange={(e) => updateCredentials({ user: e.target.value })}
              placeholder="root"
              style={{ width: 140 }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Password
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                className="input-field"
                value={credentials.password}
                onChange={(e) => updateCredentials({ password: e.target.value })}
                placeholder="Enter MySQL password"
                style={{ width: 180, paddingRight: 36 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 8,
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-dim)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                }}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Host
            </label>
            <input
              type="text"
              className="input-field"
              value={credentials.host}
              onChange={(e) => updateCredentials({ host: e.target.value })}
              placeholder="localhost"
              style={{ width: 130 }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', paddingTop: 18 }}>
            <span
              className="badge badge-success"
              style={{ padding: '8px 12px', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <ShieldCheck size={14} />
              Session Protected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

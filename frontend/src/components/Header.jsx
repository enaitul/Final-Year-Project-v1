import React from 'react';
import { Database, Zap, Cpu, CheckCircle2, AlertOctagon, Loader2 } from 'lucide-react';

export function Header({ status }) {
  const getStatusBadge = () => {
    switch (status.state) {
      case 'running':
        return (
          <div className="badge badge-warning" style={{ padding: '6px 14px', gap: '8px' }}>
            <Loader2 size={14} className="anim-spin" style={{ animation: 'spin 1s linear infinite' }} />
            <span>RUNNING: {status.text}</span>
          </div>
        );
      case 'success':
        return (
          <div className="badge badge-success" style={{ padding: '6px 14px', gap: '8px' }}>
            <CheckCircle2 size={14} />
            <span>{status.text}</span>
          </div>
        );
      case 'failed':
        return (
          <div className="badge badge-danger" style={{ padding: '6px 14px', gap: '8px' }}>
            <AlertOctagon size={14} />
            <span>{status.text}</span>
          </div>
        );
      default:
        return (
          <div className="badge badge-neutral" style={{ padding: '6px 14px', gap: '8px' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--emerald-400)', display: 'inline-block' }} />
            <span>SYSTEM IDLE &middot; READY</span>
          </div>
        );
    }
  };

  return (
    <header style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 14,
              background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 24px rgba(99, 102, 241, 0.35)',
              color: '#fff',
            }}
          >
            <Zap size={26} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
                <span style={{ background: 'linear-gradient(135deg, #818cf8, #38bdf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  AI-Powered
                </span>{' '}
                MySQL Automated Testing Framework
              </h1>
              <span className="badge badge-neutral" style={{ border: '1px solid rgba(129, 140, 248, 0.3)', color: 'var(--indigo-400)' }}>
                React v2.2
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 2 }}>
              Multi-Worker Concurrency Architecture &middot; 1,500 Test Cases &middot; AI Root Cause Diagnostics &middot; Anomaly Simulation
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {getStatusBadge()}
        </div>
      </div>
    </header>
  );
}

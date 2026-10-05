import React from 'react';
import {
  LayoutDashboard,
  PlayCircle,
  BarChart3,
  Filter,
  GitCompare,
  Sparkles,
  AlertTriangle,
  Server,
} from 'lucide-react';

const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'execution', label: 'Execution Control', icon: PlayCircle },
  { id: 'benchmark', label: 'Performance', icon: BarChart3 },
  { id: 'selective', label: 'Selective Run', icon: Filter },
  { id: 'diff', label: 'Compare Results', icon: GitCompare },
  { id: 'ai', label: 'AI Diagnostics', icon: Sparkles },
  { id: 'simulation', label: 'Simulation', icon: AlertTriangle },
  { id: 'remote', label: 'Remote Hosts', icon: Server },
];

export function Navigation({ activeTab, setActiveTab }) {
  return (
    <nav
      style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: 26,
        width: '100%',
        paddingBottom: 0,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexWrap: 'wrap',
          gap: 4,
          width: '100%',
          background: 'rgba(18, 24, 38, 0.75)',
          border: '1px solid var(--glass-border)',
          borderRadius: 'var(--radius-md)',
          padding: '6px',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.25)',
        }}
      >
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 14px',
                borderRadius: 'var(--radius-pill)',
                border: 'none',
                background: isActive
                  ? 'linear-gradient(135deg, #6366f1, #4f46e5)'
                  : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                fontWeight: 600,
                fontSize: '0.82rem',
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: isActive ? '0 2px 16px var(--indigo-glow)' : 'none',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--text-main)';
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = 'var(--text-muted)';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

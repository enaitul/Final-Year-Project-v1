import React, { useState, useRef, useEffect } from 'react';
import {
  Database,
  Rocket,
  CheckCircle2,
  Zap,
  BarChart3,
  AlertTriangle,
  Server,
  Copy,
  Trash2,
  Search,
  Check,
  Terminal,
} from 'lucide-react';

export function ExecutionTab({ status, consoleOutput, clearLog, runCommand }) {
  const [filterText, setFilterText] = useState('');
  const [copied, setCopied] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const consoleRef = useRef(null);

  useEffect(() => {
    if (autoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleOutput, autoScroll]);

  const handleCopy = () => {
    navigator.clipboard.writeText(consoleOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredOutput = filterText
    ? consoleOutput
        .split('\n')
        .filter((line) => line.toLowerCase().includes(filterText.toLowerCase()))
        .join('\n')
    : consoleOutput;

  const isRunning = status.state === 'running';

  return (
    <div className="tab-content-enter">
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20 }}>
        {/* Execution Workflow Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="glass-card">
            <div className="card-title" style={{ marginBottom: 14 }}>
              Execution Workflow
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                className="btn btn-glass"
                disabled={isRunning}
                onClick={() => runCommand('setup')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <Database size={16} color="var(--indigo-400)" />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>1. Setup Group DBs</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Recreates ai_testing_group1..4</div>
                </div>
              </button>

              <button
                className="btn btn-primary"
                disabled={isRunning}
                onClick={() => runCommand('parallel')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <Rocket size={16} />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>2. Run 4 Workers</div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>Parallel test execution (1,500 TCs)</div>
                </div>
              </button>

              <button
                className="btn btn-emerald"
                disabled={isRunning}
                onClick={() => runCommand('merge')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <CheckCircle2 size={16} />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>3. Merge & Validate</div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.85 }}>10-point baseline integrity check</div>
                </div>
              </button>

              <div style={{ height: 1, background: 'var(--glass-border)', margin: '6px 0' }} />

              <button
                className="btn btn-amber"
                disabled={isRunning}
                onClick={() => runCommand('full')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <Zap size={16} />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 800 }}>⚡ Run Full End-to-End Suite</div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.9 }}>Setup &rarr; Parallel Run &rarr; Merge</div>
                </div>
              </button>

              <button
                className="btn btn-glass"
                disabled={isRunning}
                onClick={() => runCommand('benchmark')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <BarChart3 size={16} color="var(--cyan-400)" />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>Run Benchmarks</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Sequential vs Parallel timer</div>
                </div>
              </button>

              <button
                className="btn btn-glass"
                disabled={isRunning}
                onClick={() => runCommand('simulation')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <AlertTriangle size={16} color="var(--amber-400)" />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>Run Failure Simulation</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Inject faults & verify resilience</div>
                </div>
              </button>

              <button
                className="btn btn-glass"
                disabled={isRunning}
                onClick={() => runCommand('remote')}
                style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
              >
                <Server size={16} color="var(--purple-400)" />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontWeight: 700 }}>Dispatch Remote Nodes</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Trigger SSH execution via IPs</div>
                </div>
              </button>
            </div>
          </div>

          {/* Real-time Status Card */}
          <div className="glass-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)', letterSpacing: '0.06em' }}>
              Execution Engine Status
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 10 }}>
              <div
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  background:
                    status.state === 'running'
                      ? 'var(--amber-400)'
                      : status.state === 'success'
                      ? 'var(--emerald-400)'
                      : status.state === 'failed'
                      ? 'var(--rose-400)'
                      : 'var(--text-dim)',
                  boxShadow:
                    status.state === 'running'
                      ? '0 0 12px var(--amber-400)'
                      : status.state === 'success'
                      ? '0 0 12px var(--emerald-400)'
                      : status.state === 'failed'
                      ? '0 0 12px var(--rose-400)'
                      : 'none',
                }}
                className={status.state === 'running' ? 'anim-pulse' : ''}
              />
              <span style={{ fontSize: '0.86rem', fontWeight: 700 }}>
                {status.text}
              </span>
            </div>
          </div>
        </div>

        {/* Real-time Console Terminal */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="terminal-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="terminal-dots">
                <span className="terminal-dot dot-red" />
                <span className="terminal-dot dot-yellow" />
                <span className="terminal-dot dot-green" />
              </div>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Terminal size={14} /> Live Execution Console Terminal
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* Search filter */}
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={14} style={{ position: 'absolute', left: 8, color: 'var(--text-dim)' }} />
                <input
                  type="text"
                  placeholder="Filter console..."
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  style={{
                    background: 'rgba(0,0,0,0.5)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: 6,
                    padding: '4px 8px 4px 28px',
                    fontSize: '0.72rem',
                    color: 'var(--text-main)',
                    width: 140,
                    outline: 'none',
                  }}
                />
              </div>

              {/* Auto scroll toggle */}
              <button
                className={`btn btn-glass`}
                style={{ padding: '4px 10px', fontSize: '0.7rem' }}
                onClick={() => setAutoScroll(!autoScroll)}
              >
                Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
              </button>

              {/* Copy */}
              <button
                className="btn btn-glass"
                style={{ padding: '4px 10px', fontSize: '0.7rem' }}
                onClick={handleCopy}
              >
                {copied ? <Check size={12} color="var(--emerald-400)" /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              {/* Clear */}
              <button
                className="btn btn-glass"
                style={{ padding: '4px 10px', fontSize: '0.7rem' }}
                onClick={clearLog}
              >
                <Trash2 size={12} />
                <span>Clear</span>
              </button>
            </div>
          </div>

          <div className="terminal-body" ref={consoleRef} style={{ height: 530 }}>
            {filteredOutput || '(Empty console output)'}
          </div>
        </div>
      </div>
    </div>
  );
}

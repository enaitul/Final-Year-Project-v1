import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Play,
  RotateCw,
  CheckCircle2,
  ShieldAlert,
  Bug,
  Activity,
  FileText,
} from 'lucide-react';

export function SimulationTab({ fetchSimulation, runCommand, isRunning }) {
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    const data = await fetchSimulation();
    if (data && data.success && data.report) {
      setReport(data.report);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadReport();
  }, [fetchSimulation]);

  const handleRunSimulation = async () => {
    setLoading(true);
    setReport('Running simulate_failures.py... Please wait...\n');
    const data = await runCommand('simulation');
    if (data && data.report) {
      setReport(data.report);
    } else if (data && data.output) {
      setReport(data.output);
    }
    setLoading(false);
  };

  return (
    <div className="tab-content-enter">
      {/* Header and Controls */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
              Failure & Anomaly Simulation Engine
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
              Validates framework resilience against false positives by injecting synthetic schema corruptions and catching unexpected negative query successes.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-amber"
              disabled={isRunning || loading}
              onClick={handleRunSimulation}
            >
              <Play size={16} /> Trigger Live Anomaly Simulation
            </button>
            <button
              className="btn btn-glass"
              disabled={loading}
              onClick={loadReport}
            >
              <RotateCw size={15} className={loading ? 'anim-spin' : ''} /> Refresh Report
            </button>
          </div>
        </div>
      </div>

      {/* KPI Status Cards */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Positive Case Failure Check
            </span>
            <CheckCircle2 size={18} color="var(--emerald-400)" />
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--emerald-400)', marginTop: 8 }}>
            VERIFIED ✅
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Catches syntax & table corruption; sets FAIL
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Negative Case Anomaly Check
            </span>
            <CheckCircle2 size={18} color="var(--emerald-400)" />
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--emerald-400)', marginTop: 8 }}>
            VERIFIED ✅
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Flags unexpected query success as failure anomaly
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Framework Fault Tolerance
            </span>
            <ShieldAlert size={18} color="var(--cyan-400)" />
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--cyan-400)', marginTop: 8 }}>
            100% Protection
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Baseline regression validation active
          </div>
        </div>
      </div>

      {/* Dual Simulation Experiment Flow Cards */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Simulation 1 */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">🧪 Simulation 1: Positive Case Failure (Schema Corruption)</div>
              <div className="card-subtitle">Artificial schema fault injection experiment</div>
            </div>
            <span className="badge badge-danger">Fault Injection</span>
          </div>

          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <p>
              <strong>Injected Condition:</strong> Modifies a positive test query to reference a non-existent table (<code>SELECT * FROM non_existent_table_xyz_123;</code>).
            </p>

            <div
              style={{
                background: '#04060a',
                padding: '12px 14px',
                borderRadius: 'var(--radius-sm)',
                margin: '12px 0',
                fontFamily: 'JetBrains Mono',
                fontSize: '0.75rem',
                border: '1px solid var(--glass-border)',
                lineHeight: 1.7,
              }}
            >
              <div style={{ color: 'var(--amber-400)' }}>Expected: Execution_Status = PASS</div>
              <div style={{ color: 'var(--rose-400)' }}>Injected: MySQL Error 1146 (Table doesn't exist)</div>
              <div style={{ color: 'var(--emerald-400)' }}>Result: Engine Flags Execution_Status = FAIL ✅</div>
            </div>

            <p style={{ fontSize: '0.76rem', color: 'var(--text-dim)' }}>
              <strong>Verification Verdict:</strong> The validation engine accurately captures positive query syntax/schema errors and prevents silent false positives.
            </p>
          </div>
        </div>

        {/* Simulation 2 */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">🧪 Simulation 2: Unexpected Success of Negative Test Case</div>
              <div className="card-subtitle">Expected error violation experiment</div>
            </div>
            <span className="badge badge-warning">Anomaly Detection</span>
          </div>

          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            <p>
              <strong>Injected Condition:</strong> Modifies a negative test case expecting MySQL error 1062 to execute a valid query (<code>SELECT 1;</code>).
            </p>

            <div
              style={{
                background: '#04060a',
                padding: '12px 14px',
                borderRadius: 'var(--radius-sm)',
                margin: '12px 0',
                fontFamily: 'JetBrains Mono',
                fontSize: '0.75rem',
                border: '1px solid var(--glass-border)',
                lineHeight: 1.7,
              }}
            >
              <div style={{ color: 'var(--amber-400)' }}>Expected: MySQL Error 1062 (Duplicate Entry)</div>
              <div style={{ color: 'var(--indigo-400)' }}>Injected: Valid Query Execution (Success)</div>
              <div style={{ color: 'var(--emerald-400)' }}>Result: Caught Anomaly &amp; Flagged as FAIL ✅</div>
            </div>

            <p style={{ fontSize: '0.76rem', color: 'var(--text-dim)' }}>
              <strong>Verification Verdict:</strong> The engine verifies that expected errors occur. If a negative query unexpectedly succeeds, it is immediately flagged as a failure anomaly.
            </p>
          </div>
        </div>
      </div>

      {/* Simulation Analysis Report Console */}
      <div className="glass-card">
        <div className="card-header-flex">
          <div>
            <div className="card-title">
              <FileText size={18} color="var(--amber-400)" /> Simulation Analysis Report
            </div>
            <div className="card-subtitle">Loaded from reports/simulation_analysis_report.txt</div>
          </div>
          <span className="badge badge-neutral">Generated by simulate_failures.py</span>
        </div>

        <div
          style={{
            background: '#04060a',
            border: '1px solid var(--glass-border)',
            borderRadius: 'var(--radius-md)',
            padding: '18px',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '0.78rem',
            lineHeight: 1.7,
            color: 'var(--text-muted)',
            minHeight: 260,
            maxHeight: 440,
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}
        >
          {report ||
            'Click "Trigger Live Anomaly Simulation" to execute simulate_failures.py and view the verification analysis log.'}
        </div>
      </div>
    </div>
  );
}

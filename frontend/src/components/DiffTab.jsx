import React, { useState, useEffect } from 'react';
import {
  GitCompare,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Search,
  Maximize2,
} from 'lucide-react';

export function DiffTab({ fetchCompare, isRunning }) {
  const [diffData, setDiffData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleCompare = async () => {
    setLoading(true);
    const data = await fetchCompare();
    setDiffData(data);
    setLoading(false);
  };

  useEffect(() => {
    handleCompare();
  }, [fetchCompare]);

  const highlightMatches = (text) => {
    if (!searchTerm || !text) return text;
    // Simple text display
    return text;
  };

  return (
    <div className="tab-content-enter">
      {/* Header and Controls */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
              Visual Regression Diff & Baseline Comparison
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
              Side-by-side split-screen comparison of actual merged test execution records against the certified regression baseline.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={14} style={{ position: 'absolute', left: 8, color: 'var(--text-dim)' }} />
              <input
                type="text"
                className="input-field"
                placeholder="Find TC... (e.g. TC1486)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: 28, width: 180 }}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleCompare}
              disabled={loading || isRunning}
            >
              <RotateCw size={15} className={loading ? 'anim-spin' : ''} /> Compare Results
            </button>
          </div>
        </div>

        {/* Match / Mismatch Summary Banner */}
        {diffData && (
          <div
            style={{
              marginTop: 16,
              padding: '12px 18px',
              borderRadius: 'var(--radius-md)',
              background: diffData.match
                ? 'rgba(16, 185, 129, 0.12)'
                : 'rgba(244, 63, 94, 0.12)',
              border: `1px solid ${diffData.match ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            {diffData.match ? (
              <CheckCircle2 size={20} color="var(--emerald-400)" />
            ) : (
              <AlertTriangle size={20} color="var(--rose-400)" />
            )}
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: diffData.match ? 'var(--emerald-400)' : 'var(--rose-400)' }}>
                {diffData.match ? 'PERFECT REGRESSION MATCH' : 'REGRESSION MISMATCH DETECTED'}
              </div>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: 2 }}>
                {diffData.summary || diffData.error || 'No comparison report loaded.'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Side-by-Side Diff Panes */}
      <div className="diff-container">
        {/* Actual Merged Output */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.8rem', fontWeight: 700, color: 'var(--indigo-400)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--indigo-400)' }} />
              ACTUAL MERGED OUTPUT (`reports/response_merged.txt`)
            </div>
            <span className="badge badge-neutral">Latest Execution</span>
          </div>

          <div className="diff-pane" style={{ height: 500 }}>
            {diffData?.actual ? (
              diffData.actual
            ) : (
              <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '50px 0' }}>
                Run Merge & Validate from Execution Control, then click "Compare Results"
              </div>
            )}
          </div>
        </div>

        {/* Standard Baseline Output */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.8rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--emerald-400)' }} />
              CERTIFIED STANDARD BASELINE (`reports/standard_test_results.txt`)
            </div>
            <span className="badge badge-success">Golden Reference</span>
          </div>

          <div className="diff-pane" style={{ height: 500 }}>
            {diffData?.baseline ? (
              diffData.baseline
            ) : (
              <div style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '50px 0' }}>
                Baseline reference file loaded from reports/standard_test_results.txt
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

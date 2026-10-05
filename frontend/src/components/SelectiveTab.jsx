import React, { useState } from 'react';
import {
  Filter,
  Play,
  Search,
  CheckCircle2,
  AlertCircle,
  Download,
  Clock,
  Layers,
} from 'lucide-react';

export function SelectiveTab({ runCommand, isRunning }) {
  const [filter, setFilter] = useState({
    feature: '',
    featureName: '',
    testIds: '',
    testType: 'ALL',
    limit: '25',
  });

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTable, setSearchTable] = useState('');

  const handleRun = async () => {
    setLoading(true);
    const res = await runCommand('selective', {
      feature: filter.feature,
      feature_name: filter.featureName,
      test_ids: filter.testIds,
      test_type: filter.testType,
      limit: filter.limit,
    });

    if (res && res.success && res.results) {
      setResults(res.results);
    }
    setLoading(false);
  };

  const filteredRows = results.filter((r) => {
    if (!searchTable) return true;
    const q = searchTable.toLowerCase();
    return (
      (r.Test_Case_ID || '').toLowerCase().includes(q) ||
      (r.Feature_ID || '').toLowerCase().includes(q) ||
      (r.Test_Type || '').toLowerCase().includes(q) ||
      (r.Status || '').toLowerCase().includes(q) ||
      (r.Actual_Error || '').toLowerCase().includes(q)
    );
  });

  const passedCount = results.filter((r) => (r.Status || '').toUpperCase() === 'PASS').length;
  const failedCount = results.filter((r) => (r.Status || '').toUpperCase() === 'FAIL').length;
  const avgTime = results.length
    ? (
        results.reduce((acc, r) => acc + Number(r.Execution_Time || 0), 0) /
        results.length
      ).toFixed(4)
    : '0.0000';

  const exportCSV = () => {
    if (!results.length) return;
    const headers = ['Test_Case_ID', 'Feature_ID', 'Test_Type', 'Status', 'Execution_Time', 'Actual_Error'];
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(',')]
        .concat(
          results.map((r) =>
            [
              r.Test_Case_ID,
              r.Feature_ID,
              r.Test_Type,
              r.Status,
              r.Execution_Time,
              `"${(r.Actual_Error || '').replace(/"/g, '""')}"`,
            ].join(',')
          )
        )
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'selective_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="tab-content-enter">
      {/* Filter Card */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <div className="card-header-flex">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
              Selective Execution Engine & Filter
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
              Execute custom subsets of the 1,500 test suite by Feature ID, Name, specific Case IDs, or Test Types.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-end', marginTop: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Feature ID
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. F001 F025"
              value={filter.feature}
              onChange={(e) => setFilter({ ...filter, feature: e.target.value })}
              style={{ width: 140 }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Feature Name
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. employee"
              value={filter.featureName}
              onChange={(e) => setFilter({ ...filter, featureName: e.target.value })}
              style={{ width: 150 }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Test Case IDs
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g. TC001 TC050"
              value={filter.testIds}
              onChange={(e) => setFilter({ ...filter, testIds: e.target.value })}
              style={{ width: 160 }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Test Type
            </label>
            <select
              className="input-field"
              value={filter.testType}
              onChange={(e) => setFilter({ ...filter, testType: e.target.value })}
              style={{ width: 130, cursor: 'pointer' }}
            >
              <option value="ALL">All Types</option>
              <option value="Positive">Positive</option>
              <option value="Negative">Negative</option>
              <option value="Edge">Edge</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Limit
            </label>
            <input
              type="number"
              className="input-field"
              placeholder="25"
              value={filter.limit}
              onChange={(e) => setFilter({ ...filter, limit: e.target.value })}
              style={{ width: 80 }}
            />
          </div>

          <button
            className="btn btn-primary"
            onClick={handleRun}
            disabled={loading || isRunning}
            style={{ padding: '10px 20px' }}
          >
            <Play size={16} /> Run Filtered Suite
          </button>
        </div>
      </div>

      {/* Metrics Bar when results exist */}
      {results.length > 0 && (
        <div className="grid-4" style={{ marginBottom: 16 }}>
          <div className="glass-card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>Total Filtered</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: 4 }}>{results.length} Cases</div>
          </div>
          <div className="glass-card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>Passed</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--emerald-400)', marginTop: 4 }}>{passedCount} Passed</div>
          </div>
          <div className="glass-card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>Failed</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: failedCount ? 'var(--rose-400)' : 'var(--text-muted)', marginTop: 4 }}>{failedCount} Failed</div>
          </div>
          <div className="glass-card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 700 }}>Avg Latency</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--cyan-400)', marginTop: 4 }}>{avgTime}s</div>
          </div>
        </div>
      )}

      {/* Results Table */}
      <div className="glass-card">
        <div className="card-header-flex">
          <div>
            <div className="card-title">Execution Results</div>
            <div className="card-subtitle">Loaded from reports/selective_results.csv</div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {results.length > 0 && (
              <>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <Search size={14} style={{ position: 'absolute', left: 8, color: 'var(--text-dim)' }} />
                  <input
                    type="text"
                    placeholder="Search in table..."
                    value={searchTable}
                    onChange={(e) => setSearchTable(e.target.value)}
                    style={{
                      background: 'rgba(0,0,0,0.4)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 6,
                      padding: '6px 8px 6px 28px',
                      fontSize: '0.76rem',
                      color: 'var(--text-main)',
                      width: 160,
                      outline: 'none',
                    }}
                  />
                </div>

                <button className="btn btn-glass" style={{ padding: '6px 12px', fontSize: '0.74rem' }} onClick={exportCSV}>
                  <Download size={14} /> Export CSV
                </button>
              </>
            )}
          </div>
        </div>

        <div style={{ overflowX: 'auto', maxHeight: 440, borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#090e18', borderBottom: '1px solid var(--glass-border)', color: 'var(--text-dim)', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                <th style={{ padding: '12px 14px' }}>Case ID</th>
                <th style={{ padding: '12px 14px' }}>Feature</th>
                <th style={{ padding: '12px 14px' }}>Type</th>
                <th style={{ padding: '12px 14px' }}>Status</th>
                <th style={{ padding: '12px 14px' }}>Time (s)</th>
                <th style={{ padding: '12px 14px' }}>Output / Captured Error</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                    {results.length === 0 ? 'Configure filters and click "Run Filtered Suite" to execute test cases' : 'No records match search'}
                  </td>
                </tr>
              ) : (
                filteredRows.map((r, i) => {
                  const isPass = (r.Status || '').toUpperCase() === 'PASS';
                  return (
                    <tr
                      key={i}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: i % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                      }}
                    >
                      <td style={{ padding: '10px 14px', fontFamily: 'JetBrains Mono', fontWeight: 700, color: 'var(--indigo-400)' }}>
                        {r.Test_Case_ID}
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                        {r.Feature_ID}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span className="badge badge-neutral">{r.Test_Type}</span>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <span className={`badge ${isPass ? 'badge-success' : 'badge-danger'}`}>
                          {isPass ? 'PASS' : 'FAIL'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 14px', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>
                        {Number(r.Execution_Time || 0).toFixed(4)}s
                      </td>
                      <td style={{ padding: '10px 14px', color: isPass ? 'var(--text-dim)' : 'var(--rose-400)', fontFamily: 'JetBrains Mono', fontSize: '0.74rem' }}>
                        {r.Actual_Error || 'Query executed successfully'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

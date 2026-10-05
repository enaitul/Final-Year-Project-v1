import React, { useEffect, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  Database,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Activity,
  ArrowRight,
  ShieldCheck,
  Server,
  Layers,
  HelpCircle,
} from 'lucide-react';

const TYPE_COLORS = ['#38bdf8', '#fb7185', '#a78bfa'];

export function OverviewTab({ fetchOverview, setActiveTab, runCommand }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview().then((res) => {
      if (res && res.success && res.overview) {
        setData(res.overview);
      }
      setLoading(false);
    });
  }, [fetchOverview]);

  const testTypeData = [
    { name: 'Positive Tests (Query Succeeds)', value: 500, color: '#38bdf8' },
    { name: 'Negative Tests (Expected SQL Errors)', value: 500, color: '#fb7185' },
    { name: 'Edge Case Tests (Boundary & Limits)', value: 500, color: '#a78bfa' },
  ];

  const errorData = data?.error_categories || [
    { category: 'Constraint Violations (1062/1451)', count: 5, color: '#fbbf24' },
    { category: 'Missing Table/Col (1146/1054)', count: 2, color: '#fb923c' },
    { category: 'Permission / Auth (1044/1045)', count: 2, color: '#f87171' },
    { category: 'Lock / Timeout (1205/1213)', count: 2, color: '#38bdf8' },
    { category: 'Data Truncation (1265/1366)', count: 2, color: '#a3e635' },
    { category: 'Syntax Errors (1064)', count: 1, color: '#c084fc' },
  ];

  return (
    <div className="tab-content-enter">
      {/* Executive Hero */}
      <div
        className="glass-card"
        style={{
          marginBottom: 24,
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.06) 100%)',
          borderColor: 'rgba(99, 102, 241, 0.25)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 20 }}>
          <div>
            <div className="badge badge-info" style={{ marginBottom: 10 }}>
              Architecture Overview &middot; Multi-Worker Concurrency
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 6 }}>
              AI-Powered MySQL Automated Testing Framework
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: 820 }}>
              High-concurrency test automation system executing 1,500 MySQL test cases across 4 concurrent worker processes running against isolated disposable databases. Features automated 10-point regression validation, AI root cause diagnostics, and synthetic anomaly injection.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={() => runCommand('full')}>
              <Zap size={16} /> Run Full Suite
            </button>
            <button className="btn btn-glass" onClick={() => setActiveTab('benchmark')}>
              View Graphs <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700, letterSpacing: '0.06em' }}>
              Total Test Suite
            </span>
            <Layers size={18} color="var(--indigo-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', marginTop: 8 }}>
            1,500
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginTop: 4 }}>
            TC001 &ndash; TC1500 contiguous IDs
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700, letterSpacing: '0.06em' }}>
              Active Concurrency
            </span>
            <Activity size={18} color="var(--cyan-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--cyan-400)', marginTop: 8 }}>
            4 Workers
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginTop: 4 }}>
            375 cases / worker across isolated DBs
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700, letterSpacing: '0.06em' }}>
              Parallel Speedup
            </span>
            <Zap size={18} color="var(--emerald-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--emerald-400)', marginTop: 8 }}>
            2.33x Faster
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginTop: 4 }}>
            57% total execution time saved
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700, letterSpacing: '0.06em' }}>
              Validation Engine
            </span>
            <ShieldCheck size={18} color="var(--purple-400)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--purple-400)', marginTop: 8 }}>
            10-Point Check
          </div>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Automatic baseline regression compare
          </div>
        </div>
      </div>

      {/* Visual Charts: Test Distribution & Error Pattern Diagnostics */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Test Type Distribution Donut Chart */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">📊 Test Suite Distribution Breakdown</div>
              <div className="card-subtitle">Equal partition of 1,500 test cases across evaluation types</div>
            </div>
            <span className="badge badge-neutral">1,500 Total</span>
          </div>

          <div style={{ height: 260, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={testTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={95}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {testTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const item = payload[0];
                      return (
                        <div className="custom-chart-tooltip">
                          <p style={{ fontWeight: 700, color: item.payload.color }}>{item.name}</p>
                          <p style={{ marginTop: 4 }}>
                            Cases: <strong>{item.value}</strong> (33.3%)
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginTop: 10 }}>
            {testTypeData.map((t) => (
              <div key={t.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: t.color }} />
                <span>{t.name.split(' ')[0]}: <strong>500</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Diagnostics Error Pattern Classification */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">🔍 AI Diagnostic Error Pattern Frequency</div>
              <div className="card-subtitle">Detected MySQL error code distribution and root causes</div>
            </div>
            <button className="btn btn-glass" style={{ padding: '6px 12px', fontSize: '0.72rem' }} onClick={() => setActiveTab('ai')}>
              Full Traces
            </button>
          </div>

          <div style={{ height: 260, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorData} layout="vertical" margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis dataKey="category" type="category" width={140} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const item = payload[0];
                      return (
                        <div className="custom-chart-tooltip">
                          <p style={{ fontWeight: 700, color: item.payload.color }}>{item.payload.category}</p>
                          <p style={{ marginTop: 4 }}>
                            Occurrences: <strong>{item.value}</strong>
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {errorData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color || '#6366f1'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ textAlign: 'center', fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 8 }}>
            Scanned across agent_group1.log through agent_group4.log by rule-based heuristic classifier
          </div>
        </div>
      </div>

      {/* 4 Worker Architecture Breakdown */}
      <div className="glass-card" style={{ marginBottom: 24 }}>
        <div className="card-header-flex">
          <div>
            <div className="card-title">⚙️ 4-Worker Concurrent Partitioning Architecture</div>
            <div className="card-subtitle">Complete isolation via separate disposable databases and per-worker response files</div>
          </div>
          <button className="btn btn-emerald" onClick={() => runCommand('parallel')}>
            <Zap size={14} /> Launch 4 Workers
          </button>
        </div>

        <div className="grid-4">
          {[
            {
              group: 1,
              range: 'TC001 - TC375',
              count: 375,
              db: 'ai_testing_group1',
              domain: 'DDL, DML & Schema Basics',
              color: '#38bdf8',
            },
            {
              group: 2,
              range: 'TC376 - TC750',
              count: 375,
              db: 'ai_testing_group2',
              domain: 'Complex Joins, Foreign Keys & Transactions',
              color: '#818cf8',
            },
            {
              group: 3,
              range: 'TC751 - TC1125',
              count: 375,
              db: 'ai_testing_group3',
              domain: 'Analytical Queries & Window Functions',
              color: '#c084fc',
            },
            {
              group: 4,
              range: 'TC1126 - TC1500',
              count: 375,
              db: 'ai_testing_group4',
              domain: 'Stored Procedures, Triggers & Views',
              color: '#34d399',
            },
          ].map((w) => (
            <div
              key={w.group}
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                borderTop: `3px solid ${w.color}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 800, fontSize: '0.9rem', color: w.color }}>
                  WORKER GROUP {w.group}
                </span>
                <span className="badge badge-neutral">{w.count} Cases</span>
              </div>
              <div style={{ fontFamily: 'JetBrains Mono', fontSize: '0.78rem', color: 'var(--text-main)', marginTop: 8 }}>
                Range: <strong>{w.range}</strong>
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
                Database: <code>{w.db}</code>
              </div>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.4 }}>
                {w.domain}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

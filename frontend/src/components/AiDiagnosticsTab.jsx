import React, { useState } from 'react';
import {
  Sparkles,
  Bot,
  AlertTriangle,
  CheckCircle2,
  KeyRound,
  FileText,
  HelpCircle,
  Code2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export function AiDiagnosticsTab({ runCommand, isRunning }) {
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gemini-1.5-flash');
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);

  const errorCategories = [
    { category: 'Constraint Violation (1062/1451)', count: 5, color: '#fbbf24' },
    { category: 'Missing Table/Col (1146/1054)', count: 2, color: '#fb923c' },
    { category: 'Permission / Auth (1044/1045)', count: 2, color: '#f87171' },
    { category: 'Lock / Timeout (1205/1213)', count: 2, color: '#38bdf8' },
    { category: 'Data Truncation (1265/1366)', count: 2, color: '#a3e635' },
    { category: 'Syntax Error (1064)', count: 1, color: '#c084fc' },
  ];

  const diagnosticTraces = [
    {
      group: 'agent_group3:L297',
      category: 'PERMISSION_OR_AUTH (1044)',
      snippet: '[group3] Running TC1044 | F070 | Negative',
      rootCause: 'Database user lacks necessary privileges for the attempted operation.',
      action: 'Verify MYSQL_ADMIN_USER credentials and verify GRANT ALL ON ai_testing_group3.* privileges.',
    },
    {
      group: 'agent_group3:L307',
      category: 'MISSING_TABLE_OR_COLUMN (1054)',
      snippet: '[group3] Running TC1054 | F071 | Positive',
      rootCause: 'Target table or referenced column is missing from the database schema.',
      action: 'Check schema setup script (setup_group_databases.py) to ensure table schema is pre-created.',
    },
    {
      group: 'agent_group3:L315',
      category: 'CONSTRAINT_VIOLATION (1062)',
      snippet: '[group3] Running TC1062 | F071 | Edge',
      rootCause: 'Violation of Primary Key or Unique Constraint integrity.',
      action: 'Ensure prerequisite seed data exists and execution order maintains parent-child relationship integrity.',
    },
    {
      group: 'agent_group3:L317',
      category: 'SYNTAX_ERROR (1064)',
      snippet: '[group3] Running TC1064 | F071 | Edge',
      rootCause: 'Invalid SQL query syntax or reserved keyword collision.',
      action: 'Review query clause ordering, backtick quotation marks, and MySQL 8.0 compatibility.',
    },
    {
      group: 'agent_group4:L83',
      category: 'LOCK_OR_TIMEOUT (1205)',
      snippet: '[group4] Running TC1205 | F082 | Edge',
      rootCause: 'Lock wait timeout exceeded during concurrent transaction contention.',
      action: 'Ensure transactions issue COMMIT or ROLLBACK in finally blocks to avoid holding row-level locks.',
    },
  ];

  const handleRunAi = async () => {
    if (!apiKey.trim()) {
      alert('Please enter a Gemini API Key to run the generative AI analysis agent.');
      return;
    }
    setLoading(true);
    setReport('Preparing local diagnostics and dispatching Gemini AI reasoning model...\n');

    const res = await runCommand('ai', {
      gemini_api_key: apiKey.trim(),
      gemini_model: model,
    });

    if (res && res.report) {
      setReport(res.report);
    } else if (res && res.output) {
      setReport(res.output);
    } else {
      setReport('Diagnostic analysis completed. Check reports/ai_analysis_report.txt for details.');
    }
    setLoading(false);
  };

  return (
    <div className="tab-content-enter">
      {/* Gemini AI Config Card */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <div className="card-header-flex">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
              AI Agent Intelligent Test Log Diagnostics & Root Cause Analysis
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
              Two-stage diagnostic pipeline: local pattern classifier (`ai_agent_analyzer.py`) + Gemini reasoning LLM for actionable fix recommendations.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end', marginTop: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 260 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Gemini API Key
            </label>
            <input
              type="password"
              className="input-field"
              placeholder="Paste your Gemini API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              Gemini Model
            </label>
            <select
              className="input-field"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              style={{ width: 180, cursor: 'pointer' }}
            >
              <option value="gemini-1.5-flash">gemini-1.5-flash (Fast)</option>
              <option value="gemini-1.5-pro">gemini-1.5-pro (Deep Reasoning)</option>
              <option value="gemini-2.0-flash">gemini-2.0-flash</option>
              <option value="gemini-2.5-flash">gemini-2.5-flash</option>
            </select>
          </div>

          <button
            className="btn btn-rose"
            onClick={handleRunAi}
            disabled={loading || isRunning}
            style={{ padding: '10px 22px' }}
          >
            <Sparkles size={16} /> Run Gemini AI Agent
          </button>
        </div>

        <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 10 }}>
          🔒 Security Notice: Your Gemini API key is used strictly in-flight for this session and is never persisted to disk or logs.
        </div>
      </div>

      {/* Grid: Error Category Distribution Chart & Diagnostic Traces */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Error Pattern Chart */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">📊 Error Code Classification Frequency</div>
              <div className="card-subtitle">Scanned from agent_group1.log through agent_group4.log</div>
            </div>
            <span className="badge badge-warning">14 Traces Detected</span>
          </div>

          <div style={{ height: 260, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorCategories} layout="vertical" margin={{ left: 10, right: 30, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="category" type="category" width={150} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="custom-chart-tooltip">
                          <p style={{ fontWeight: 700, color: payload[0].payload.color }}>
                            {payload[0].payload.category}
                          </p>
                          <p style={{ marginTop: 4 }}>
                            Occurrences: <strong>{payload[0].value}</strong>
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                  {errorCategories.map((entry, index) => (
                    <Cell key={`c-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Local Heuristic Traces */}
        <div className="glass-card">
          <div className="card-header-flex">
            <div>
              <div className="card-title">🔍 Diagnostic Trace Samples & Corrective SQL</div>
              <div className="card-subtitle">Generated by ai_agent_analyzer.py</div>
            </div>
            <span className="badge badge-neutral">Rule Engine</span>
          </div>

          <div style={{ height: 260, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, paddingRight: 4 }}>
            {diagnosticTraces.map((trace, i) => (
              <div
                key={i}
                style={{
                  background: 'rgba(0, 0, 0, 0.35)',
                  border: '1px solid var(--glass-border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '10px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.78rem', color: 'var(--indigo-400)' }}>
                    {trace.group} &middot; {trace.category}
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono', color: 'var(--text-dim)', marginTop: 4 }}>
                  {trace.snippet}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  <strong>Root Cause:</strong> {trace.rootCause}
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--emerald-400)', marginTop: 2 }}>
                  <strong>Action:</strong> {trace.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gemini AI Diagnostic Report Viewer */}
      <div className="glass-card">
        <div className="card-header-flex">
          <div>
            <div className="card-title">
              <Bot size={18} color="var(--rose-400)" /> Gemini Generative Diagnostic Intelligence Report
            </div>
            <div className="card-subtitle">Saved to reports/gemini_ai_analysis_report.md</div>
          </div>
          {report && <span className="badge badge-success">Analysis Generated</span>}
        </div>

        <div
          style={{
            background: '#04060a',
            border: '1px solid var(--glass-border)',
            borderRadius: 'var(--radius-md)',
            padding: '18px',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '0.8rem',
            lineHeight: 1.7,
            color: 'var(--text-muted)',
            minHeight: 280,
            maxHeight: 480,
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}
        >
          {report ||
            'Enter your Gemini API Key and click "Run Gemini AI Agent" to generate AI executive summaries, root cause groupings, and automated SQL corrective actions.'}
        </div>
      </div>
    </div>
  );
}

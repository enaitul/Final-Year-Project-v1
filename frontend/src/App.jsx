import React, { useState } from 'react';
import { useTestingApi } from './hooks/useTestingApi';
import { Header } from './components/Header';
import { CredentialBar } from './components/CredentialBar';
import { Navigation } from './components/Navigation';
import { OverviewTab } from './components/OverviewTab';
import { ExecutionTab } from './components/ExecutionTab';
import { BenchmarkTab } from './components/BenchmarkTab';
import { SelectiveTab } from './components/SelectiveTab';
import { DiffTab } from './components/DiffTab';
import { AiDiagnosticsTab } from './components/AiDiagnosticsTab';
import { SimulationTab } from './components/SimulationTab';
import { RemoteExecutionTab } from './components/RemoteExecutionTab';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const {
    credentials,
    updateCredentials,
    status,
    consoleOutput,
    clearLog,
    runCommand,
    fetchCompare,
    fetchBenchmark,
    fetchSimulation,
    fetchOverview,
    fetchHosts,
    fetchLogs,
  } = useTestingApi();

  const isRunning = status.state === 'running';

  return (
    <div className="app-wrapper">
      {/* Top Header */}
      <Header status={status} />

      {/* MySQL Connection Credential Bar */}
      <CredentialBar
        credentials={credentials}
        updateCredentials={updateCredentials}
      />

      {/* Navigation Tabs Bar */}
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Active Tab Panel */}
      <main>
        {activeTab === 'overview' && (
          <OverviewTab
            fetchOverview={fetchOverview}
            setActiveTab={setActiveTab}
            runCommand={runCommand}
          />
        )}

        {activeTab === 'execution' && (
          <ExecutionTab
            status={status}
            consoleOutput={consoleOutput}
            clearLog={clearLog}
            runCommand={runCommand}
          />
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkTab
            fetchBenchmark={fetchBenchmark}
            runCommand={runCommand}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'selective' && (
          <SelectiveTab
            runCommand={runCommand}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'diff' && (
          <DiffTab
            fetchCompare={fetchCompare}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'ai' && (
          <AiDiagnosticsTab
            runCommand={runCommand}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'simulation' && (
          <SimulationTab
            fetchSimulation={fetchSimulation}
            runCommand={runCommand}
            isRunning={isRunning}
          />
        )}

        {activeTab === 'remote' && (
          <RemoteExecutionTab
            fetchHosts={fetchHosts}
            runCommand={runCommand}
            isRunning={isRunning}
          />
        )}
      </main>

      {/* Fixed Bottom Status Bar */}
      <footer
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'rgba(8, 11, 17, 0.88)',
          borderTop: '1px solid var(--glass-border)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          padding: '8px 32px',
          fontSize: '0.74rem',
          color: 'var(--text-dim)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background:
                status.state === 'running'
                  ? 'var(--amber-400)'
                  : status.state === 'success'
                  ? 'var(--emerald-400)'
                  : status.state === 'failed'
                  ? 'var(--rose-400)'
                  : 'var(--emerald-400)',
              display: 'inline-block',
            }}
            className={status.state === 'running' ? 'anim-pulse' : ''}
          />
          <span style={{ color: 'var(--text-muted)' }}>
            System Online &middot; Dashboard v2.2 React Edition &middot; 4 Worker Processes
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ color: status.state === 'running' ? 'var(--amber-400)' : 'var(--text-main)', fontWeight: 600 }}>
            {status.text}
          </span>
          <span style={{ color: 'var(--glass-border-bright)' }}>|</span>
          <span>Port 8050 &middot; 1,500 Test Cases</span>
        </div>
      </footer>
    </div>
  );
}

export default App;

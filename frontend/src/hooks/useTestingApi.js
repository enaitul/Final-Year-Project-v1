import { useState, useEffect, useCallback } from 'react';

const ACTION_DESCRIPTIONS = {
  setup: 'Preparing isolated group databases (ai_testing_group1 .. 4)',
  parallel: 'Running 4 worker groups in parallel across 1,500 test cases',
  merge: 'Merging response records & performing 10-point regression validation',
  full: 'Running complete end-to-end suite (Setup -> Parallel -> Merge)',
  benchmark: 'Executing Sequential vs. Parallel multi-run benchmark suite',
  selective: 'Executing filtered test cases with selective runner',
  ai: 'Analyzing logs & generating Gemini AI diagnostic intelligence',
  simulation: 'Injecting synthetic schema faults & anomaly verification',
  remote: 'Dispatching test suites across remote target devices via SSH',
};

// Keep requests relative to the current origin. In development Vite proxies
// these paths to the Python server; in production gui_dashboard.py serves both
// the React bundle and the API. This also works from another machine on a LAN.
const API_BASE = '';

export function useTestingApi() {
  const [credentials, setCredentials] = useState(() => {
    try {
      const saved = localStorage.getItem('mysql_testing_creds');
      if (saved) return JSON.parse(saved);
    } catch (e) {
      // ignore
    }
    return { user: 'root', password: '', host: 'localhost' };
  });

  const [status, setStatus] = useState({
    state: 'idle', // 'idle' | 'running' | 'success' | 'failed'
    text: 'System Ready',
    activeAction: null,
  });

  const [consoleOutput, setConsoleOutput] = useState(
    '⚡ AI-Powered Automated MySQL Testing Framework v2.2\nSystem online. Ready to execute commands.\n'
  );

  const updateCredentials = (patch) => {
    setCredentials((prev) => {
      const updated = { ...prev, ...patch };
      try {
        localStorage.setItem('mysql_testing_creds', JSON.stringify(updated));
      } catch (e) {
        // ignore
      }
      return updated;
    });
  };

  const appendLog = useCallback((text) => {
    setConsoleOutput((prev) => prev + text);
  }, []);

  const clearLog = useCallback(() => {
    setConsoleOutput('');
  }, []);

  const runCommand = useCallback(
    async (action, extraParams = {}) => {
      const actionName = ACTION_DESCRIPTIONS[action] || action;
      setStatus({ state: 'running', text: actionName + '…', activeAction: action });
      appendLog(`\n======================================================\n`);
      appendLog(`>>> [${new Date().toLocaleTimeString()}] Triggering: ${actionName}\n`);
      appendLog(`======================================================\n`);

      try {
        const payload = {
          action,
          user: credentials.user,
          password: credentials.password,
          host: credentials.host,
          ...extraParams,
        };

        const res = await fetch(`${API_BASE}/api/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok && !data.output) {
          data.output = `Request failed (${res.status} ${res.statusText}).`;
        }
        if (data.output) {
          appendLog(data.output + '\n');
        }

        if (data.success) {
          setStatus({
            state: 'success',
            text: `Completed: ${action.toUpperCase()}`,
            activeAction: null,
          });
        } else {
          setStatus({
            state: 'failed',
            text: `Failed: ${action.toUpperCase()}`,
            activeAction: null,
          });
        }
        return data;
      } catch (err) {
        appendLog(`\n[ERROR] Connection failed: ${err.message}\n`);
        setStatus({
          state: 'failed',
          text: `Error connecting to backend (${err.message})`,
          activeAction: null,
        });
        return { success: false, error: err.message };
      }
    },
    [credentials, appendLog]
  );

  const fetchCompare = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/compare`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const fetchBenchmark = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/benchmark`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const fetchSimulation = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/simulation`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const fetchOverview = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/overview`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const fetchHosts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hosts`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/logs`);
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  return {
    credentials,
    updateCredentials,
    status,
    setStatus,
    consoleOutput,
    appendLog,
    clearLog,
    runCommand,
    fetchCompare,
    fetchBenchmark,
    fetchSimulation,
    fetchOverview,
    fetchHosts,
    fetchLogs,
  };
}

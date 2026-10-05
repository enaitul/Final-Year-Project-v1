import React, { useState, useEffect } from 'react';
import {
  Server,
  Play,
  RotateCw,
  Network,
  Globe,
  Shield,
  FolderDown,
  CheckCircle2,
} from 'lucide-react';

export function RemoteExecutionTab({ fetchHosts, runCommand, isRunning }) {
  const [hostsData, setHostsData] = useState({ hosts: [], global_settings: {} });
  const [loading, setLoading] = useState(false);

  const loadHosts = async () => {
    setLoading(true);
    const data = await fetchHosts();
    if (data && data.success) {
      setHostsData({
        hosts: data.hosts || [],
        global_settings: data.global_settings || {},
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    loadHosts();
  }, [fetchHosts]);

  const handleDispatch = async () => {
    await runCommand('remote');
  };

  const hosts = hostsData.hosts.length
    ? hostsData.hosts
    : [
        {
          host_id: 'HOST_01',
          ip_address: '192.168.1.101',
          port: 22,
          username: 'tester',
          auth_type: 'password',
          target_group: 1,
          remote_work_dir: '/opt/testing_framework',
        },
        {
          host_id: 'HOST_02',
          ip_address: '192.168.1.102',
          port: 22,
          username: 'tester',
          auth_type: 'password',
          target_group: 2,
          remote_work_dir: '/opt/testing_framework',
        },
        {
          host_id: 'LOCAL_SIMULATED',
          ip_address: '127.0.0.1',
          port: 22,
          username: 'localhost',
          auth_type: 'local',
          target_group: 3,
          remote_work_dir: '.',
        },
      ];

  const settings = hostsData.global_settings || {
    connection_timeout: 10,
    log_retrieval_dir: 'reports',
    auto_merge_after_remote_execution: true,
  };

  return (
    <div className="tab-content-enter">
      {/* Header and Controls */}
      <div className="glass-card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
              Remote Shell Execution Controller &amp; Target Devices
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
              Dispatches test groups across remote physical/virtual machines via SSH IP addresses, executes isolated test runners, and retrieves response logs back to central storage.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-primary"
              disabled={isRunning || loading}
              onClick={handleDispatch}
            >
              <Play size={16} /> Dispatch Remote Execution
            </button>
            <button
              className="btn btn-glass"
              disabled={loading}
              onClick={loadHosts}
            >
              <RotateCw size={15} className={loading ? 'anim-spin' : ''} /> Reload Config
            </button>
          </div>
        </div>
      </div>

      {/* Global Settings Grid */}
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Connection Timeout
            </span>
            <Globe size={18} color="var(--indigo-400)" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--indigo-400)', marginTop: 8 }}>
            {settings.connection_timeout || 10} Seconds
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            TCP / SSH Socket timeout threshold
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Log Retrieval Target
            </span>
            <FolderDown size={18} color="var(--cyan-400)" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--cyan-400)', marginTop: 8 }}>
            `reports/`
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Central storage for downloaded worker logs
          </div>
        </div>

        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-dim)', fontWeight: 700 }}>
              Auto-Merge & Validate
            </span>
            <CheckCircle2 size={18} color="var(--emerald-400)" />
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--emerald-400)', marginTop: 8 }}>
            Enabled ✅
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: 4 }}>
            Automatically triggers merge_and_validate.py
          </div>
        </div>
      </div>

      {/* Target Devices Table */}
      <div className="glass-card">
        <div className="card-header-flex">
          <div>
            <div className="card-title">
              <Network size={18} color="var(--indigo-400)" /> Target Remote Devices (`remote_hosts.json`)
            </div>
            <div className="card-subtitle">Nodes configured for distributed parallel test execution</div>
          </div>
          <span className="badge badge-neutral">{hosts.length} Hosts Configured</span>
        </div>

        <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#090e18', borderBottom: '1px solid var(--glass-border)', color: 'var(--text-dim)', fontSize: '0.72rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 14px' }}>Host ID</th>
                <th style={{ padding: '12px 14px' }}>IP Address : Port</th>
                <th style={{ padding: '12px 14px' }}>Username</th>
                <th style={{ padding: '12px 14px' }}>Target Group</th>
                <th style={{ padding: '12px 14px' }}>Auth Protocol</th>
                <th style={{ padding: '12px 14px' }}>Remote Working Dir</th>
              </tr>
            </thead>
            <tbody>
              {hosts.map((h, i) => (
                <tr
                  key={i}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    background: i % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                  }}
                >
                  <td style={{ padding: '12px 14px', fontWeight: 700, color: 'var(--indigo-400)', fontFamily: 'JetBrains Mono' }}>
                    {h.host_id}
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'JetBrains Mono', color: 'var(--text-main)' }}>
                    {h.ip_address} : {h.port}
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-muted)' }}>
                    {h.username}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className="badge badge-info">Group {h.target_group}</span>
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span className={`badge ${h.auth_type === 'local' ? 'badge-neutral' : 'badge-warning'}`}>
                      {h.auth_type}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'JetBrains Mono', color: 'var(--text-dim)', fontSize: '0.76rem' }}>
                    {h.remote_work_dir}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

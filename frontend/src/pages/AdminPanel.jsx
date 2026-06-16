import { useState } from "react";
import { Activity, Bug, Cpu, Database, Gauge, Server, Shield } from "lucide-react";
import GlassCard from "../components/common/GlassCard";
import StatusChip from "../components/common/StatusChip";
import { systemStatus } from "../lib/mockData";
import { callJarvis } from "../lib/bridge";

export default function AdminPanel() {
  const [output, setOutput] = useState("No admin action yet.");
  const [debugEnabled, setDebugEnabled] = useState(false);

  const runHealthCheck = async () => {
    const result = await callJarvis("admin.health_check");
    setOutput(result.data?.reply || result.message || "Health check completed.");
  };

  const toggleDebug = async () => {
    const next = !debugEnabled;
    setDebugEnabled(next);

    const result = await callJarvis("admin.toggle_debug", {
      enabled: next,
    });

    setOutput(result.data?.reply || result.message || "Debug setting changed.");
  };

  const openLogs = async () => {
    const result = await callJarvis("admin.open_logs_folder");
    setOutput(result.data?.reply || result.message || "Training_Data folder opened.");
  };

  const clearMemory = async () => {
    const confirmed = window.confirm("Clear saved system memory?");
    if (!confirmed) return;

    const result = await callJarvis("admin.clear_memory");
    setOutput(result.data?.reply || result.message || "Memory cleared.");
  };

  const deleteTrainingData = async () => {
    const confirmed = window.confirm("Delete Training_Data logs?");
    if (!confirmed) return;

    const result = await callJarvis("training.delete");
    setOutput(result.data?.reply || result.message || "Training_Data deleted.");
  };

  return (
    <div className="h-full overflow-y-auto p-container-padding">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Admin Panel</h1>
            <p className="mt-2 text-on-surface-variant">
              System diagnostics and developer controls.
            </p>
          </div>

          <button
            onClick={runHealthCheck}
            className="rounded-lg border border-primary-container/30 bg-primary-container/10 px-4 py-2 text-sm font-semibold text-primary-container hover:shadow-glow-soft"
          >
            Run Health Check
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4">
          {[
            ["AI", systemStatus.ai, Server],
            ["Model", systemStatus.model, Activity],
            ["CPU", systemStatus.cpu, Cpu],
            ["RAM", systemStatus.ram, Gauge],
          ].map(([label, value, Icon]) => (
            <GlassCard key={label}>
              <Icon className="text-primary-container" />
              <p className="mono-label mt-4 text-on-surface-variant">{label}</p>
              <p className="mono-data mt-2 text-primary">{value}</p>
            </GlassCard>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <GlassCard>
            <div className="mb-5 flex items-center gap-3">
              <Database className="text-primary-container" />
              <h2 className="text-lg font-semibold">Training_Data</h2>
              <StatusChip tone="success">ACTIVE</StatusChip>
            </div>

            <div className="space-y-3 mono-data text-on-surface-variant">
              <p>Sessions: logging enabled</p>
              <p>AI routes: logging enabled</p>
              <p>Memory changes: logging enabled</p>
              <p>Voice events: logging enabled</p>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="mb-5 flex items-center gap-3">
              <Bug className="text-primary-container" />
              <h2 className="text-lg font-semibold">Debug Controls</h2>
            </div>

            <div className="space-y-3">
              <button
                onClick={toggleDebug}
                className="w-full rounded-lg border border-white/10 p-3 text-left hover:bg-white/5"
              >
                {debugEnabled ? "Disable AI route debug" : "Enable AI route debug"}
              </button>
              <button
                onClick={openLogs}
                className="w-full rounded-lg border border-white/10 p-3 text-left hover:bg-white/5"
              >
                Open Training_Data folder
              </button>
              <button
                onClick={clearMemory}
                className="w-full rounded-lg border border-danger/30 p-3 text-left text-danger hover:bg-danger/10"
              >
                Clear local memory
              </button>
            </div>
          </GlassCard>
        </div>

        <GlassCard>
          <div className="mb-5 flex items-center gap-3">
            <Shield className="text-primary-container" />
            <h2 className="text-lg font-semibold">Admin Output</h2>
          </div>

          <pre className="max-h-64 overflow-auto rounded-lg border border-white/10 bg-black/30 p-4 mono-data text-on-surface-variant whitespace-pre-wrap">
            {output}
          </pre>

          <button
            onClick={deleteTrainingData}
            className="mt-4 rounded-lg border border-danger/30 px-4 py-2 text-danger hover:bg-danger/10"
          >
            Delete Training_Data
          </button>
        </GlassCard>
      </div>
    </div>
  );
}
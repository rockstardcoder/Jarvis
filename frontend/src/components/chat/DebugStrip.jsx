import { Bug, Timer } from "lucide-react";
import { debugState } from "../../lib/mockData";
import StatusChip from "../common/StatusChip";

export default function DebugStrip() {
  return (
    <div className="glass-panel-soft flex items-center justify-between rounded-xl px-4 py-3">
      <div className="flex items-center gap-3">
        <Bug size={16} className="text-primary-container" />
        <span className="mono-label text-on-surface-variant">DEBUG</span>
        <span className="mono-data text-on-surface">
          {debugState.tool} → {debugState.action} → {debugState.target}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1 mono-data text-on-surface-variant">
          <Timer size={14} />
          {debugState.duration}
        </span>
        <StatusChip tone="success">{debugState.status}</StatusChip>
      </div>
    </div>
  );
}
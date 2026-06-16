import { Cloud, Cpu, Sparkles, Zap } from "lucide-react";
import GlassCard from "../components/common/GlassCard";
import StatusChip from "../components/common/StatusChip";

export default function PlansPage() {
  return (
    <div className="h-full overflow-y-auto p-container-padding">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Plans</h1>
          <p className="mt-2 text-on-surface-variant">Jarvis is currently running in local-first Free mode.</p>
        </div>

        <GlassCard className="border-primary-container/20">
          <div className="flex items-start justify-between gap-6">
            <div>
              <StatusChip tone="success">CURRENT PLAN</StatusChip>
              <h2 className="mt-4 text-2xl font-semibold">Free Local Plan</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-on-surface-variant">
                Local Jarvis assistant with Ollama support, voice input/output, Windows automation,
                Training_Data logs, and optional user-provided API keys later.
              </p>
            </div>
            <div className="rounded-xl border border-primary-container/20 bg-primary-container/10 p-4 text-primary-container">
              <Cpu size={38} />
            </div>
          </div>
        </GlassCard>

        <div className="grid grid-cols-3 gap-4">
          {[
            ["Cloud Sync", "Coming later", Cloud],
            ["Creator Upgrade", "Update 1.2", Sparkles],
            ["Automation Packs", "Coming later", Zap],
          ].map(([title, status, Icon]) => (
            <GlassCard key={title}>
              <Icon className="text-primary-container" />
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-on-surface-variant">{status}</p>
            </GlassCard>
          ))}
        </div>
      </div>
    </div>
  );
}
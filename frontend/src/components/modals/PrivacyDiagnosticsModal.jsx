import { Shield } from "lucide-react";

export default function PrivacyDiagnosticsModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-background/80 p-6 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-xl rounded-xl shadow-glow-soft">
        <div className="flex items-center gap-3 border-b border-white/10 px-6 py-4">
          <Shield className="text-primary-container" />
          <h2 className="text-xl font-semibold">Diagnostics & Privacy</h2>
        </div>

        <div className="space-y-4 px-6 py-5 text-sm leading-6 text-on-surface-variant">
          <p>
            Jarvis stores Training_Data locally to help debug commands, improve routing,
            and diagnose errors. Uploads are optional and disabled by default.
          </p>

          <div className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
            <p className="font-semibold text-on-surface">Saved locally:</p>
            <p>Commands, tool routes, tool results, errors, voice text, timings, settings snapshots, and memory changes.</p>
          </div>

          <div className="rounded-lg border border-warning/20 bg-warning/5 p-4">
            <p className="font-semibold text-warning">Sensitive data:</p>
            <p>API keys, passwords, tokens, and emails are redacted where possible. Always review logs before sharing.</p>
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-white/10 px-6 py-4">
          <button onClick={onClose} className="rounded-lg border border-white/10 px-4 py-2 hover:bg-white/5">
            Keep Disabled
          </button>
          <button onClick={onClose} className="rounded-lg bg-primary-container px-4 py-2 font-semibold text-background hover:shadow-glow">
            I Understand
          </button>
        </div>
      </div>
    </div>
  );
}
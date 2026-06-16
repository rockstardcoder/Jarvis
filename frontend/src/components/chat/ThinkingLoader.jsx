export default function ThinkingLoader() {
  return (
    <div className="flex w-full justify-start">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-primary-container/30 bg-primary-container/10 shadow-glow-soft">
          <div className="h-4 w-4 rounded-full bg-gradient-to-br from-primary-container via-primary-blue to-primary-green animate-pulse" />
        </div>

        <div className="glass-panel rounded-2xl rounded-tl-md px-5 py-4">
          <div className="jarvis-thinking-loader">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="mt-3 text-xs font-semibold uppercase tracking-[0.22em] text-secondary">
            Jarvis is thinking
          </div>
        </div>
      </div>
    </div>
  );
}
export default function ToggleSwitch({ checked, onChange, label, description }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-white/10 bg-white/[0.025] p-4">
      <div>
        <p className="font-semibold text-primary">{label}</p>
        {description && (
          <p className="mt-1 text-sm text-secondary">{description}</p>
        )}
      </div>

      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={[
          "relative h-8 w-14 shrink-0 rounded-full border transition-all duration-300",
          checked
            ? "border-primary-container/50 bg-primary-container/20 shadow-glow-soft"
            : "border-white/15 bg-surface-raised",
        ].join(" ")}
      >
        <span
          className={[
            "absolute top-1 h-6 w-6 rounded-full transition-all duration-300",
            checked
              ? "left-7 core-gradient shadow-glow"
              : "left-1 bg-muted",
          ].join(" ")}
        />
      </button>
    </div>
  );
}
export default function StatusChip({ children, tone = "neutral" }) {
  const tones = {
    neutral: "border-white/10 bg-white/5 text-on-surface-variant",
    active: "border-primary-container/30 bg-primary-container/10 text-primary-container shadow-glow-soft",
    success: "border-success/30 bg-success/10 text-success",
    warning: "border-warning/30 bg-warning/10 text-warning",
    danger: "border-danger/30 bg-danger/10 text-danger",
  };

  return (
    <span className={`mono-label inline-flex items-center rounded-full border px-2.5 py-1 ${tones[tone]}`}>
      {children}
    </span>
  );
}
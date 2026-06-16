export default function IconButton({ icon: Icon, label, active = false, danger = false, onClick }) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={[
        "no-drag flex h-10 w-10 items-center justify-center rounded-lg border transition-all active:scale-95",
        active
          ? "border-primary-container/30 bg-primary-container/10 text-primary-container shadow-glow-soft"
          : "border-white/10 bg-white/5 text-on-surface-variant hover:bg-white/10 hover:text-primary",
        danger ? "hover:border-danger/40 hover:text-danger" : "",
      ].join(" ")}
    >
      <Icon size={18} strokeWidth={1.8} />
    </button>
  );
}
export default function GlassCard({ children, className = "" }) {
  return (
    <section className={`glass-panel rounded-xl p-6 ${className}`}>
      {children}
    </section>
  );
}
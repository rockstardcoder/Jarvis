export default function JarvisLogo({ size = "md", showText = true }) {
  const sizes = {
    sm: {
      box: "h-9 w-9",
      title: "text-lg",
      sub: "text-[10px]",
      radius: "rounded-xl",
    },
    md: {
      box: "h-12 w-12",
      title: "text-2xl",
      sub: "text-xs",
      radius: "rounded-2xl",
    },
    lg: {
      box: "h-16 w-16",
      title: "text-3xl",
      sub: "text-sm",
      radius: "rounded-[24px]",
    },
  };

  const current = sizes[size] || sizes.md;

  return (
    <div className="flex items-center gap-3">
      <div
        className={[
          "relative shrink-0 overflow-hidden",
          current.box,
          current.radius,
          "bg-[linear-gradient(135deg,#10B981_0%,#22D3EE_42%,#3B82F6_100%)]",
          "shadow-[0_0_30px_rgba(34,211,238,0.36)]",
          "ring-1 ring-cyan-300/30",
        ].join(" ")}
      >
        <div className="absolute inset-[7px] rounded-[10px] bg-background/82" />
        <div className="absolute left-[17%] top-[16%] h-[32%] w-[70%] rotate-45 rounded-full bg-cyan-200/35 blur-[1px]" />
        <div className="absolute bottom-[12%] left-[15%] h-[22%] w-[55%] -rotate-45 rounded-full bg-emerald-300/35 blur-[1px]" />
        <div className="absolute inset-0 rounded-[inherit] bg-white/5" />
      </div>

      {showText && (
        <div className="leading-none">
          <div className={`${current.title} font-semibold tracking-[0.18em] text-primary`}>
            JARVIS
          </div>
          <div className={`${current.sub} mt-1 font-medium tracking-[0.32em] core-text-gradient`}>
            CORE
          </div>
        </div>
      )}
    </div>
  );
}
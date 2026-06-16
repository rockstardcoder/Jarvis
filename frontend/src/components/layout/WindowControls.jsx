import { Minus, Square, X } from "lucide-react";

export default function WindowControls() {
  return (
    <div className="no-drag flex items-center gap-2 text-on-surface-variant">
      <button className="rounded-md p-1.5 hover:bg-white/5 hover:text-primary active:scale-95">
        <Minus size={16} />
      </button>
      <button className="rounded-md p-1.5 hover:bg-white/5 hover:text-primary active:scale-95">
        <Square size={14} />
      </button>
      <button className="rounded-md p-1.5 hover:bg-danger/10 hover:text-danger active:scale-95">
        <X size={16} />
      </button>
    </div>
  );
}
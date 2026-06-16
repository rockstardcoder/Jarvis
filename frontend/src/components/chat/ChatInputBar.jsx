import { ChevronDown, Keyboard, Mic, Send, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import VoiceActivityMeter from "./VoiceActivityMeter";

function getCollapseMode() {
  return localStorage.getItem("jarvis.text_input.collapse_mode") || "delay";
}

export default function ChatInputBar({
  value,
  setValue,
  onSend,
  selectedModel,
  setSelectedModel,
  modelOptions,
  micState,
  onMicClick,
  voiceStatus,
}) {
  const inputRef = useRef(null);
  const collapseTimerRef = useRef(null);

  const [expanded, setExpanded] = useState(false);
  const [collapseMode, setCollapseMode] = useState(getCollapseMode);

  const listening = micState === "continuous";

  useEffect(() => {
    const handler = () => {
      setCollapseMode(getCollapseMode());
    };

    window.addEventListener("jarvis:text-input-settings-changed", handler);

    return () => {
      window.removeEventListener("jarvis:text-input-settings-changed", handler);
    };
  }, []);

  useEffect(() => {
    const keyboardHandler = (event) => {
      const key = event.key.toLowerCase();

      if ((event.ctrlKey && key === "k") || key === "/") {
        event.preventDefault();
        openInput();
      }

      if (event.key === "Escape" && expanded) {
        event.preventDefault();
        closeInput();
      }
    };

    window.addEventListener("keydown", keyboardHandler);

    return () => {
      window.removeEventListener("keydown", keyboardHandler);
    };
  }, [expanded]);

  const openInput = () => {
    clearTimeout(collapseTimerRef.current);
    setExpanded(true);

    setTimeout(() => {
      inputRef.current?.focus();
    }, 180);
  };

  const closeInput = () => {
    clearTimeout(collapseTimerRef.current);
    setExpanded(false);
  };

  const submit = () => {
    const clean = value.trim();
    if (!clean) return;

    onSend(clean);
    setValue("");

    if (collapseMode === "delay") {
      clearTimeout(collapseTimerRef.current);

      collapseTimerRef.current = setTimeout(() => {
        setExpanded(false);
      }, 3000);
    }
  };

  const VoiceStatusBlock = (
    <div className="flex flex-col items-center gap-2 sm:flex-row">
      <VoiceActivityMeter active={listening} />

      <div className="rounded-full border border-white/10 bg-background/70 px-4 py-2 text-center text-xs text-secondary shadow-glow-soft backdrop-blur-xl">
        {voiceStatus || "Listening for “Hey Jarvis” or “Wake up Jarvis”"}
      </div>
    </div>
  );

  if (!expanded) {
    return (
      <div className="flex w-full flex-col items-center gap-3">
        {VoiceStatusBlock}

        <button
          onClick={openInput}
          className="jarvis-text-input-shell jarvis-text-input-collapsed jarvis-secondary-input-button group flex h-14 items-center justify-center rounded-full border border-primary-container/30 text-primary-container shadow-glow-soft hover:border-primary-container/60 hover:shadow-glow active:scale-95"
          title="Open text input"
        >
          <Keyboard size={22} className="transition-transform group-hover:scale-110" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex w-full flex-col items-center gap-3">
      {VoiceStatusBlock}

      <div className="jarvis-text-input-shell jarvis-text-input-expanded glass-panel flex min-w-0 items-center gap-2 rounded-2xl p-2.5">
        <div className="relative shrink-0">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="h-11 w-[170px] appearance-none rounded-xl border border-white/10 bg-surface-card px-3 pr-8 text-sm text-primary outline-none focus:border-primary-container/40"
          >
            {modelOptions.map((model) => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>

          <ChevronDown
            size={15}
            className="pointer-events-none absolute right-2.5 top-3.5 text-secondary"
          />
        </div>

        <input
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          placeholder="Ask Jarvis anything..."
          className="h-11 min-w-0 flex-1 rounded-xl border border-white/10 bg-surface-soft px-4 text-sm text-primary outline-none placeholder:text-muted focus:border-primary-container/40 focus:shadow-glow-soft"
        />

        <button
          onClick={onMicClick}
          title={listening ? "Voice listening active" : "Start listening"}
          className={[
            "relative flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition-all active:scale-95",
            listening
              ? "border-primary-container/50 bg-primary-container/15 text-primary-container shadow-glow"
              : "border-white/10 bg-white/5 text-secondary hover:text-primary-container",
          ].join(" ")}
        >
          {listening && (
            <span className="absolute inset-[-3px] rounded-xl border border-primary-container/50 animate-ping" />
          )}

          <Mic size={19} />
        </button>

        <button
          onClick={submit}
          className="core-gradient flex h-11 shrink-0 items-center gap-2 rounded-xl px-4 font-semibold text-background transition-all hover:shadow-glow active:scale-95"
        >
          <Send size={19} />
          <span>Send</span>
        </button>

        <button
          onClick={closeInput}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-secondary transition hover:text-danger"
          title="Close text input"
        >
          <X size={19} />
        </button>
      </div>
    </div>
  );
}
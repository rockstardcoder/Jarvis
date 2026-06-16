import { MessageCircle, Mic, Settings, Volume2 } from "lucide-react";
import JarvisLogo from "../common/JarvisLogo";
import { callJarvis } from "../../lib/bridge";

export default function FloatingWidget({ activePage, onOpen, onSettings }) {
  const isChat = activePage === "chat";

  const widgetPosition = isChat
    ? "bottom-[112px] right-6"
    : "bottom-6 right-6";

  const listenOnce = async () => {
    await callJarvis("voice.listen_once");
  };

  const voiceOn = async () => {
    await callJarvis("voice.set_audio_output", {
      enabled: true,
    });
  };

  return (
    <div
      className={`fixed ${widgetPosition} z-50 scale-[0.9] origin-bottom-right transition-all duration-300 ease-out`}
    >
      <div className="glass-panel flex items-center gap-3 rounded-full px-4 py-2 shadow-glow-soft">
        <button
          onClick={onOpen}
          title="Open Chat"
          className="flex h-10 w-10 items-center justify-center rounded-full"
        >
          <JarvisLogo size="sm" showText={false} />
        </button>

        <button
          onClick={listenOnce}
          title="Listen once"
          className="mic-pulse flex h-10 w-10 items-center justify-center rounded-full border border-primary-container/30 bg-primary-container/10 text-primary-container"
        >
          <Mic size={18} />
        </button>

        <button
          onClick={voiceOn}
          title="Voice output on"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-secondary hover:text-primary-container"
        >
          <Volume2 size={18} />
        </button>

        <button
          onClick={onOpen}
          title="Open Chat"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-secondary hover:text-primary-container"
        >
          <MessageCircle size={18} />
        </button>

        <button
          onClick={onSettings}
          title="Open Settings"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/5 text-secondary hover:text-primary-container"
        >
          <Settings size={18} />
        </button>
      </div>
    </div>
  );
}
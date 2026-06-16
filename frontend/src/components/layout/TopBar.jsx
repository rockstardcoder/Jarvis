import { Activity, Circle, Cpu, Mic } from "lucide-react";
import { useEffect, useState } from "react";
import StatusChip from "../common/StatusChip";
import { callJarvis } from "../../lib/bridge";

function providerLabel(provider) {
  if (provider === "openai") return "ChatGPT Mode";
  if (provider === "gemini") return "Gemini Mode";
  return "Local Mode";
}

export default function TopBar() {
  const [provider, setProvider] = useState("llama");

  useEffect(() => {
    async function loadProvider() {
      const result = await callJarvis("ai_provider.get");
      if (result.ok && result.data?.active_provider) {
        setProvider(result.data.active_provider);
      }
    }

    loadProvider();

    const handler = (event) => {
      if (event.detail?.provider) {
        setProvider(event.detail.provider);
      } else {
        loadProvider();
      }
    };

    window.addEventListener("jarvis:provider-changed", handler);

    return () => {
      window.removeEventListener("jarvis:provider-changed", handler);
    };
  }, []);

  return (
    <header className="fixed left-[280px] right-0 top-0 z-30 flex h-16 items-center justify-between border-b border-white/10 bg-background/70 px-7 backdrop-blur-2xl">
      <div className="flex items-center gap-4">
        <div className="core-gradient flex h-10 w-10 items-center justify-center rounded-full shadow-glow-soft">
          <Activity size={20} className="text-background" />
        </div>

        <div>
          <h2 className="font-semibold text-primary">Good morning, CoderBoiii.</h2>
          <p className="text-sm text-secondary">How can Jarvis help today?</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <StatusChip tone="success">
          <Circle size={8} className="fill-success text-success" />
          AI Online
        </StatusChip>

        <StatusChip tone="active">
          <Mic size={14} />
          Voice Ready
        </StatusChip>

        <StatusChip tone="neutral">
          <Cpu size={14} />
          {providerLabel(provider)}
        </StatusChip>
      </div>
    </header>
  );
}
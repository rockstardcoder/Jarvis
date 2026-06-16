import { useEffect, useState } from "react";
import { Bot, FolderOpen, KeyRound, Volume2 } from "lucide-react";
import GlassCard from "../components/common/GlassCard";
import StatusChip from "../components/common/StatusChip";
import ToggleSwitch from "../components/common/ToggleSwitch";
import { callJarvis } from "../lib/bridge";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    voice: {
      audio_output: true,
      continuous_listening: false,
      do_not_speak_errors: true,
    },
    folders: {},
  });

  const [providers, setProviders] = useState({
    active_provider: "llama",
    providers: {},
  });

  const [apiKeys, setApiKeys] = useState({
    gemini: "",
    openai: "",
  });

  const [status, setStatus] = useState("Ready.");

  useEffect(() => {
    loadSettings();
    loadProviders();
  }, []);

  const loadSettings = async () => {
    const result = await callJarvis("settings.get");

    if (result.ok && result.data) {
      setSettings(result.data);
    }
  };

  const loadProviders = async () => {
    const result = await callJarvis("ai_provider.get");

    if (result.ok && result.data) {
      setProviders(result.data);

      window.dispatchEvent(
        new CustomEvent("jarvis:provider-changed", {
          detail: {
            provider: result.data.active_provider,
          },
        })
      );
    }
  };

  const setVoiceToggle = async (key, value) => {
    setSettings((current) => ({
      ...current,
      voice: {
        ...current.voice,
        [key]: value,
      },
    }));

    const commandMap = {
      audio_output: "voice.set_audio_output",
      continuous_listening: "voice.set_continuous_listening",
      do_not_speak_errors: "voice.set_silent_errors",
    };

    const result = await callJarvis(commandMap[key], {
      enabled: value,
    });

    setStatus(result.data?.reply || result.message || "Voice setting saved.");
  };

  const selectProvider = async (provider) => {
    const result = await callJarvis("ai_provider.select", {
      provider,
    });

    setStatus(result.message || "Provider selection complete.");

    if (result.ok) {
      await loadProviders();
    }
  };

  const saveApiKey = async (provider) => {
    const key = apiKeys[provider];

    if (!key.trim()) {
      setStatus("API key cannot be empty.");
      return;
    }

    const saveResult = await callJarvis("ai_provider.set_api_key", {
      provider,
      api_key: key,
    });

    if (!saveResult.ok) {
      setStatus(saveResult.message || "API key save failed.");
      return;
    }

    setApiKeys((current) => ({
      ...current,
      [provider]: "",
    }));

    const selectResult = await callJarvis("ai_provider.select", {
      provider,
    });

    setStatus(selectResult.message || "API key saved and provider selected.");

    await loadProviders();
  };

  const clearApiKey = async (provider) => {
    const confirmed = window.confirm(`Clear ${provider} API key?`);
    if (!confirmed) return;

    const result = await callJarvis("ai_provider.clear_api_key", {
      provider,
    });

    setStatus(result.message || "API key cleared.");

    if (result.ok) {
      await loadProviders();
    }
  };

  const updateProviderModel = async (provider, model) => {
    const result = await callJarvis("ai_provider.update_config", {
      provider,
      model,
    });

    setStatus(result.message || "Provider model saved.");

    if (result.ok) {
      await loadProviders();
    }
  };

  const openFolder = async (folder) => {
    const result = await callJarvis("folder.open", { folder });
    setStatus(result.data?.reply || result.message || "Folder opened.");
  };

  const changeFolder = async (folder) => {
    const result = await callJarvis("folder.choose", { folder });

    if (result.ok && result.data?.settings) {
      setSettings(result.data.settings);
    }

    setStatus(result.data?.reply || result.message || "Folder selection finished.");
  };

  const folders = [
    ["screenshots", "Screenshots"],
    ["documents", "Documents"],
    ["presentations", "Presentations"],
    ["pdf", "PDF"],
    ["training_data", "Training_Data"],
    ["notes", "Notes"],
  ];

  const providerCards = [
    ["llama", "Llama / Ollama", "Local AI running on your PC"],
    ["gemini", "Gemini", "Google Gemini API"],
    ["openai", "ChatGPT / OpenAI", "OpenAI API compatible"],
  ];

  return (
    <div className="h-full overflow-y-auto p-container-padding">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
          <p className="mt-2 text-secondary">
            Manage AI providers, voice, and output folders.
          </p>
          <p className="mono-data mt-3 text-primary-container">{status}</p>
        </div>

        <GlassCard>
          <div className="mb-5 flex items-center gap-3">
            <Bot className="text-primary-container" />
            <h2 className="text-lg font-semibold">AI Providers</h2>
            <StatusChip tone="active">
              ACTIVE {providers.active_provider?.toUpperCase()}
            </StatusChip>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {providerCards.map(([id, title, description]) => {
              const provider = providers.providers?.[id] || {};
              const active = providers.active_provider === id;

              return (
                <div
                  key={id}
                  className={[
                    "rounded-xl border p-4 transition-all",
                    active
                      ? "border-primary-container/40 bg-primary-container/10 shadow-glow-soft"
                      : "border-white/10 bg-white/[0.03]",
                  ].join(" ")}
                >
                  <p className="font-semibold">{title}</p>
                  <p className="mt-1 text-sm text-secondary">{description}</p>

                  <div className="mt-4 space-y-2 mono-data text-secondary">
                    <p>Model: {provider.model || "Not set"}</p>
                    <p>API key: {provider.api_key_set ? "Saved" : "Not saved"}</p>
                  </div>

                  <input
                    className="auth-input mt-4"
                    value={provider.model || ""}
                    onChange={(e) => {
                      setProviders((current) => ({
                        ...current,
                        providers: {
                          ...current.providers,
                          [id]: {
                            ...current.providers[id],
                            model: e.target.value,
                          },
                        },
                      }));
                    }}
                    onBlur={(e) => updateProviderModel(id, e.target.value)}
                    placeholder="Model name"
                  />

                  {id !== "llama" && (
                    <div className="mt-3 space-y-2">
                      <input
                        className="auth-input"
                        type="password"
                        value={apiKeys[id] || ""}
                        onChange={(e) =>
                          setApiKeys((current) => ({
                            ...current,
                            [id]: e.target.value,
                          }))
                        }
                        placeholder={`${title} API key`}
                      />

                      <button
                        onClick={() => saveApiKey(id)}
                        className="w-full rounded-lg border border-primary-container/30 px-3 py-2 text-sm text-primary-container hover:bg-primary-container/10"
                      >
                        Save API Key & Select
                      </button>

                      <button
                        onClick={() => clearApiKey(id)}
                        className="w-full rounded-lg border border-danger/30 px-3 py-2 text-sm text-danger hover:bg-danger/10"
                      >
                        Clear API Key
                      </button>
                    </div>
                  )}

                  <button
                    onClick={() => selectProvider(id)}
                    className="mt-4 w-full rounded-lg bg-primary-container px-3 py-2 font-semibold text-background hover:shadow-glow"
                  >
                    Select {title}
                  </button>
                </div>
              );
            })}
          </div>

          <div className="mt-5 rounded-lg border border-warning/20 bg-warning/5 p-4 text-sm text-secondary">
            <KeyRound className="mr-2 inline text-warning" size={16} />
            API keys are saved locally using Windows-local encryption and are not shown again.
          </div>
        </GlassCard>

        <GlassCard>
          <div className="mb-5 flex items-center gap-3">
            <Volume2 className="text-primary-container" />
            <h2 className="text-lg font-semibold">Voice</h2>
          </div>

          <div className="space-y-3">
            <ToggleSwitch
              checked={settings.voice?.audio_output}
              onChange={(value) => setVoiceToggle("audio_output", value)}
              label="Audio output"
              description="Allow Jarvis to speak responses."
            />
            <ToggleSwitch
              checked={settings.voice?.continuous_listening}
              onChange={(value) => setVoiceToggle("continuous_listening", value)}
              label="Continuous listening"
              description="Keep listening in background."
            />
            <ToggleSwitch
              checked={settings.voice?.do_not_speak_errors}
              onChange={(value) => setVoiceToggle("do_not_speak_errors", value)}
              label="Do not speak errors"
              description="Errors remain visible but not spoken."
            />
          </div>
        </GlassCard>

        <GlassCard>
          <div className="mb-5 flex items-center gap-3">
            <FolderOpen className="text-primary-container" />
            <h2 className="text-lg font-semibold">Output Folders</h2>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {folders.map(([folderKey, folderLabel]) => (
              <div key={folderKey} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                <p className="font-semibold">{folderLabel}</p>
                <p className="mono-data mt-2 truncate text-secondary">
                  {settings.folders?.[folderKey] || "Not set"}
                </p>

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => openFolder(folderKey)}
                    className="rounded-lg border border-white/10 px-3 py-2 text-xs hover:bg-white/5"
                  >
                    Open
                  </button>

                  <button
                    onClick={() => changeFolder(folderKey)}
                    className="rounded-lg border border-primary-container/30 px-3 py-2 text-xs text-primary-container hover:bg-primary-container/10"
                  >
                    Change
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
import { useEffect, useRef, useState } from "react";
import { ArrowDown } from "lucide-react";
import ChatBubble from "../components/chat/ChatBubble";
import ChatInputBar from "../components/chat/ChatInputBar";
import DebugStrip from "../components/chat/DebugStrip";
import StatusChip from "../components/common/StatusChip";
import ThinkingLoader from "../components/chat/ThinkingLoader";
import { initialMessages } from "../lib/mockData";
import { callJarvis } from "../lib/bridge";

const DEFAULT_CHAT_ID = "default";
const WAKE_PHRASES = ["hey jarvis", "wake up jarvis", "wakeup jarvis"];
const SLEEP_PHRASES = ["sleep jarvis", "exit jarvis"];

function getChatKey(chatId) {
  return `jarvis.chat.history.${chatId || DEFAULT_CHAT_ID}`;
}

function getConversationList() {
  try {
    const saved = localStorage.getItem("jarvis.chat.conversations");
    const parsed = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function upsertConversation(conversation) {
  let conversations = getConversationList();

  const existingIndex = conversations.findIndex((item) => item.id === conversation.id);

  if (existingIndex >= 0) {
    conversations[existingIndex] = {
      ...conversations[existingIndex],
      ...conversation,
    };
  } else {
    conversations = [conversation, ...conversations];
  }

  conversations = conversations.slice(0, 20);

  localStorage.setItem("jarvis.chat.conversations", JSON.stringify(conversations));
  localStorage.setItem("jarvis.active.chat.id", conversation.id);
  window.dispatchEvent(new CustomEvent("jarvis:conversations-updated"));
}

function loadHistory(chatId) {
  try {
    const saved = localStorage.getItem(getChatKey(chatId));
    if (saved) return JSON.parse(saved);
  } catch {
    // ignore
  }

  if (chatId === DEFAULT_CHAT_ID) return initialMessages;
  return [];
}

function saveHistory(chatId, messages) {
  localStorage.setItem(getChatKey(chatId), JSON.stringify(messages));
}

function makeChatTitle(text) {
  const clean = String(text || "").trim();
  if (!clean) return "New Chat";
  return clean.length > 34 ? `${clean.slice(0, 34)}...` : clean;
}

function containsWakePhrase(text) {
  const clean = String(text || "").toLowerCase();
  return WAKE_PHRASES.some((phrase) => clean.includes(phrase));
}

function containsSleepPhrase(text) {
  const clean = String(text || "").toLowerCase();
  return SLEEP_PHRASES.some((phrase) => clean.includes(phrase));
}

function removeWakePhrase(text) {
  let clean = String(text || "").trim();

  for (const phrase of WAKE_PHRASES) {
    clean = clean.replace(new RegExp(phrase, "i"), "").trim();
  }

  return clean;
}

export default function ChatPage() {
  const scrollBoxRef = useRef(null);
  const endRef = useRef(null);
  const listeningRef = useRef(false);
  const messagesRef = useRef([]);
  const chatIdRef = useRef(DEFAULT_CHAT_ID);

  const [chatId, setChatId] = useState(() => {
    return localStorage.getItem("jarvis.active.chat.id") || DEFAULT_CHAT_ID;
  });

  const [messages, setMessages] = useState(() => {
    const activeId = localStorage.getItem("jarvis.active.chat.id") || DEFAULT_CHAT_ID;
    const loaded = loadHistory(activeId);
    messagesRef.current = loaded;
    chatIdRef.current = activeId;
    return loaded;
  });

  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("llama:llama3.1:8b");
  const [modelOptions, setModelOptions] = useState([
    {
      value: "llama:llama3.1:8b",
      label: "Llama",
    },
  ]);

  const [micState, setMicState] = useState("continuous");
  const [voiceStatus, setVoiceStatus] = useState(
    "Listening for “Hey Jarvis” or “Wake up Jarvis”"
  );
  const [isRunning, setIsRunning] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);

  useEffect(() => {
    messagesRef.current = messages;
    saveHistory(chatId, messages);
  }, [messages, chatId]);

  useEffect(() => {
    chatIdRef.current = chatId;
  }, [chatId]);

  useEffect(() => {
    const newChatHandler = (event) => {
      const conversation =
        event.detail || {
          id: `chat-${Date.now()}`,
          title: "New Chat",
          time: "Now",
        };

      setChatId(conversation.id);
      chatIdRef.current = conversation.id;
      setMessages([]);
      messagesRef.current = [];

      localStorage.setItem("jarvis.active.chat.id", conversation.id);
      saveHistory(conversation.id, []);
      setTimeout(() => scrollToBottom(false), 50);
    };

    const openChatHandler = (event) => {
      const conversation = event.detail;
      if (!conversation?.id) return;

      const loaded = loadHistory(conversation.id);

      setChatId(conversation.id);
      chatIdRef.current = conversation.id;
      setMessages(loaded);
      messagesRef.current = loaded;

      localStorage.setItem("jarvis.active.chat.id", conversation.id);
      setTimeout(() => scrollToBottom(false), 50);
    };

    window.addEventListener("jarvis:new-chat", newChatHandler);
    window.addEventListener("jarvis:open-chat", openChatHandler);

    return () => {
      window.removeEventListener("jarvis:new-chat", newChatHandler);
      window.removeEventListener("jarvis:open-chat", openChatHandler);
    };
  }, []);

  useEffect(() => {
    loadProviders();

    const providerHandler = () => loadProviders();
    window.addEventListener("jarvis:provider-changed", providerHandler);

    return () => {
      window.removeEventListener("jarvis:provider-changed", providerHandler);
    };
  }, []);

  useEffect(() => {
    if (isAtBottom) scrollToBottom(false);
  }, [messages, isAtBottom, isRunning]);

  useEffect(() => {
    startAutoWakeListening();

    return () => {
      listeningRef.current = false;
    };
  }, []);

  const loadProviders = async () => {
    const result = await callJarvis("ai_provider.get");

    if (!result.ok || !result.data?.providers) return;

    const providers = result.data.providers;

    const options = Object.entries(providers).map(([key, provider]) => ({
      value: `${key}:${provider.model || provider.label}`,
      label:
        key === "openai"
          ? "ChatGPT"
          : key === "gemini"
            ? "Gemini"
            : "Llama",
    }));

    setModelOptions(options);

    const active = result.data.active_provider || "llama";
    const activeProvider = providers[active];

    if (activeProvider) {
      setSelectedModel(`${active}:${activeProvider.model || activeProvider.label}`);
    }
  };

  const scrollToBottom = (smooth = true) => {
    endRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "auto",
      block: "end",
    });
  };

  const handleScroll = () => {
    const box = scrollBoxRef.current;
    if (!box) return;

    const distanceFromBottom = box.scrollHeight - box.scrollTop - box.clientHeight;
    setIsAtBottom(distanceFromBottom < 120);
  };

  const ensureConversationForMessage = (text) => {
    let activeId = chatIdRef.current;

    if (!activeId || activeId === DEFAULT_CHAT_ID) {
      activeId = `chat-${Date.now()}`;
      setChatId(activeId);
      chatIdRef.current = activeId;
    }

    upsertConversation({
      id: activeId,
      title: makeChatTitle(text),
      time: "Now",
    });

    return activeId;
  };

  const appendMessage = (activeChatId, message) => {
    const finalMessage = {
      id: Date.now() + Math.random(),
      ...message,
    };

    const nextMessages = [...messagesRef.current, finalMessage];

    messagesRef.current = nextMessages;
    setMessages(nextMessages);
    saveHistory(activeChatId, nextMessages);

    return finalMessage;
  };

  const handleModelChange = async (value) => {
    setSelectedModel(value);

    const provider = value.split(":")[0];

    const result = await callJarvis("ai_provider.select", {
      provider,
    });

    if (result.ok) {
      window.dispatchEvent(
        new CustomEvent("jarvis:provider-changed", {
          detail: { provider },
        })
      );
    } else {
      await loadProviders();
    }
  };

  const sendCommandText = async (text, meta = undefined) => {
    const activeChatId = ensureConversationForMessage(text);

    appendMessage(activeChatId, {
      role: "user",
      text,
      meta,
    });

    setIsRunning(true);
    setVoiceStatus("Jarvis is processing...");
    setTimeout(() => scrollToBottom(true), 50);

    const provider = selectedModel.split(":")[0];

    window.dispatchEvent(
      new CustomEvent("jarvis:provider-changed", {
        detail: { provider },
      })
    );

    const result = await callJarvis("chat.send", {
      text,
      model: selectedModel,
    });

    appendMessage(activeChatId, {
      role: "assistant",
      text: result.ok
        ? result.data?.reply || result.message || "Command completed."
        : result.message || "Command failed.",
      meta: result.data?.meta || (result.ok ? "JARVIS RUNTIME / CONNECTED" : "BRIDGE ERROR"),
    });

    setIsRunning(false);
    setVoiceStatus("Listening for “Hey Jarvis” or “Wake up Jarvis”");
    setTimeout(() => scrollToBottom(true), 80);
  };

  const onSend = async (text) => {
    await sendCommandText(text);
  };

  const listenRaw = async () => {
    const result = await callJarvis("voice.listen_raw");

    if (!result.ok) {
      setVoiceStatus(result.message || "Voice listener error.");
      return "";
    }

    return result.data?.heard_text || "";
  };

  
  const runWakeLoop = async () => {
  let commandMode = false;

  while (listeningRef.current) {
    if (!commandMode) {
      setVoiceStatus("Listening for “Hey Jarvis” or “Wake up Jarvis”");
    } else {
      setVoiceStatus("Command mode active. Say “sleep Jarvis” to stop.");
    }

    const heardText = await listenRaw();

    if (!listeningRef.current) break;

    if (!heardText) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      continue;
    }

    setVoiceStatus(`Heard: ${heardText}`);

    if (containsSleepPhrase(heardText)) {
      commandMode = false;
      setVoiceStatus("Jarvis sleeping. Say “Hey Jarvis” to wake again.");
      await new Promise((resolve) => setTimeout(resolve, 800));
      continue;
    }

    if (!commandMode) {
      if (!containsWakePhrase(heardText)) {
        await new Promise((resolve) => setTimeout(resolve, 250));
        continue;
      }

      commandMode = true;

      const commandAfterWake = removeWakePhrase(heardText);

      if (!commandAfterWake) {
        setVoiceStatus("Wake phrase detected. Listening for commands...");
        await new Promise((resolve) => setTimeout(resolve, 400));
        continue;
      }

      setVoiceStatus(`Voice command: ${commandAfterWake}`);
      await sendCommandText(commandAfterWake, "VOICE INPUT");
      continue;
    }

    setVoiceStatus(`Voice command: ${heardText}`);
    await sendCommandText(heardText, "VOICE INPUT");
  }
};

  const startAutoWakeListening = () => {
    if (listeningRef.current) return;

    listeningRef.current = true;
    setMicState("continuous");
    runWakeLoop();
  };

  const stopWakeListening = () => {
    listeningRef.current = false;
    setMicState("off");
    setVoiceStatus("Voice listening paused.");
  };

  const onMicClick = async () => {
    if (listeningRef.current) {
      stopWakeListening();
      return;
    }

    startAutoWakeListening();
  };

  return (
    <section className="relative flex h-full min-w-0 flex-col overflow-hidden">
      <div className="shrink-0 border-b border-white/10 px-6 py-5">
        <div className="flex min-w-0 items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-3xl font-semibold tracking-tight">Command Center</h1>
            <p className="mt-1 text-sm text-secondary">
              Voice-first Jarvis command center. Text input is available as a secondary control.
            </p>
          </div>

          <div className="hidden shrink-0 flex-wrap items-center justify-end gap-2 lg:flex">
            <StatusChip tone="active">MODEL {selectedModel}</StatusChip>

            <StatusChip tone={isRunning ? "warning" : "success"}>
              {isRunning ? "EXECUTING" : "READY"}
            </StatusChip>

            <StatusChip tone={micState === "continuous" ? "success" : "neutral"}>
              {micState === "continuous" ? "WAKE LISTENING" : "VOICE PAUSED"}
            </StatusChip>
          </div>
        </div>
      </div>

      <div
        ref={scrollBoxRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto px-8 py-6"
      >
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-5 pb-4">
          <DebugStrip />

          {messages.length === 0 && (
            <div className="mx-auto mt-20 max-w-xl rounded-2xl border border-white/10 bg-white/[0.025] p-6 text-center">
              <p className="text-xl font-semibold text-primary">Jarvis is ready</p>
              <p className="mt-2 text-sm text-secondary">
                Say “Hey Jarvis” or “Wake up Jarvis” to start.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <ChatBubble
              key={message.id}
              role={message.role}
              text={message.text}
              meta={message.meta}
            />
          ))}

          {isRunning && <ThinkingLoader />}

          <div ref={endRef} />
        </div>
      </div>

      {!isAtBottom && (
        <button
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-[105px] left-1/2 z-40 flex h-10 w-10 -translate-x-1/2 items-center justify-center rounded-full border border-white/10 bg-surface-card text-primary-container shadow-glow-soft hover:border-primary-container/40"
          title="Scroll to bottom"
        >
          <ArrowDown size={19} />
        </button>
      )}

      <div className="shrink-0 border-t border-white/10 bg-background/80 px-8 pt-3 pb-8 backdrop-blur-xl">
        <div className="mx-auto w-full max-w-5xl">
          <ChatInputBar
            value={input}
            setValue={setInput}
            onSend={onSend}
            selectedModel={selectedModel}
            setSelectedModel={handleModelChange}
            modelOptions={modelOptions}
            micState={micState}
            onMicClick={onMicClick}
            voiceStatus={voiceStatus}
          />
        </div>
      </div>
    </section>
  );
}
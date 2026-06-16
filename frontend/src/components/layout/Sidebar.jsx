import {
  Bot,
  CalendarDays,
  Check,
  ChevronRight,
  Crown,
  MessageSquare,
  Plus,
  Settings,
  Terminal,
  Trash2,
  UserCircle,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import JarvisLogo from "../common/JarvisLogo";
import { callJarvis } from "../../lib/bridge";

const navItems = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "plans", label: "Plans", icon: Crown },
  { id: "profile", label: "Profile", icon: UserCircle },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ activePage, onNavigate, onAdmin }) {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState("");
  const [pendingDeleteId, setPendingDeleteId] = useState("");

  useEffect(() => {
    loadChats();

    const refreshHandler = () => {
      loadChats();
    };

    window.addEventListener("jarvis:conversations-updated", refreshHandler);

    return () => {
      window.removeEventListener("jarvis:conversations-updated", refreshHandler);
    };
  }, []);

  const loadChats = async () => {
    const result = await callJarvis("chat.list");

    if (result.ok && Array.isArray(result.data?.chats)) {
      setConversations(result.data.chats);
    }
  };

  const newChat = async () => {
    const result = await callJarvis("chat.create", {
      title: "New Chat",
    });

    if (!result.ok || !result.data?.chat) return;

    const chat = result.data.chat;

    setActiveConversation(chat.id);
    onNavigate("chat");

    window.dispatchEvent(
      new CustomEvent("jarvis:open-chat", {
        detail: chat,
      })
    );

    await loadChats();
  };

  const openConversation = (conversation) => {
    setActiveConversation(conversation.id);
    setPendingDeleteId("");
    onNavigate("chat");

    window.dispatchEvent(
      new CustomEvent("jarvis:open-chat", {
        detail: conversation,
      })
    );
  };

  const askDeleteConversation = (event, conversation) => {
    event.stopPropagation();
    setPendingDeleteId(conversation.id);
  };

  const cancelDeleteConversation = (event) => {
    event.stopPropagation();
    setPendingDeleteId("");
  };

  const confirmDeleteConversation = async (event, conversation) => {
    event.stopPropagation();

    const result = await callJarvis("chat.delete", {
      chat_id: conversation.id,
    });

    setPendingDeleteId("");

    if (result.ok) {
      if (activeConversation === conversation.id) {
        setActiveConversation("");

        window.dispatchEvent(
          new CustomEvent("jarvis:new-empty-chat")
        );
      }

      await loadChats();
    }
  };

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[280px] flex-col border-r border-white/10 bg-black/30 backdrop-blur-2xl">
      <div className="px-6 pb-7 pt-7">
        <JarvisLogo size="md" />
      </div>

      <nav className="space-y-2 px-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = activePage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={[
                "group flex h-14 w-full items-center gap-4 rounded-xl px-4 text-left transition-all",
                active
                  ? "core-border bg-primary-container/10 text-primary shadow-glow-soft"
                  : "text-secondary hover:bg-white/[0.04] hover:text-primary",
              ].join(" ")}
            >
              <Icon
                size={22}
                className={
                  active
                    ? "text-primary-container"
                    : "text-secondary group-hover:text-primary-container"
                }
              />
              <span className="text-base font-medium">{item.label}</span>
              {active && (
                <span className="ml-auto h-2 w-2 rounded-full bg-primary-container shadow-glow" />
              )}
            </button>
          );
        })}
      </nav>

      <div className="mt-8 min-h-0 flex-1 px-5">
        <div className="flex items-center justify-between">
          <p className="mono-label text-primary-container">Conversations</p>

          <button
            onClick={newChat}
            className="flex items-center gap-1 rounded-lg border border-primary-container/30 px-2.5 py-1.5 text-xs text-primary-container hover:bg-primary-container/10"
          >
            <Plus size={14} />
            New Chat
          </button>
        </div>

        <div className="mt-3 max-h-[360px] space-y-2 overflow-y-auto pr-1">
          {conversations.length === 0 && (
            <p className="rounded-lg border border-white/10 bg-white/[0.025] p-3 text-sm text-muted">
              No chats yet.
            </p>
          )}

          {conversations.map((conversation) => {
            const selected = activeConversation === conversation.id;
            const deleting = pendingDeleteId === conversation.id;

            return (
              <button
                key={conversation.id}
                onClick={() => openConversation(conversation)}
                className={[
                  "group flex w-full items-center gap-3 rounded-lg border px-3 py-3 text-left transition-all",
                  selected
                    ? "border-primary-container/35 bg-primary-container/10"
                    : "border-transparent hover:border-white/10 hover:bg-white/[0.035]",
                ].join(" ")}
              >
                <CalendarDays size={15} className="text-primary-container" />

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-primary">{conversation.title}</p>
                  <p className="mt-1 text-xs text-muted">
                    {conversation.time} • {conversation.message_count || 0} msgs
                  </p>
                </div>

                {deleting ? (
                  <span className="flex items-center gap-1">
                    <span
                      onClick={(event) => confirmDeleteConversation(event, conversation)}
                      className="flex h-7 w-7 items-center justify-center rounded-lg text-success hover:bg-success/10"
                    >
                      <Check size={15} />
                    </span>

                    <span
                      onClick={cancelDeleteConversation}
                      className="flex h-7 w-7 items-center justify-center rounded-lg text-danger hover:bg-danger/10"
                    >
                      <X size={15} />
                    </span>
                  </span>
                ) : (
                  <span
                    onClick={(event) => askDeleteConversation(event, conversation)}
                    className="hidden h-8 w-8 items-center justify-center rounded-lg text-muted hover:bg-danger/10 hover:text-danger group-hover:flex"
                  >
                    <Trash2 size={15} />
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-4">
        <div className="glass-panel rounded-xl p-5">
          <div className="flex items-center gap-3">
            <div className="core-gradient flex h-11 w-11 items-center justify-center rounded-full shadow-glow">
              <Bot size={22} className="text-background" />
            </div>
            <div>
              <p className="font-semibold text-primary">Jarvis Core</p>
              <p className="text-xs text-secondary">v1.0 • Local AI</p>
            </div>
          </div>
        </div>

        <button
          onClick={onAdmin}
          className="mt-3 flex w-full items-center gap-3 rounded-xl border border-white/10 px-4 py-3 text-left text-secondary transition-all hover:bg-white/[0.04] hover:text-primary"
        >
          <Terminal size={18} />
          <span className="text-sm font-medium">Debug Console</span>
          <ChevronRight size={16} className="ml-auto" />
        </button>
      </div>
    </aside>
  );
}
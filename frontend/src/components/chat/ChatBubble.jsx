import { Bot, User } from "lucide-react";

export default function ChatBubble({ role, text, meta }) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-primary-container/20 bg-primary-container/10 text-primary-container">
          <Bot size={18} />
        </div>
      )}

      <div
        className={[
          "max-w-[72%] rounded-xl border px-4 py-3 shadow-glass",
          isUser
            ? "border-primary-container/20 bg-primary-container/10 text-primary"
            : "border-white/10 bg-surface-container/80 text-on-surface",
        ].join(" ")}
      >
        <p className="whitespace-pre-wrap text-sm leading-6">{text}</p>
        {meta ? <p className="mono-label mt-2 text-on-surface-variant">{meta}</p> : null}
      </div>

      {isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-on-surface-variant">
          <User size={18} />
        </div>
      )}
    </div>
  );
}
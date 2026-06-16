export const aiModels = [
  "llama3.1:8b",
  "gemini-api",
  "openai-api",
];

export const navItems = [
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "plans", label: "Plans", icon: "calendar" },
  { id: "profile", label: "Profile", icon: "user" },
  { id: "settings", label: "Settings", icon: "settings" },
];

export const initialMessages = [
  {
    id: 1,
    role: "assistant",
    text: "Jarvis Online. AI Brain ready using llama3.1:8b.",
    meta: "SYSTEM / READY",
  },
  {
    id: 2,
    role: "user",
    text: "open edge",
  },
  {
    id: 3,
    role: "assistant",
    text: "Opening Microsoft Edge.",
    meta: "direct_route → open_app → 421ms",
  },
];

export const debugState = {
  lastCommand: "open edge",
  source: "direct_route",
  tool: "open_app",
  action: "open_app",
  target: "microsoft edge",
  status: "OK",
  duration: "421 ms",
  voiceRaw: "open age",
  voiceCorrected: "open edge",
};

export const profileMemory = {
  name: "CoderBoiii",
  accountType: "Local",
  plan: "Free Local",
  gpu: "NVIDIA GeForce RTX 4060",
  cpu: "i5-14600K",
  ram: "32GB DDR5",
};

export const diagnosticsStatus = {
  uploadAllowed: false,
  privacyAccepted: true,
  endpointConfigured: false,
  lastExport: "Training_Data\\exports\\training_data_export_2026-06-15_16-53-49.zip",
  lastUpload: "No upload endpoint configured.",
};

export const systemStatus = {
  ai: "Online",
  model: "llama3.1:8b",
  cpu: "4%",
  ram: "45%",
  gpu: "RTX 4060",
  vram: "7.2 / 8 GB",
  temp: "56°C",
};
import { useEffect, useState } from "react";
import { Database, LogOut, Mail, Monitor, Pencil, ShieldCheck, UserCircle } from "lucide-react";
import GlassCard from "../components/common/GlassCard";
import StatusChip from "../components/common/StatusChip";
import { callJarvis } from "../lib/bridge";

export default function ProfilePage({ user, setUser, onLogout }) {
  const [profile, setProfile] = useState({
    authenticated: true,
    name: user?.name || "",
    email: user?.email || "",
    email_verified: user?.email_verified || false,
    accountType: "Email Account",
    plan: "Free",
    gpu: "NVIDIA GeForce RTX 4060",
    cpu: "i5-14600K",
    ram: "32GB DDR5",
  });

  const [status, setStatus] = useState("Ready.");
  const [memoryOutput, setMemoryOutput] = useState("No memory output yet.");

  const [name, setName] = useState(user?.name || "");
  const [emailForm, setEmailForm] = useState({
    new_email: "",
    password: "",
    code: "",
    codeSent: false,
    devCode: "",
  });

  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
  });

  useEffect(() => {
    async function loadProfile() {
      const result = await callJarvis("profile.get");

      if (result.ok && result.data) {
        setProfile(result.data);
        setName(result.data.name || "");
      }
    }

    loadProfile();
  }, []);

  const saveName = async () => {
    const result = await callJarvis("auth.update_name", { name });

    setStatus(result.message || "Name updated.");

    if (result.ok && result.data?.user) {
      setUser(result.data.user);
      setProfile((current) => ({
        ...current,
        name: result.data.user.name,
      }));
    }
  };

  const startEmailChange = async () => {
    const result = await callJarvis("auth.change_email_start", {
      new_email: emailForm.new_email,
      password: emailForm.password,
    });

    setStatus(result.message || "Email verification started.");

    if (result.ok) {
      setEmailForm((current) => ({
        ...current,
        codeSent: true,
        devCode: result.data?.dev_code || "",
      }));
    }
  };

  const verifyEmailChange = async () => {
    const result = await callJarvis("auth.change_email_verify", {
      new_email: emailForm.new_email,
      code: emailForm.code,
    });

    setStatus(result.message || "Email changed.");

    if (result.ok && result.data?.user) {
      setUser(result.data.user);
      setProfile((current) => ({
        ...current,
        email: result.data.user.email,
        email_verified: result.data.user.email_verified,
      }));

      setEmailForm({
        new_email: "",
        password: "",
        code: "",
        codeSent: false,
        devCode: "",
      });
    }
  };

  const changePassword = async () => {
    const result = await callJarvis("auth.change_password", passwordForm);

    setStatus(result.message || "Password changed.");

    if (result.ok) {
      setPasswordForm({
        current_password: "",
        new_password: "",
      });
    }
  };

  const showMemory = async () => {
    const result = await callJarvis("memory.show");
    setMemoryOutput(result.data?.reply || result.message || "No memory returned.");
  };

  const clearMemory = async () => {
    const confirmed = window.confirm("Clear saved system memory?");
    if (!confirmed) return;

    const result = await callJarvis("memory.clear");
    setMemoryOutput(result.data?.reply || result.message || "Memory cleared.");
  };

  return (
    <div className="h-full overflow-y-auto p-container-padding">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
            <p className="mt-2 text-on-surface-variant">
              Manage your Jarvis account, email, password, and local memory.
            </p>
            <p className="mono-data mt-3 text-primary">{status}</p>
          </div>

          <button
            onClick={onLogout}
            className="flex items-center gap-2 rounded-lg border border-danger/30 px-4 py-2 text-danger hover:bg-danger/10"
          >
            <LogOut size={17} />
            Logout
          </button>
        </div>

        <div className="grid grid-cols-[360px_1fr] gap-4">
          <GlassCard>
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full border border-primary-container/20 bg-primary-container/10 text-primary-container">
                <UserCircle size={36} />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{profile.name}</h2>
                <p className="text-sm text-on-surface-variant">{profile.email}</p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              <StatusChip tone="success">{profile.accountType}</StatusChip>
              <StatusChip tone={profile.email_verified ? "success" : "warning"}>
                {profile.email_verified ? "EMAIL VERIFIED" : "EMAIL NOT VERIFIED"}
              </StatusChip>
              <StatusChip tone="neutral">{profile.plan}</StatusChip>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="mb-5 flex items-center gap-3">
              <Monitor className="text-primary-container" />
              <h2 className="text-lg font-semibold">Saved PC Memory</h2>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                ["GPU", profile.gpu],
                ["CPU", profile.cpu],
                ["RAM", profile.ram],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg border border-white/10 bg-white/[0.03] p-4">
                  <p className="mono-label text-on-surface-variant">{label}</p>
                  <p className="mono-data mt-2 text-primary">{value}</p>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <GlassCard>
            <div className="mb-4 flex items-center gap-3">
              <Pencil className="text-primary-container" />
              <h2 className="text-lg font-semibold">Change Name</h2>
            </div>

            <input
              className="auth-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
            />

            <button onClick={saveName} className="auth-primary mt-3">
              Save Name
            </button>
          </GlassCard>

          <GlassCard>
            <div className="mb-4 flex items-center gap-3">
              <Mail className="text-primary-container" />
              <h2 className="text-lg font-semibold">Change Email</h2>
            </div>

            <input
              className="auth-input"
              value={emailForm.new_email}
              onChange={(e) => setEmailForm({ ...emailForm, new_email: e.target.value })}
              placeholder="New email"
            />

            <input
              className="auth-input mt-3"
              type="password"
              value={emailForm.password}
              onChange={(e) => setEmailForm({ ...emailForm, password: e.target.value })}
              placeholder="Current password"
            />

            <button onClick={startEmailChange} className="auth-primary mt-3">
              Send Code
            </button>

            {emailForm.codeSent && (
              <>
                <p className="mt-3 rounded-lg border border-warning/20 bg-warning/5 p-3 text-sm text-warning">
                  Dev code: {emailForm.devCode}
                </p>

                <input
                  className="auth-input mt-3 text-center font-mono tracking-[0.4em]"
                  value={emailForm.code}
                  onChange={(e) => setEmailForm({ ...emailForm, code: e.target.value })}
                  placeholder="000000"
                  maxLength={6}
                />

                <button onClick={verifyEmailChange} className="auth-primary mt-3">
                  Verify Email
                </button>
              </>
            )}
          </GlassCard>

          <GlassCard>
            <div className="mb-4 flex items-center gap-3">
              <ShieldCheck className="text-primary-container" />
              <h2 className="text-lg font-semibold">Change Password</h2>
            </div>

            <input
              className="auth-input"
              type="password"
              value={passwordForm.current_password}
              onChange={(e) =>
                setPasswordForm({ ...passwordForm, current_password: e.target.value })
              }
              placeholder="Current password"
            />

            <input
              className="auth-input mt-3"
              type="password"
              value={passwordForm.new_password}
              onChange={(e) =>
                setPasswordForm({ ...passwordForm, new_password: e.target.value })
              }
              placeholder="New password"
            />

            <button onClick={changePassword} className="auth-primary mt-3">
              Change Password
            </button>
          </GlassCard>
        </div>

        <GlassCard>
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <Database className="text-primary-container" />
                <h2 className="text-lg font-semibold">Jarvis Memory</h2>
              </div>
              <p className="mt-2 text-sm text-on-surface-variant">
                Memory is local and used for Jarvis context.
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={showMemory}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm hover:bg-white/5"
              >
                Show Memory
              </button>
              <button
                onClick={clearMemory}
                className="rounded-lg border border-danger/30 px-4 py-2 text-sm text-danger hover:bg-danger/10"
              >
                Clear Memory
              </button>
            </div>
          </div>

          <pre className="mt-5 max-h-72 overflow-auto rounded-lg border border-white/10 bg-black/30 p-4 mono-data text-on-surface-variant whitespace-pre-wrap">
            {memoryOutput}
          </pre>
        </GlassCard>
      </div>
    </div>
  );
}
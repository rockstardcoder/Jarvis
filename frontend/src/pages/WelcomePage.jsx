import { useState } from "react";
import {
  ArrowLeft,
  Eye,
  EyeOff,
  Lock,
  LogIn,
  Mail,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  User,
  UserPlus,
} from "lucide-react";
import { callJarvis } from "../lib/bridge";
import JarvisLogo from "../components/common/JarvisLogo";
import DotSpinner from "../components/common/DotSpinner";

export default function WelcomePage({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [status, setStatus] = useState("Use your email account to continue.");
  const [pendingEmail, setPendingEmail] = useState("");
  const [devCode, setDevCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState("");

  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  const [signupForm, setSignupForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [code, setCode] = useState("");

  const startSignup = async () => {
    setLoading(true);
    setStatus("Creating account...");
    setLoginError("");

    const result = await callJarvis("auth.signup_start", signupForm);

    setTimeout(() => {
      setLoading(false);
      setStatus(result.message || "Verification code created.");

      if (result.ok && result.data?.user) {
        onAuthSuccess(result.data.user);
        return;
      }

      if (result.ok) {
        setPendingEmail(result.data.email);
        setDevCode(result.data.dev_code || "");
        setMode("verify");
        return;
      }

      setLoginError(result.message || "Signup failed.");
    }, 950);
  };

  const resendCode = async () => {
    setLoading(true);
    setStatus("Resending verification code...");
    setLoginError("");

    const result = await callJarvis("auth.signup_start", {
      ...signupForm,
      email: pendingEmail || signupForm.email,
    });

    setTimeout(() => {
      setLoading(false);
      setStatus(result.message || "Verification code resent.");

      if (result.ok) {
        setPendingEmail(result.data.email);
        setDevCode(result.data.dev_code || "");
        return;
      }

      setLoginError(result.message || "Could not resend code.");
    }, 750);
  };

  const verifySignup = async () => {
    setLoading(true);
    setStatus("Verifying email...");
    setLoginError("");

    const result = await callJarvis("auth.signup_verify", {
      email: pendingEmail,
      code,
    });

    setTimeout(() => {
      setLoading(false);
      setStatus(result.message || "Verification complete.");

      if (result.ok && result.data?.user) {
        onAuthSuccess(result.data.user);
        return;
      }

      setLoginError(result.message || "Verification failed.");
    }, 700);
  };

  const login = async () => {
    setLoading(true);
    setStatus("Logging in...");
    setLoginError("");

    const result = await callJarvis("auth.login", loginForm);

    setTimeout(() => {
      setLoading(false);
      setStatus(result.message || "Login complete.");

      if (result.ok && result.data?.user) {
        onAuthSuccess(result.data.user);
        return;
      }

      if (result.ok && result.data?.needs_verification) {
        setPendingEmail(result.data.email || loginForm.email);
        setDevCode(result.data.dev_code || "");
        setMode("verify");
        return;
      }

      setLoginError(result.message || "Invalid email or password.");
    }, 700);
  };

  const goBack = () => {
    setLoginError("");

    if (mode === "verify") {
      setMode("signup");
      return;
    }

    if (mode === "signup") {
      setMode("login");
      return;
    }

    setMode("login");
  };

  return (
    <div className="relative flex h-screen items-center justify-center overflow-hidden bg-background p-6">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[12%] top-[12%] h-[360px] w-[360px] rounded-full bg-primary-container/10 blur-[100px]" />
        <div className="absolute bottom-[5%] right-[10%] h-[440px] w-[440px] rounded-full bg-primary-blue/10 blur-[120px]" />
      </div>

      <div className="glass-panel relative w-[500px] rounded-[28px] p-8 shadow-card-depth">
        {mode !== "login" && (
          <button
            onClick={goBack}
            className="absolute left-5 top-5 flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-secondary hover:border-primary-container/30 hover:text-primary-container"
            title="Back"
          >
            <ArrowLeft size={19} />
          </button>
        )}

        <div className="mx-auto flex h-20 items-center justify-center">
          {loading ? (
            <DotSpinner />
          ) : (
            <div className="flex h-20 w-20 items-center justify-center rounded-full border border-primary-container/25 bg-primary-container/10 shadow-glow-soft">
              <Sparkles size={36} className="text-primary-container" />
            </div>
          )}
        </div>

        <h1 className="mt-6 text-center text-4xl font-bold tracking-tight">Jarvis Account</h1>
        <p className="mt-2 text-center text-sm text-secondary">
          Email authentication is required for this Jarvis profile.
        </p>

        <p
          className={[
            "mono-data mt-5 rounded-xl border bg-black/20 p-3 text-center",
            loginError ? "border-danger/30 text-danger" : "border-white/10 text-primary",
          ].join(" ")}
        >
          {loading ? "Please wait..." : status}
        </p>

        {mode === "login" && (
          <div className="mt-6 space-y-4">
            <AuthInput
              icon={Mail}
              label="Email"
              placeholder="Enter your email"
              value={loginForm.email}
              error={Boolean(loginError)}
              onChange={(value) => {
                setLoginError("");
                setLoginForm({ ...loginForm, email: value });
              }}
            />

            <AuthInput
              icon={Lock}
              label="Password"
              placeholder="Enter your password"
              type={showPassword ? "text" : "password"}
              value={loginForm.password}
              error={Boolean(loginError)}
              onChange={(value) => {
                setLoginError("");
                setLoginForm({ ...loginForm, password: value });
              }}
              rightIcon={showPassword ? EyeOff : Eye}
              onRightIconClick={() => setShowPassword(!showPassword)}
            />

            {loginError && <p className="auth-error-text">{loginError}</p>}

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-secondary">
                <input type="checkbox" className="accent-cyan-400" />
                Remember me
              </label>

              <button className="text-primary-container hover:underline">
                Forgot password?
              </button>
            </div>

            <button onClick={login} disabled={loading} className="auth-primary">
              {loading ? <DotSpinner size="sm" /> : <LogIn size={18} />}
              Login
            </button>

            <p className="text-center text-sm text-secondary">
              Don&apos;t have an account?{" "}
              <button
                onClick={() => {
                  setLoginError("");
                  setStatus("Create your Jarvis account.");
                  setMode("signup");
                }}
                className="font-semibold text-primary-container hover:underline"
              >
                Create account
              </button>
            </p>
          </div>
        )}

        {mode === "signup" && (
          <div className="mt-6 space-y-4">
            <AuthInput
              icon={User}
              label="Name"
              placeholder="Enter your name"
              value={signupForm.name}
              onChange={(value) => setSignupForm({ ...signupForm, name: value })}
            />

            <AuthInput
              icon={Mail}
              label="Email"
              placeholder="Enter your email"
              value={signupForm.email}
              onChange={(value) => setSignupForm({ ...signupForm, email: value })}
            />

            <AuthInput
              icon={Lock}
              label="Password"
              placeholder="Minimum 6 characters"
              type={showPassword ? "text" : "password"}
              value={signupForm.password}
              onChange={(value) => setSignupForm({ ...signupForm, password: value })}
              rightIcon={showPassword ? EyeOff : Eye}
              onRightIconClick={() => setShowPassword(!showPassword)}
            />

            {loginError && <p className="auth-error-text">{loginError}</p>}

            <button onClick={startSignup} disabled={loading} className="auth-primary">
              {loading ? <DotSpinner size="sm" /> : <UserPlus size={18} />}
              Create Account
            </button>

            <p className="text-center text-sm text-secondary">
              Already have an account?{" "}
              <button
                onClick={() => {
                  setLoginError("");
                  setStatus("Use your email account to continue.");
                  setMode("login");
                }}
                className="font-semibold text-primary-container hover:underline"
              >
                Login
              </button>
            </p>
          </div>
        )}

        {mode === "verify" && (
          <div className="mt-6 space-y-4">
            <div className="rounded-xl border border-warning/20 bg-warning/5 p-4 text-sm text-secondary">
              <ShieldCheck className="mr-2 inline text-warning" size={16} />
              Development verification code:
              <span className="ml-2 font-mono font-bold text-warning">{devCode}</span>
            </div>

            <input
              className="auth-input text-center font-mono text-lg tracking-[0.45em]"
              placeholder="000000"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />

            {loginError && <p className="auth-error-text">{loginError}</p>}

            <button onClick={verifySignup} disabled={loading} className="auth-primary">
              {loading ? <DotSpinner size="sm" /> : <Lock size={18} />}
              Verify Email
            </button>

            <button onClick={resendCode} disabled={loading} className="auth-secondary">
              <RefreshCcw size={17} />
              Resend Code
            </button>

            <p className="text-center text-sm text-secondary">
              Wrong email?{" "}
              <button
                onClick={() => {
                  setLoginError("");
                  setMode("signup");
                }}
                className="font-semibold text-primary-container hover:underline"
              >
                Edit details
              </button>
            </p>
          </div>
        )}

        <div className="mt-7 flex justify-center">
          <JarvisLogo size="sm" />
        </div>
      </div>
    </div>
  );
}

function AuthInput({
  icon: Icon,
  label,
  placeholder,
  value,
  onChange,
  type = "text",
  rightIcon: RightIcon,
  onRightIconClick,
  error = false,
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-semibold text-primary">{label}</label>

      <div
        className={[
          "flex h-12 items-center gap-3 rounded-xl border bg-surface-soft px-3 transition-all focus-within:border-primary-container/50 focus-within:shadow-glow-soft",
          error ? "auth-input-error" : "border-white/10",
        ].join(" ")}
      >
        <Icon size={18} className={error ? "text-danger" : "text-secondary"} />

        <input
          className="h-full min-w-0 flex-1 bg-transparent text-primary outline-none placeholder:text-muted"
          placeholder={placeholder}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />

        {RightIcon && (
          <button
            type="button"
            onClick={onRightIconClick}
            className={error ? "text-danger" : "text-secondary hover:text-primary-container"}
          >
            <RightIcon size={18} />
          </button>
        )}
      </div>
    </div>
  );
}

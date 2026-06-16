import { useEffect, useState } from "react";
import AppShell from "./components/layout/AppShell";
import WelcomePage from "./pages/WelcomePage";
import { callJarvis } from "./lib/bridge";

export default function App() {
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [user, setUser] = useState(null);
  const [activePage, setActivePage] = useState("chat");

  useEffect(() => {
    async function checkAuth() {
      const result = await callJarvis("auth.current_user");

      if (result.ok && result.data?.authenticated) {
        setUser(result.data.user);
      } else {
        setUser(null);
      }

      setCheckingAuth(false);
    }

    checkAuth();
  }, []);

  const handleAuthSuccess = (authUser) => {
    setUser(authUser);
    setActivePage("chat");
  };

  const handleLogout = async () => {
    await callJarvis("auth.logout");
    setUser(null);
    setActivePage("chat");
  };

  if (checkingAuth) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-on-surface">
        <div className="glass-panel rounded-xl p-6 mono-data text-primary">
          Checking Jarvis account...
        </div>
      </div>
    );
  }

  if (!user) {
    return <WelcomePage onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <AppShell
      activePage={activePage}
      setActivePage={setActivePage}
      user={user}
      setUser={setUser}
      onLogout={handleLogout}
    />
  );
}
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import FloatingWidget from "../widget/FloatingWidget";
import ChatPage from "../../pages/ChatPage";
import PlansPage from "../../pages/PlansPage";
import ProfilePage from "../../pages/ProfilePage";
import SettingsPage from "../../pages/SettingsPage";
import AdminPanel from "../../pages/AdminPanel";

export default function AppShell({
  activePage,
  setActivePage,
  user,
  setUser,
  onLogout,
}) {
  const renderPage = () => {
    if (activePage === "plans") return <PlansPage />;

    if (activePage === "profile") {
      return (
        <ProfilePage
          user={user}
          setUser={setUser}
          onLogout={onLogout}
        />
      );
    }

    if (activePage === "settings") return <SettingsPage />;
    if (activePage === "admin") return <AdminPanel />;

    return <ChatPage />;
  };

  return (
    <div className="h-screen overflow-hidden bg-background text-primary">
      <div className="pointer-events-none fixed inset-0 opacity-70">
        <div className="absolute right-[-15%] top-[10%] h-[540px] w-[540px] rounded-full bg-primary-blue/10 blur-[120px]" />
        <div className="absolute bottom-[-15%] left-[35%] h-[420px] w-[420px] rounded-full bg-primary-green/10 blur-[120px]" />
      </div>

      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        onAdmin={() => setActivePage("admin")}
      />

      <TopBar />

      <main className="relative ml-[280px] mt-16 h-[calc(100vh-64px)] overflow-hidden">
        {renderPage()}
      </main>

      <FloatingWidget
        activePage={activePage}
        onOpen={() => setActivePage("chat")}
        onSettings={() => setActivePage("settings")}
      />
    </div>
  );
}
import { Navigate, NavLink, Route, HashRouter as Router, Routes } from "react-router-dom";
import { MyCoaching } from "./pages/MyCoaching";
import { TeamRoster } from "./pages/TeamRoster";
import { UserDetailPage } from "./pages/UserDetail";

export default function App() {
  return (
    <Router>
      <div className="app-shell">
        <nav className="app-nav">
          <h1>GCCF Coach</h1>
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "chip active" : "chip")}>
            Team
          </NavLink>
          <NavLink to="/me" className={({ isActive }) => (isActive ? "chip active" : "chip")}>
            My coaching
          </NavLink>
        </nav>

        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<TeamRoster />} />
          <Route path="/dashboard/users/:userId" element={<UserDetailPage />} />
          <Route path="/me" element={<MyCoaching />} />
        </Routes>
      </div>
    </Router>
  );
}

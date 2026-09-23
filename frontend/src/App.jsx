import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Admin from "./pages/Admin.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">🌊 AquaAlert Odisha</div>
          <nav>
            <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
              Citizen Map
            </NavLink>
            <NavLink to="/admin" className={({ isActive }) => (isActive ? "active" : "")}>
              Admin Dashboard
            </NavLink>
          </nav>
        </header>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

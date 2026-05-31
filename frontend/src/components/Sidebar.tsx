import { NavLink } from "react-router-dom";
import "../styles/sidebar.css";

const menuItems = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Videos", path: "/videos" },
  { label: "Validaciones", path: "/validaciones" },
  { label: "Estadisticas", path: "/statistics" },
  { label: "Frecuencia y abundancia", path: "/statistics/frequency" },
  { label: "Diversidad y gremios", path: "/statistics/diversity" },
  { label: "Tendencias temporales", path: "/statistics/trends" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src="/logowwf.png" alt="WWF" />
        <h2>WWF</h2>
      </div>

      <div className="sidebar-title">MENU PRINCIPAL</div>

      <ul className="sidebar-menu">
        {menuItems.map((item) => (
          <li key={item.path}>
            <NavLink
              to={item.path}
              end={item.path === "/statistics"}
              className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>

      <div className="sidebar-user">
        <div className="avatar">JD</div>

        <div>
          <h4>Jane Doe</h4>
          <span>Biologa Investigadora</span>
        </div>
      </div>
    </aside>
  );
}

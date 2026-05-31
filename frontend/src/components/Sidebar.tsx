import { Link } from "react-router-dom";
import "../styles/sidebar.css";

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src="/logowwf.png" alt="WWF" />
        <h2>WWF</h2>
      </div>

      <div className="sidebar-title">
        MENÚ PRINCIPAL
      </div>

      <ul className="sidebar-menu">
        <li>
          <Link to="/dashboard" className="sidebar-link">
            Dashboard
          </Link>
        </li>

        <li>
          <Link to="/estudios" className="sidebar-link">
            Mis Estudios
          </Link>
        </li>

        <li>
          <Link to="/videos" className="sidebar-link">
            Videos
          </Link>
        </li>

        <li>
          <Link to="/validaciones" className="sidebar-link">
            Validaciones
          </Link>
        </li>

        <li>
          <Link to="/estadisticas" className="sidebar-link">
            Estadísticas
          </Link>
        </li>

        <li>
          <Link to="/reportes" className="sidebar-link">
            Reportes
          </Link>
        </li>

        <li>
          <Link to="/configuracion" className="sidebar-link">
            Configuración
          </Link>
        </li>
      </ul>

      <div className="sidebar-user">
        <div className="avatar">JD</div>

        <div>
          <h4>Jane Doe</h4>
          <span>Bióloga Investigadora</span>
        </div>
      </div>
    </aside>
  );
}
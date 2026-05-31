import "../styles/login.css";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

const Login = () => {
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();

    toast.success("Bienvenido al sistema WWF", {
      position: "top-right",
      autoClose: 2000,
    });

    setTimeout(() => {
      navigate("/dashboard");
    }, 2000);
  };

  return (
    <div className="login-container">
      {/* Panel Izquierdo */}
      <div className="login-left">
        <div className="overlay">
          <div className="left-content">
            <h1>
              Conservamos la vida
              <br />
              silvestre para las
              <br />
              futuras generaciones.
            </h1>

            <p>WWF Bolivia</p>
          </div>
        </div>
      </div>

      {/* Panel Derecho */}
      <div className="login-right">
        <div className="login-card">
          <div className="logo-container">
            <img
              src="logowwf.png"
              alt="WWF Logo"
              className="logo"
            />
          </div>

          <h2>WWF</h2>

          <p className="subtitle">
            Plataforma de identificación automática
            <br />
            y análisis de fauna silvestre
          </p>

          <form className="login-form" onSubmit={handleLogin}>
            <div className="form-group">
              <label>Correo electrónico</label>
              <input
                type="email"
                placeholder="correo@ejemplo.com"
              />
            </div>

            <div className="form-group">
              <label>Contraseña</label>

              <div className="password-container">
                <input
                  type="password"
                  placeholder="••••••••••"
                />
                <span className="eye-icon">👁</span>
              </div>
            </div>

            <a href="#" className="forgot-password">
              ¿Olvidaste tu contraseña?
            </a>

            <button type="submit" className="login-btn">
              Ingresar
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
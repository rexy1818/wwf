import Sidebar from "../components/Sidebar";
import "../styles/video.css";
import { Upload, Video, PlayCircle } from "lucide-react";

export default function Videos() {
  return (
    <>
      <Sidebar />

      <main className="videos-container">
        <div className="videos-header">
          <h1>Procesamiento de Videos</h1>
          <p>
            Cargue uno o varios videos para iniciar el análisis automático de
            especies mediante inteligencia artificial.
          </p>
        </div>

        {/* Zona de carga */}
        <section className="upload-section">
          <div className="upload-box">
            <Upload size={60} />

            <h2>Arrastre videos aquí</h2>

            <p>
              o haga clic para seleccionar múltiples archivos desde su equipo
            </p>

            <button className="upload-btn">
              Seleccionar Videos
            </button>
          </div>
        </section>

        {/* Resumen */}
        <section className="summary-grid">
          <div className="summary-card">
            <Video size={32} />
            <h3>0</h3>
            <span>Videos cargados</span>
          </div>

          <div className="summary-card">
            <PlayCircle size={32} />
            <h3>0</h3>
            <span>Procesados</span>
          </div>

          <div className="summary-card">
            <Upload size={32} />
            <h3>0%</h3>
            <span>Progreso</span>
          </div>
        </section>

        {/* Tabla */}
        <section className="videos-table">
          <div className="table-header">
            <h2>Lista de Videos</h2>
          </div>

          <table>
            <thead>
              <tr>
                <th>Archivo</th>
                <th>Estado</th>
                <th>Especie</th>
                <th>Cámara</th>
                <th>Fecha</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>Sin videos cargados</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </>
  );
}
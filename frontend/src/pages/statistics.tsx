import { Link } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import "../styles/statistics.css";

import data from "../data/datosSimulados.json";

export default function Statistics() {
  const detections = data.deteccionesSimuladas || [];

  const totalDetections = detections.length;
  const totalSpecies = new Set(detections.map((item: any) => item.especie)).size;
  const totalStations = new Set(detections.map((item: any) => item.estacion)).size;

  const validatedRecords = detections.filter((item: any) => item.validado).length;

  const validatedPercentage =
    totalDetections > 0
      ? ((validatedRecords / totalDetections) * 100).toFixed(1)
      : "0";

  const speciesCount: Record<string, number> = {};

  detections.forEach((item: any) => {
    speciesCount[item.especie] = (speciesCount[item.especie] || 0) + 1;
  });

  const mostRegisteredSpecies =
    Object.entries(speciesCount).sort((a, b) => b[1] - a[1])[0]?.[0] ||
    "Sin datos";

  return (
    <>
      <Sidebar />

      <main className="statistics-container">
        <section className="statistics-header">
          <h1>Dashboard Estadístico</h1>
          <p>
            Resumen general de los registros simulados obtenidos por cámaras
            trampa para el monitoreo de fauna silvestre.
          </p>
        </section>

        <section className="statistics-summary-grid">
          <div className="statistics-card">
            <span>Total de detecciones</span>
            <h2>{totalDetections}</h2>
          </div>

          <div className="statistics-card">
            <span>Total de especies</span>
            <h2>{totalSpecies}</h2>
          </div>

          <div className="statistics-card">
            <span>Estaciones activas</span>
            <h2>{totalStations}</h2>
          </div>

          <div className="statistics-card">
            <span>Registros validados</span>
            <h2>{validatedPercentage}%</h2>
          </div>
        </section>

        <section className="statistics-main-card">
          <span>Especie más registrada</span>
          <h2>{mostRegisteredSpecies}</h2>
        </section>

        <section className="statistics-options-grid">
          <div className="statistics-option-card">
            <h2>Frecuencia y abundancia</h2>
            <p>
              Muestra registros por especie, porcentaje de aparición y ranking
              de especies más frecuentes.
            </p>
            <Link to="/statistics/frequency">Ver análisis</Link>
          </div>

          <div className="statistics-option-card">
            <h2>Diversidad, gremios y presas</h2>
            <p>
              Muestra riqueza de especies, gremios tróficos y presas potenciales
              del jaguar.
            </p>
            <Link to="/statistics/diversity">Ver análisis</Link>
          </div>

          <div className="statistics-option-card">
            <h2>Tendencias temporales</h2>
            <p>
              Muestra registros por fecha, hora del día y patrones de actividad
              diaria.
            </p>
            <Link to="/statistics/trends">Ver análisis</Link>
          </div>
        </section>
      </main>
    </>
  );
}
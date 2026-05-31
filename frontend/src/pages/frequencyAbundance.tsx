import Sidebar from "../components/Sidebar";
import "../styles/statistics.css";

import data from "../data/datosSimulados.json";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type Detection = {
  id: number;
  idVideo: string;
  idCamara: string;
  estacion: string;
  fecha: string;
  hora: string;
  temperatura: number;
  especie: string;
  latitud: number;
  longitud: number;
  validado: boolean;
  confianzaModelo: number;
};

function calculatePercentage(value: number, total: number) {
  if (total === 0) return "0.0";
  return ((value / total) * 100).toFixed(1);
}

function countRecordsBySpecies(detections: Detection[]) {
  const speciesCount: Record<string, number> = {};

  detections.forEach((item) => {
    speciesCount[item.especie] = (speciesCount[item.especie] || 0) + 1;
  });

  return Object.entries(speciesCount)
    .map(([species, count]) => ({
      species,
      count,
    }))
    .sort((a, b) => b.count - a.count);
}

function countUniqueSpecies(detections: Detection[]) {
  return new Set(detections.map((item) => item.especie)).size;
}

function countUniqueStations(detections: Detection[]) {
  return new Set(detections.map((item) => item.estacion)).size;
}

export default function FrequencyAbundance() {
  const detections: Detection[] = data.deteccionesSimuladas || [];

  const totalRecords = detections.length;
  const totalSpecies = countUniqueSpecies(detections);
  const totalStations = countUniqueStations(detections);

  const recordsBySpecies = countRecordsBySpecies(detections);

  const tableData = recordsBySpecies.map((item) => ({
    ...item,
    percentage: calculatePercentage(item.count, totalRecords),
  }));

  const topSpecies = tableData.slice(0, 5);

  return (
    <>
      <Sidebar />

      <main className="statistics-container">
        <section className="statistics-header">
          <h1>Frecuencia y abundancia de especies</h1>
          <p>
            Este análisis muestra la frecuencia absoluta, frecuencia relativa y
            abundancia relativa básica de las especies registradas por las
            cámaras trampa.
          </p>
        </section>

        <section className="statistics-summary-grid">
          <div className="statistics-card">
            <span>Total de registros</span>
            <h2>{totalRecords}</h2>
          </div>

          <div className="statistics-card">
            <span>Especies detectadas</span>
            <h2>{totalSpecies}</h2>
          </div>

          <div className="statistics-card">
            <span>Estaciones activas</span>
            <h2>{totalStations}</h2>
          </div>

          <div className="statistics-card">
            <span>Especie más frecuente</span>
            <h2>{topSpecies[0]?.species || "Sin datos"}</h2>
          </div>
        </section>

        <section className="statistics-chart-card">
          <h2>Registros por especie</h2>

          <div className="statistics-chart">
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={recordsBySpecies}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="species"
                  angle={-25}
                  textAnchor="end"
                  height={90}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" name="Registros" fill="#149A8A" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="statistics-content-grid">
          <div className="statistics-table-card">
            <h2>Tabla de frecuencia</h2>

            <table className="statistics-table">
              <thead>
                <tr>
                  <th>Especie</th>
                  <th>Cantidad de registros</th>
                  <th>Porcentaje</th>
                </tr>
              </thead>

              <tbody>
                {tableData.map((item) => (
                  <tr key={item.species}>
                    <td>{item.species}</td>
                    <td>{item.count}</td>
                    <td>{item.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="statistics-ranking-card">
            <h2>Ranking de especies más frecuentes</h2>

            <div className="statistics-ranking-list">
              {topSpecies.map((item, index) => (
                <div className="statistics-ranking-item" key={item.species}>
                  <div>
                    <strong>
                      #{index + 1} {item.species}
                    </strong>
                    <span>{item.percentage}% del total</span>
                  </div>

                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
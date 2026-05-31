import { useMemo, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/statistics.css";

import data from "../data/datosSimulados.json";

import {
  LineChart,
  Line,
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

function classifyActivityByHour(hourText: string) {
  const [hour, minutes] = hourText.split(":").map(Number);
  const totalMinutes = hour * 60 + minutes;

  const nocturnalStart = 18 * 60 + 31;
  const nocturnalEnd = 5 * 60;

  const diurnalStart = 6 * 60 + 31;
  const diurnalEnd = 17 * 60;

  const crepuscularMorningStart = 5 * 60 + 1;
  const crepuscularMorningEnd = 6 * 60 + 30;

  const crepuscularAfternoonStart = 17 * 60 + 1;
  const crepuscularAfternoonEnd = 18 * 60 + 30;

  if (totalMinutes >= nocturnalStart || totalMinutes <= nocturnalEnd) {
    return "Nocturna";
  }

  if (totalMinutes >= diurnalStart && totalMinutes <= diurnalEnd) {
    return "Diurna";
  }

  if (
    (totalMinutes >= crepuscularMorningStart &&
      totalMinutes <= crepuscularMorningEnd) ||
    (totalMinutes >= crepuscularAfternoonStart &&
      totalMinutes <= crepuscularAfternoonEnd)
  ) {
    return "Crepuscular";
  }

  return "Sin clasificar";
}

function groupRecordsByDate(detections: Detection[]) {
  const dateCount: Record<string, number> = {};

  detections.forEach((item) => {
    dateCount[item.fecha] = (dateCount[item.fecha] || 0) + 1;
  });

  return Object.entries(dateCount)
    .map(([date, count]) => ({
      date,
      count,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function groupRecordsByHour(detections: Detection[]) {
  const hourCount: Record<string, number> = {};

  detections.forEach((item) => {
    const hour = item.hora.split(":")[0] + ":00";
    hourCount[hour] = (hourCount[hour] || 0) + 1;
  });

  return Object.entries(hourCount)
    .map(([hour, count]) => ({
      hour,
      count,
    }))
    .sort((a, b) => a.hour.localeCompare(b.hour));
}

function groupRecordsByActivity(detections: Detection[]) {
  const activityCount: Record<string, number> = {
    Nocturna: 0,
    Diurna: 0,
    Crepuscular: 0,
  };

  detections.forEach((item) => {
    const activity = classifyActivityByHour(item.hora);

    if (activityCount[activity] !== undefined) {
      activityCount[activity] += 1;
    }
  });

  return Object.entries(activityCount).map(([activity, count]) => ({
    activity,
    count,
  }));
}

export default function TemporalTrends() {
  const detections: Detection[] = data.deteccionesSimuladas || [];

  const speciesOptions = useMemo(() => {
    return Array.from(new Set(detections.map((item) => item.especie))).sort();
  }, [detections]);

  const [selectedSpecies, setSelectedSpecies] = useState("Todas");

  const filteredDetections = useMemo(() => {
    if (selectedSpecies === "Todas") {
      return detections;
    }

    return detections.filter((item) => item.especie === selectedSpecies);
  }, [selectedSpecies, detections]);

  const recordsByDate = groupRecordsByDate(filteredDetections);
  const recordsByHour = groupRecordsByHour(filteredDetections);
  const recordsByActivity = groupRecordsByActivity(filteredDetections);

  const totalFilteredRecords = filteredDetections.length;

  const mostActiveDate =
    recordsByDate.sort((a, b) => b.count - a.count)[0]?.date || "Sin datos";

  const mostActiveHour =
    recordsByHour.sort((a, b) => b.count - a.count)[0]?.hour || "Sin datos";

  const mainActivity =
    recordsByActivity.sort((a, b) => b.count - a.count)[0]?.activity ||
    "Sin datos";

  return (
    <>
      <Sidebar />

      <main className="statistics-container">
        <section className="statistics-header">
          <h1>Tendencias temporales y patrones de actividad</h1>
          <p>
            Este análisis muestra la distribución temporal de los registros,
            agrupando detecciones por fecha, hora del día y categoría de
            actividad.
          </p>
        </section>

        <section className="statistics-filter-card">
          <label htmlFor="speciesFilter">Filtrar por especie</label>

          <select
            id="speciesFilter"
            value={selectedSpecies}
            onChange={(event) => setSelectedSpecies(event.target.value)}
          >
            <option value="Todas">Todas las especies</option>

            {speciesOptions.map((species) => (
              <option key={species} value={species}>
                {species}
              </option>
            ))}
          </select>
        </section>

        <section className="statistics-summary-grid">
          <div className="statistics-card">
            <span>Registros analizados</span>
            <h2>{totalFilteredRecords}</h2>
          </div>

          <div className="statistics-card">
            <span>Fecha con más registros</span>
            <h2>{mostActiveDate}</h2>
          </div>

          <div className="statistics-card">
            <span>Hora con más actividad</span>
            <h2>{mostActiveHour}</h2>
          </div>

          <div className="statistics-card">
            <span>Actividad predominante</span>
            <h2>{mainActivity}</h2>
          </div>
        </section>

        <section className="statistics-chart-card">
          <h2>Registros por fecha</h2>

          <div className="statistics-chart">
            <ResponsiveContainer width="100%" height={330}>
              <LineChart data={recordsByDate}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  angle={-20}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  name="Registros"
                  stroke="#144a9a"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="statistics-content-grid">
          <div className="statistics-chart-card">
            <h2>Registros por hora del día</h2>

            <div className="statistics-chart">
              <ResponsiveContainer width="100%" height={330}>
                <BarChart data={recordsByHour}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" name="Registros" fill="#F28C00" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="statistics-ranking-card">
            <h2>Clasificación de actividad</h2>

            <div className="statistics-ranking-list">
              {recordsByActivity.map((item) => (
                <div className="statistics-ranking-item" key={item.activity}>
                  <div>
                    <strong>{item.activity}</strong>
                    <span>
                      {item.activity === "Nocturna" &&
                        "18:31 a 05:00"}
                      {item.activity === "Diurna" &&
                        "06:31 a 17:00"}
                      {item.activity === "Crepuscular" &&
                        "05:01 a 06:30 y 17:01 a 18:30"}
                    </span>
                  </div>

                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="statistics-chart-card">
          <h2>Comparación por categoría de actividad</h2>

          <div className="statistics-chart">
            <ResponsiveContainer width="100%" height={330}>
              <BarChart data={recordsByActivity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="activity" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" name="Registros" fill="#B85C38" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </main>
    </>
  );
}
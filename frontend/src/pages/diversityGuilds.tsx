import Sidebar from "../components/Sidebar";
import "../styles/statistics.css";

import data from "../data/datosSimulados.json";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

type Detection = {
  id: number;
  especie: string;
  estacion: string;
  fecha: string;
  hora: string;
  validado: boolean;
};

type SpeciesInfo = {
  especie: string;
  nombreCientifico: string;
  gremioTrofico: string;
  esPresaJaguar: boolean;
};

function joinDetectionsWithSpeciesInfo(
  detections: Detection[],
  speciesInfo: SpeciesInfo[]
) {
  return detections.map((detection) => {
    const info = speciesInfo.find(
      (item) => item.especie === detection.especie
    );

    return {
      ...detection,
      nombreCientifico: info?.nombreCientifico || "No registrado",
      gremioTrofico: info?.gremioTrofico || "No definido",
      esPresaJaguar: info?.esPresaJaguar || false,
    };
  });
}

function countUniqueSpecies(detections: Detection[]) {
  return new Set(detections.map((item) => item.especie)).size;
}

function countByGuild(joinedData: ReturnType<typeof joinDetectionsWithSpeciesInfo>) {
  const guildCount: Record<string, number> = {};

  joinedData.forEach((item) => {
    guildCount[item.gremioTrofico] = (guildCount[item.gremioTrofico] || 0) + 1;
  });

  return Object.entries(guildCount).map(([guild, count]) => ({
    guild,
    count,
  }));
}

function getSpeciesTable(
  detections: Detection[],
  speciesInfo: SpeciesInfo[]
) {
  const detectedSpecies = Array.from(
    new Set(detections.map((item) => item.especie))
  );

  return detectedSpecies
    .map((species) => {
      const info = speciesInfo.find((item) => item.especie === species);

      return {
        species,
        scientificName: info?.nombreCientifico || "No registrado",
        guild: info?.gremioTrofico || "No definido",
        isJaguarPrey: info?.esPresaJaguar || false,
      };
    })
    .sort((a, b) => a.species.localeCompare(b.species));
}

function getPreyRanking(
  detections: Detection[],
  speciesInfo: SpeciesInfo[]
) {
  const preySpecies = speciesInfo
    .filter((item) => item.esPresaJaguar)
    .map((item) => item.especie);

  const preyCount: Record<string, number> = {};

  detections.forEach((item) => {
    if (preySpecies.includes(item.especie)) {
      preyCount[item.especie] = (preyCount[item.especie] || 0) + 1;
    }
  });

  return Object.entries(preyCount)
    .map(([species, count]) => ({
      species,
      count,
    }))
    .sort((a, b) => b.count - a.count);
}

export default function DiversityGuilds() {
  const detections: Detection[] = data.deteccionesSimuladas || [];
  const speciesInfo: SpeciesInfo[] = data.especiesInfo || [];

  const joinedData = joinDetectionsWithSpeciesInfo(detections, speciesInfo);

  const totalSpecies = countUniqueSpecies(detections);

  const speciesTable = getSpeciesTable(detections, speciesInfo);

  const jaguarPreyDetected = speciesTable.filter(
    (item) => item.isJaguarPrey
  ).length;

  const guildData = countByGuild(joinedData);

  const preyRanking = getPreyRanking(detections, speciesInfo);

  const COLORS = ["#144A9A", "#149A8A", "#F28C00", "#B85C38", "#9ACD18"];

  return (
    <>
      <Sidebar />

      <main className="statistics-container">
        <section className="statistics-header">
          <h1>Diversidad, gremios y presas del jaguar</h1>
          <p>
            Este análisis muestra la riqueza de especies detectadas, la
            composición por gremio trófico y la disponibilidad de presas
            potenciales para el jaguar.
          </p>
        </section>

        <section className="statistics-summary-grid">
          <div className="statistics-card">
            <span>Total de especies detectadas</span>
            <h2>{totalSpecies}</h2>
          </div>

          <div className="statistics-card">
            <span>Presas potenciales detectadas</span>
            <h2>{jaguarPreyDetected}</h2>
          </div>

          <div className="statistics-card">
            <span>Gremios tróficos</span>
            <h2>{guildData.length}</h2>
          </div>

          <div className="statistics-card">
            <span>Principal presa registrada</span>
            <h2>{preyRanking[0]?.species || "Sin datos"}</h2>
          </div>
        </section>

        <section className="statistics-content-grid">
          <div className="statistics-chart-card">
            <h2>Registros por gremio trófico</h2>

            <div className="statistics-chart">
              <ResponsiveContainer width="100%" height={340}>
                <PieChart>
                  <Pie
                    data={guildData}
                    dataKey="count"
                    nameKey="guild"
                    cx="50%"
                    cy="50%"
                    outerRadius={115}
                    label
                  >
                    {guildData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="statistics-ranking-card">
            <h2>Principales presas registradas</h2>

            <div className="statistics-ranking-list">
              {preyRanking.length > 0 ? (
                preyRanking.slice(0, 5).map((item, index) => (
                  <div className="statistics-ranking-item" key={item.species}>
                    <div>
                      <strong>
                        #{index + 1} {item.species}
                      </strong>
                      <span>Registros como presa potencial</span>
                    </div>

                    <strong>{item.count}</strong>
                  </div>
                ))
              ) : (
                <p>No hay presas potenciales registradas.</p>
              )}
            </div>
          </div>
        </section>

        <section className="statistics-chart-card">
          <h2>Comparación de presas potenciales del jaguar</h2>

          <div className="statistics-chart">
            <ResponsiveContainer width="100%" height={330}>
              <BarChart data={preyRanking}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="species"
                  angle={-20}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" name="Registros" fill="#B85C38" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="statistics-table-card">
          <h2>Especies detectadas y composición ecológica</h2>

          <table className="statistics-table">
            <thead>
              <tr>
                <th>Nombre común</th>
                <th>Nombre científico</th>
                <th>Gremio trófico</th>
                <th>Presa del jaguar</th>
              </tr>
            </thead>

            <tbody>
              {speciesTable.map((item) => (
                <tr key={item.species}>
                  <td>{item.species}</td>
                  <td>
                    <em>{item.scientificName}</em>
                  </td>
                  <td>{item.guild}</td>
                  <td>
                    <span
                      className={
                        item.isJaguarPrey
                          ? "statistics-badge statistics-badge-success"
                          : "statistics-badge statistics-badge-muted"
                      }
                    >
                      {item.isJaguarPrey ? "Sí" : "No"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </>
  );
}
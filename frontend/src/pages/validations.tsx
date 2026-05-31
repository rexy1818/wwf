import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/validations.css";
import Sidebar from "../components/Sidebar";

type ValidationStatus = "Pendiente" | "Aprobado" | "Corregir" | "Falso positivo";

type ProcessedVideo = {
  id: string;
  videoName: string;
  cameraId: string;
  date: string;
  time: string;
  species: string;
  scientificName: string;
  confidence: number;
  status: ValidationStatus;
  temperature: number;
  individuals: number;
  visibleSide: string;
  location: string;
  videoUrl?: string;
  frames: {
    id: string;
    timestamp: string;
    imageUrl?: string;
    species: string;
    confidence: number;
  }[];
};

const processedVideos: ProcessedVideo[] = [
  {
    id: "VID-001",
    videoName: "cam_trampa_01_jaguar_2026_05_28.mp4",
    cameraId: "CAM-TR-001",
    date: "2026-05-28",
    time: "22:14",
    species: "Jaguar",
    scientificName: "Panthera onca",
    confidence: 94.8,
    status: "Pendiente",
    temperature: 24.6,
    individuals: 1,
    visibleSide: "Lado derecho",
    location: "Sendero Norte - Reserva",
    videoUrl: "",
    frames: [
      {
        id: "FR-001",
        timestamp: "00:00:04",
        species: "Jaguar",
        confidence: 93.2,
      },
      {
        id: "FR-002",
        timestamp: "00:00:08",
        species: "Jaguar",
        confidence: 95.1,
      },
    ],
  },
  {
    id: "VID-002",
    videoName: "cam_trampa_04_anta_2026_05_27.mp4",
    cameraId: "CAM-TR-004",
    date: "2026-05-27",
    time: "03:42",
    species: "Anta",
    scientificName: "Tapirus terrestris",
    confidence: 89.5,
    status: "Aprobado",
    temperature: 22.1,
    individuals: 1,
    visibleSide: "Frontal",
    location: "Quebrada Central",
    videoUrl: "",
    frames: [
      {
        id: "FR-003",
        timestamp: "00:00:03",
        species: "Anta",
        confidence: 88.7,
      },
      {
        id: "FR-004",
        timestamp: "00:00:06",
        species: "Anta",
        confidence: 91.3,
      },
    ],
  },
  {
    id: "VID-003",
    videoName: "cam_trampa_02_ocelote_2026_05_26.mp4",
    cameraId: "CAM-TR-002",
    date: "2026-05-26",
    time: "19:33",
    species: "Ocelote",
    scientificName: "Leopardus pardalis",
    confidence: 76.4,
    status: "Corregir",
    temperature: 25.3,
    individuals: 1,
    visibleSide: "Lado izquierdo",
    location: "Bosque Bajo",
    videoUrl: "",
    frames: [
      {
        id: "FR-005",
        timestamp: "00:00:05",
        species: "Ocelote",
        confidence: 74.9,
      },
      {
        id: "FR-006",
        timestamp: "00:00:09",
        species: "Ocelote",
        confidence: 78.2,
      },
    ],
  },
  {
    id: "VID-004",
    videoName: "cam_trampa_03_movimiento_2026_05_25.mp4",
    cameraId: "CAM-TR-003",
    date: "2026-05-25",
    time: "11:08",
    species: "No confirmado",
    scientificName: "No determinado",
    confidence: 61.2,
    status: "Falso positivo",
    temperature: 28.4,
    individuals: 0,
    visibleSide: "No visible",
    location: "Camino Secundario",
    videoUrl: "",
    frames: [
      {
        id: "FR-007",
        timestamp: "00:00:02",
        species: "Movimiento vegetal",
        confidence: 59.8,
      },
      {
        id: "FR-008",
        timestamp: "00:00:05",
        species: "No confirmado",
        confidence: 62.5,
      },
    ],
  },
];

export default function Validations() {
  const navigate = useNavigate();

  const [dateFilter, setDateFilter] = useState("");
  const [cameraFilter, setCameraFilter] = useState("Todos");
  const [speciesFilter, setSpeciesFilter] = useState("Todos");
  const [statusFilter, setStatusFilter] = useState("Todos");

  const cameras = useMemo(() => {
    return ["Todos", ...Array.from(new Set(processedVideos.map((video) => video.cameraId)))];
  }, []);

  const species = useMemo(() => {
    return ["Todos", ...Array.from(new Set(processedVideos.map((video) => video.species)))];
  }, []);

  const statuses = ["Todos", "Pendiente", "Aprobado", "Corregir", "Falso positivo"];

  const filteredVideos = useMemo(() => {
    return processedVideos.filter((video) => {
      const matchesDate = dateFilter ? video.date === dateFilter : true;
      const matchesCamera = cameraFilter === "Todos" || video.cameraId === cameraFilter;
      const matchesSpecies = speciesFilter === "Todos" || video.species === speciesFilter;
      const matchesStatus = statusFilter === "Todos" || video.status === statusFilter;

      return matchesDate && matchesCamera && matchesSpecies && matchesStatus;
    });
  }, [dateFilter, cameraFilter, speciesFilter, statusFilter]);

  const summary = useMemo(() => {
    return {
      processed: processedVideos.length,
      pending: processedVideos.filter((video) => video.status === "Pendiente").length,
      approved: processedVideos.filter((video) => video.status === "Aprobado").length,
      falsePositive: processedVideos.filter((video) => video.status === "Falso positivo").length,
    };
  }, []);

  const getStatusClass = (status: ValidationStatus) => {
    switch (status) {
      case "Pendiente":
        return "status-pending";
      case "Aprobado":
        return "status-approved";
      case "Corregir":
        return "status-correct";
      case "Falso positivo":
        return "status-false";
      default:
        return "";
    }
  };

  return (
    <>
    <Sidebar/>
    
    <main className="validations-page">
      <section className="validations-header">
        <div>
          <span className="validations-kicker">Módulo científico</span>
          <h1>Validaciones</h1>
          <p>
            Revisa los videos procesados por el modelo antes de confirmar los
            registros científicos.
          </p>
        </div>
      </section>

      <section className="validations-summary-grid">
        <article className="validation-summary-card">
          <span>Videos procesados</span>
          <strong>{summary.processed}</strong>
        </article>

        <article className="validation-summary-card">
          <span>Pendientes</span>
          <strong>{summary.pending}</strong>
        </article>

        <article className="validation-summary-card">
          <span>Aprobados</span>
          <strong>{summary.approved}</strong>
        </article>

        <article className="validation-summary-card">
          <span>Falsos positivos</span>
          <strong>{summary.falsePositive}</strong>
        </article>
      </section>

      <section className="validations-filters-card">
        <div className="validations-filters-header">
          <h2>Videos procesados por IA</h2>
          <p>{filteredVideos.length} registros encontrados</p>
        </div>

        <div className="validations-filters-grid">
          <label>
            Fecha
            <input
              type="date"
              value={dateFilter}
              onChange={(event) => setDateFilter(event.target.value)}
            />
          </label>

          <label>
            Cámara
            <select
              value={cameraFilter}
              onChange={(event) => setCameraFilter(event.target.value)}
            >
              {cameras.map((camera) => (
                <option key={camera} value={camera}>
                  {camera}
                </option>
              ))}
            </select>
          </label>

          <label>
            Especie
            <select
              value={speciesFilter}
              onChange={(event) => setSpeciesFilter(event.target.value)}
            >
              {species.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label>
            Estado
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="validations-table-card">
        <div className="validations-table-wrapper">
          <table className="validations-table">
            <thead>
              <tr>
                <th>Video</th>
                <th>Cámara</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Especie predicha</th>
                <th>Confianza IA</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {filteredVideos.map((video) => (
                <tr key={video.id}>
                  <td>
                    <div className="video-name-cell">
                      <strong>{video.videoName}</strong>
                      <span>{video.scientificName}</span>
                    </div>
                  </td>
                  <td>{video.cameraId}</td>
                  <td>{video.date}</td>
                  <td>{video.time}</td>
                  <td>{video.species}</td>
                  <td>{video.confidence.toFixed(1)}%</td>
                  <td>
                    <span className={`validation-status ${getStatusClass(video.status)}`}>
                      {video.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="review-button"
                      onClick={() => navigate(`/validaciones/${video.id}`)}
                    >
                      Revisar
                    </button>
                  </td>
                </tr>
              ))}

              {filteredVideos.length === 0 && (
                <tr>
                  <td colSpan={8}>
                    <div className="empty-validations">
                      No se encontraron videos con los filtros seleccionados.
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
    </>
  );
}
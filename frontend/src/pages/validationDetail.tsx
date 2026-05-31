import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "../styles/validationDetail.css";
import Sidebar from "../components/Sidebar";

type ValidationStatus = "Pendiente" | "Aprobado" | "Corregir" | "Falso positivo";

type Frame = {
  id: string;
  timestamp: string;
  imageUrl?: string;
  species: string;
  confidence: number;
};

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
  notes?: string;
  videoUrl?: string;
  frames: Frame[];
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
    notes: "Detección nocturna con buena visibilidad lateral. Confirmar patrón de manchas.",
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
      {
        id: "FR-003",
        timestamp: "00:00:12",
        species: "Jaguar",
        confidence: 94.4,
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
    notes: "Registro validado. Individuo completo en plano frontal.",
    videoUrl: "",
    frames: [
      {
        id: "FR-004",
        timestamp: "00:00:03",
        species: "Anta",
        confidence: 88.7,
      },
      {
        id: "FR-005",
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
    notes: "La confianza es media. Revisar si corresponde a ocelote o margay.",
    videoUrl: "",
    frames: [
      {
        id: "FR-006",
        timestamp: "00:00:05",
        species: "Ocelote",
        confidence: 74.9,
      },
      {
        id: "FR-007",
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
    notes: "Probable movimiento de vegetación por viento. No se observa animal.",
    videoUrl: "",
    frames: [
      {
        id: "FR-008",
        timestamp: "00:00:02",
        species: "Movimiento vegetal",
        confidence: 59.8,
      },
      {
        id: "FR-009",
        timestamp: "00:00:05",
        species: "No confirmado",
        confidence: 62.5,
      },
    ],
  },
];

export default function ValidationDetail() {
  const navigate = useNavigate();
  const { id } = useParams();

  const video = useMemo(() => {
    return processedVideos.find((item) => item.id === id);
  }, [id]);

  const [selectedFrameId, setSelectedFrameId] = useState(
    video?.frames[0]?.id ?? ""
  );

  const selectedFrame = video?.frames.find((frame) => frame.id === selectedFrameId);

  const getStatusClass = (status: ValidationStatus) => {
    switch (status) {
      case "Pendiente":
        return "detail-status-pending";
      case "Aprobado":
        return "detail-status-approved";
      case "Corregir":
        return "detail-status-correct";
      case "Falso positivo":
        return "detail-status-false";
      default:
        return "";
    }
  };

  if (!video) {
    return (
      <main className="validation-detail-page">
        <section className="validation-not-found">
          <h1>Video no encontrado</h1>
          <p>No existe un registro de validación con el identificador solicitado.</p>
          <button onClick={() => navigate("/validaciones")}>Volver a validaciones</button>
        </section>
      </main>
    );
  }

  return (

    <>
    <Sidebar/>
    <main className="validation-detail-page">
      <header className="validation-detail-header">
        <button className="back-button" onClick={() => navigate("/validaciones")}>
          ← Volver
        </button>

        <div className="validation-detail-title">
          <h1>{video.videoName}</h1>
          <div className="validation-detail-meta">
            <span>{video.cameraId}</span>
            <span>{video.date}</span>
            <span>{video.time}</span>
          </div>
        </div>

        <span className={`detail-status ${getStatusClass(video.status)}`}>
          {video.status}
        </span>
      </header>

      <section className="video-review-area">
        {video.videoUrl ? (
          <video className="main-video" src={video.videoUrl} controls />
        ) : (
          <div className="video-placeholder">
            <div>
              <span>Vista de video procesado</span>
              <strong>{video.videoName}</strong>
              <p>
                Este espacio está preparado para renderizar un video real usando
                la propiedad <code>videoUrl</code>.
              </p>
            </div>
          </div>
        )}
      </section>

      <section className="frames-section">
        <div className="section-heading">
          <h2>Fotogramas extraídos</h2>
          <p>
            Selecciona un fotograma para revisar la evidencia visual generada por
            el modelo.
          </p>
        </div>

        <div className="frames-carousel">
          {video.frames.map((frame, index) => (
            <button
              key={frame.id}
              className={`frame-card ${
                selectedFrameId === frame.id ? "frame-card-active" : ""
              }`}
              onClick={() => setSelectedFrameId(frame.id)}
            >
              {frame.imageUrl ? (
                <img src={frame.imageUrl} alt={`Fotograma ${frame.timestamp}`} />
              ) : (
                <div className="frame-placeholder">
                  <span>Frame {index + 1}</span>
                </div>
              )}

              <div className="frame-info">
                <strong>{frame.timestamp}</strong>
                <span>{frame.species}</span>
                <small>{frame.confidence.toFixed(1)}% IA</small>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="scientific-validation-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">Validación científica</span>
            <h2>Confirmación del registro</h2>
          </div>

          {selectedFrame && (
            <div className="selected-frame-chip">
              Fotograma seleccionado: {selectedFrame.timestamp}
            </div>
          )}
        </div>

        <div className="scientific-grid">
          <article>
            <span>Predicción IA</span>
            <strong>{video.species}</strong>
          </article>

          <article>
            <span>Especie</span>
            <strong>{video.species}</strong>
          </article>

          <article>
            <span>Nombre científico</span>
            <strong className="italic-value">{video.scientificName}</strong>
          </article>

          <article>
            <span>Confianza</span>
            <strong>{video.confidence.toFixed(1)}%</strong>
          </article>

          <article>
            <span>Cámara</span>
            <strong>{video.cameraId}</strong>
          </article>

          <article>
            <span>Fecha</span>
            <strong>{video.date}</strong>
          </article>

          <article>
            <span>Hora</span>
            <strong>{video.time}</strong>
          </article>

          <article>
            <span>Temperatura</span>
            <strong>{video.temperature} °C</strong>
          </article>

          <article>
            <span>Individuos</span>
            <strong>{video.individuals}</strong>
          </article>

          <article>
            <span>Lado visible</span>
            <strong>{video.visibleSide}</strong>
          </article>

          <article>
            <span>Ubicación</span>
            <strong>{video.location}</strong>
          </article>

          <article className="notes-card">
            <span>Observaciones / notas</span>
            <strong>{video.notes || "Sin observaciones registradas."}</strong>
          </article>
        </div>

        <div className="validation-actions">
          <button className="approve-action">Aprobar detección</button>
          <button className="correct-action">Corregir especie</button>
          <button className="false-positive-action">Marcar falso positivo</button>
        </div>
      </section>
    </main>
    </>

  );
}
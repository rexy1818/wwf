import { useMemo, useRef, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/video.css";
import { Upload, Clock, Calendar } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

interface VideoResult {
  video: string;
  species: string;
  scientific_name: string;
  confidence: number;
  image: string;
  date: string;
  time: string;
}

export default function Videos() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<VideoResult[]>([]);
  const [loading, setLoading] = useState(false);

  const bestResultsPerSpecies = useMemo(() => {
    const groups: Record<string, VideoResult> = {};

    results.forEach((item) => {
      const speciesName = item.species?.toLowerCase() || "";
      
      // FILTRO: Ignorar si es "review_required" o si no hay especie
      if (speciesName === "review_required" || !speciesName) return;

      // Lógica de mejor resultado por especie
      if (!groups[speciesName] || item.confidence > groups[speciesName].confidence) {
        groups[speciesName] = item;
      }
    });

    return Object.values(groups);
  }, [results]);

  const handleSelectVideos = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;
    setFiles(Array.from(event.target.files));
  };

  const uploadAndProcess = async () => {
    if (files.length === 0) return;
    try {
      setLoading(true);
      const processedData: VideoResult[] = [];

      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);

        const uploadRes = await fetch(`${API_URL}/videos/upload`, { method: "POST", body: formData });
        const uploadData = await uploadRes.json();

        const processRes = await fetch(`${API_URL}/videos/process/${uploadData.filename}`);
        const processData = await processRes.json();

        if (processData.success) {
          const det = processData.result?.best_detection;
          const meta = det?.camera_metadata;

          processedData.push({
            video: processData.video,
            species: det?.species ?? "",
            scientific_name: det?.scientific_name ?? "N/A",
            confidence: det?.species_confidence ?? 0,
            image: processData.result?.best_image ?? "",
            date: meta?.date ?? "Sin fecha",
            time: meta?.time ?? "Sin hora",
          });
        }
      }
      setResults(processedData);
    } catch (error) {
      console.error(error);
      alert("Error en el procesamiento");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Sidebar />
      <main className="videos-container">
        <div className="videos-header">
          <h1>Registro de Biodiversidad</h1>
          <p>Resultados confirmados de avistamientos de fauna silvestre.</p>
        </div>

        <input ref={fileInputRef} type="file" multiple style={{ display: "none" }} onChange={handleSelectVideos} />

        <section className="upload-section">
          <div className="upload-box">
            <Upload size={32} color="#2d5a27" />
            <div style={{ marginTop: "10px" }}>
              <button className="upload-btn" onClick={() => fileInputRef.current?.click()}>
                Cargar Videos
              </button>
              {files.length > 0 && (
                <button className="upload-btn" onClick={uploadAndProcess} disabled={loading} style={{ marginLeft: "10px", backgroundColor: "#1a4731" }}>
                  {loading ? "Analizando..." : "Iniciar Identificación"}
                </button>
              )}
            </div>
          </div>
        </section>

        <section className="videos-table">
          <table>
            <thead>
              <tr>
                <th style={{ width: "250px" }}>Registro Visual</th>
                <th>Especie Detectada</th>
                <th>Fecha y Hora del Avistamiento</th>
              </tr>
            </thead>
            <tbody>
              {bestResultsPerSpecies.length > 0 ? (
                bestResultsPerSpecies.map((item, index) => (
                  <tr key={index}>
                    <td>
                      <img 
                        src={item.image.startsWith("storage/") ? `${API_URL}/${item.image}` : `${API_URL}/storage/${item.image}`} 
                        alt={item.species} 
                        style={{ width: "100%", maxWidth: "220px", borderRadius: "6px", display: "block" }}
                      />
                    </td>
                    <td>
                      <div className="species-info">
                        <h2 style={{ margin: 0, color: "#1a4731", textTransform: "uppercase", fontSize: "1.2rem" }}>
                          {item.species}
                        </h2>
                        <p style={{ margin: "4px 0", color: "#666", fontStyle: "italic", fontSize: "1rem" }}>
                          {item.scientific_name}
                        </p>
                      </div>
                    </td>
                    <td>
                      <div className="time-info" style={{ color: "#444" }}>
                        <p style={{ display: "flex", alignItems: "center", gap: "8px", margin: "4px 0" }}>
                          <Calendar size={16} /> {item.date}
                        </p>
                        <p style={{ display: "flex", alignItems: "center", gap: "8px", margin: "4px 0" }}>
                          <Clock size={16} /> {item.time}
                        </p>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} style={{ textAlign: "center", padding: "50px", color: "#999" }}>
                    No hay especies confirmadas para mostrar.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      </main>
    </>
  );
}
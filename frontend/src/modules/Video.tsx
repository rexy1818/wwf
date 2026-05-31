import { useEffect, useMemo, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type Detection = {
  camera_id?: string
  especie?: string
  species?: string
  fecha?: string
  hora?: string
  temperatura_c?: number
  confianza?: number
  confidence?: number
  nombre_archivo?: string
  ruta_evidencia_final?: string
}

type Analysis = {
  video_id: string
  video_name?: string
  detecciones?: Detection[]
  estadisticas?: {
    total_animales?: number
    especies_encontradas?: string[]
  }
  excel_files?: Record<string, string>
  procesado_en?: string
}

type UploadResponse = {
  filename: string
  analysis: Analysis
}

type BatchResponse = {
  total_recibidos: number
  total_procesados: number
  total_errores: number
  results: UploadResponse[]
}

type AnalysisSummary = {
  video_id: string
  video_name?: string
  total_detecciones?: number
  especies_encontradas?: string[]
}

type OcrStatus = 'queued' | 'running' | 'done' | 'error'

function hasCompleteOcr(detection: Detection) {
  return Boolean(detection.fecha && detection.hora && detection.camera_id && detection.camera_id !== 'UNKNOWN')
}

function evidenceUrl(detection: Detection) {
  const path = detection.ruta_evidencia_final
  if (!path) return ''

  const parts = path.replaceAll('\\', '/').split('/')
  const resultsIndex = parts.findIndex((part) => part.toLowerCase() === 'resultados')
  if (resultsIndex < 0 || parts.length < resultsIndex + 4) return ''

  const cameraId = parts[resultsIndex + 1]
  const species = parts[resultsIndex + 2]
  const filename = parts.slice(resultsIndex + 3).join('/')
  return `${API_URL}/analyze/file/${encodeURIComponent(cameraId)}/${encodeURIComponent(species)}/${encodeURIComponent(filename)}`
}

function excelUrl(cameraId: string) {
  return `${API_URL}/analyze/excel/${encodeURIComponent(cameraId)}`
}

function formatConfidence(value?: number) {
  if (value === undefined || value === null) return '-'
  return `${Math.round(value * 1000) / 10}%`
}

export function VideoModule() {
  const [files, setFiles] = useState<File[]>([])
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [ocrStatus, setOcrStatus] = useState<Record<number, OcrStatus>>({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const autoOcrStarted = useRef(new Set<string>())

  const detections = selectedAnalysis?.detecciones ?? []
  const excelCameras = useMemo(() => Object.keys(selectedAnalysis?.excel_files ?? {}), [selectedAnalysis])
  const ocrCompleted = detections.filter(hasCompleteOcr).length
  const ocrTotal = detections.length
  const ocrPending = Math.max(ocrTotal - ocrCompleted, 0)

  async function loadAnalyses() {
    setError('')
    const response = await fetch(`${API_URL}/analyze/list`)
    if (!response.ok) throw new Error(await response.text())
    setAnalyses(await response.json())
  }

  async function loadAnalysis(videoId: string) {
    setError('')
    const response = await fetch(`${API_URL}/analyze/results/${videoId}`)
    if (!response.ok) throw new Error(await response.text())
    setSelectedAnalysis(await response.json())
  }

  async function uploadVideos() {
    if (!files.length) {
      setError('Selecciona al menos un video.')
      return
    }

    setIsUploading(true)
    setError('')
    setMessage('')

    try {
      const formData = new FormData()
      files.forEach((file) => formData.append(files.length === 1 ? 'file' : 'files', file))
      const endpoint = files.length === 1 ? '/analyze/upload' : '/analyze/upload/batch'
      const response = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData })
      if (!response.ok) throw new Error(await response.text())

      if (files.length === 1) {
        const data = (await response.json()) as UploadResponse
        setSelectedAnalysis(data.analysis)
        setMessage(`Detecciones listas para ${data.filename}. OCR completandose en segundo plano.`)
      } else {
        const data = (await response.json()) as BatchResponse
        setSelectedAnalysis(data.results[0]?.analysis ?? null)
        setMessage(`Detecciones listas: ${data.total_procesados} de ${data.total_recibidos}. OCR completandose en segundo plano.`)
      }

      setFiles([])
      await loadAnalyses()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error procesando video')
    } finally {
      setIsUploading(false)
    }
  }

  async function requestOcr(videoId: string, index: number) {
    setOcrStatus((current) => ({ ...current, [index]: 'running' }))
    setError('')

    try {
      const response = await fetch(`${API_URL}/analyze/detection/${videoId}/${index}/extract-ocr`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error(await response.text())
      const updatedDetection = (await response.json()) as Detection

      setSelectedAnalysis((current) => {
        if (!current) return current
        const updated = [...(current.detecciones ?? [])]
        updated[index] = updatedDetection
        return { ...current, detecciones: updated }
      })
      setOcrStatus((current) => ({ ...current, [index]: 'done' }))
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo extraer OCR')
      setOcrStatus((current) => ({ ...current, [index]: 'error' }))
      return false
    }
  }

  async function extractOcr(index: number) {
    if (!selectedAnalysis?.video_id) return
    await requestOcr(selectedAnalysis.video_id, index)
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []))
  }

  useEffect(() => {
    loadAnalyses().catch((err) => setError(err instanceof Error ? err.message : 'No se pudo cargar el listado'))
  }, [])

  useEffect(() => {
    const analysis = selectedAnalysis
    if (!analysis?.video_id || autoOcrStarted.current.has(analysis.video_id)) return

    const missingIndexes = (analysis.detecciones ?? [])
      .map((detection, index) => ({ detection, index }))
      .filter(({ detection }) => !hasCompleteOcr(detection))
      .map(({ index }) => index)

    if (!missingIndexes.length) return

    const videoId = analysis.video_id
    autoOcrStarted.current.add(videoId)
    setOcrStatus((current) => {
      const next = { ...current }
      missingIndexes.forEach((index) => {
        next[index] = next[index] === 'done' ? 'done' : 'queued'
      })
      return next
    })

    let cancelled = false
    async function runBackgroundOcr() {
      for (const index of missingIndexes) {
        if (cancelled) return
        await requestOcr(videoId, index)
      }
      if (!cancelled) setMessage('OCR completado para las detecciones disponibles.')
    }

    runBackgroundOcr()

    return () => {
      cancelled = true
    }
  }, [selectedAnalysis?.video_id])

  return (
    <section className="module-panel video-module">
      <div className="module-header">
        <div>
          <span className="module-kicker">Procesamiento real</span>
          <h2>Videos</h2>
        </div>
        <button type="button" className="secondary-button" onClick={() => loadAnalyses().catch((err) => setError(String(err)))}>
          Actualizar
        </button>
      </div>

      <div className="video-upload">
        <label className="file-input">
          <input type="file" accept="video/*" multiple onChange={onFileChange} disabled={isUploading} />
          <span>{files.length ? `${files.length} video(s) seleccionado(s)` : 'Seleccionar videos'}</span>
        </label>
        <button type="button" className="primary-button" onClick={uploadVideos} disabled={isUploading || !files.length}>
          {isUploading ? 'Procesando...' : 'Procesar'}
        </button>
      </div>

      {isUploading && (
        <div className="job-banner">
          <span className="spinner" aria-hidden="true" />
          <div>
            <strong>Procesando deteccion y clasificacion</strong>
            <p>La tabla se mostrara cuando el backend devuelva las evidencias.</p>
          </div>
        </div>
      )}

      {(message || error) && <div className={error ? 'notice error' : 'notice'}>{error || message}</div>}

      <div className="video-grid">
        <aside className="analysis-list">
          <h3>Analisis guardados</h3>
          {analyses.length === 0 && <p className="muted">Sin analisis guardados.</p>}
          {analyses.map((analysis) => (
            <button
              key={analysis.video_id}
              type="button"
              className={`analysis-item ${selectedAnalysis?.video_id === analysis.video_id ? 'active' : ''}`}
              onClick={() => loadAnalysis(analysis.video_id).catch((err) => setError(String(err)))}
            >
              <strong>{analysis.video_name ?? analysis.video_id}</strong>
              <span>{analysis.total_detecciones ?? 0} detecciones</span>
              <small>{(analysis.especies_encontradas ?? []).join(', ') || 'Sin especie'}</small>
            </button>
          ))}
        </aside>

        <div className="video-results">
          {!selectedAnalysis ? (
            <div className="empty-state">
              <h3>Selecciona o procesa un video</h3>
              <p>Los resultados reales apareceran aqui.</p>
            </div>
          ) : (
            <>
              <div className="summary-row">
                <div>
                  <span>Total</span>
                  <strong>{selectedAnalysis.estadisticas?.total_animales ?? detections.length}</strong>
                </div>
                <div>
                  <span>Especies</span>
                  <strong>{(selectedAnalysis.estadisticas?.especies_encontradas ?? []).join(', ') || '-'}</strong>
                </div>
                <div>
                  <span>Excel</span>
                  <strong>{excelCameras.length || '-'}</strong>
                </div>
              </div>

              {excelCameras.length > 0 && (
                <div className="excel-row">
                  {excelCameras.map((cameraId) => (
                    <a key={cameraId} href={excelUrl(cameraId)} target="_blank" rel="noreferrer">
                      Excel {cameraId}
                    </a>
                  ))}
                </div>
              )}

              {ocrTotal > 0 && ocrPending > 0 && (
                <div className="ocr-progress">
                  <div>
                    <span className="spinner small" aria-hidden="true" />
                    <strong>OCR en segundo plano</strong>
                    <small>
                      {ocrCompleted} de {ocrTotal} detecciones con Camera ID, fecha, hora y temperatura.
                    </small>
                  </div>
                  <progress value={ocrCompleted} max={ocrTotal} />
                </div>
              )}

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Evidencia</th>
                      <th>Especie</th>
                      <th>Camara</th>
                      <th>Fecha</th>
                      <th>Hora</th>
                      <th>Temp. C</th>
                      <th>Confianza</th>
                      <th>OCR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detections.map((detection, index) => {
                      const image = evidenceUrl(detection)
                      const hasOcr = hasCompleteOcr(detection)
                      const rowOcrStatus = ocrStatus[index]
                      return (
                        <tr key={`${detection.nombre_archivo ?? index}-${index}`}>
                          <td>
                            {image ? (
                              <a href={image} target="_blank" rel="noreferrer">
                                <img src={image} alt={detection.nombre_archivo ?? 'Evidencia'} />
                              </a>
                            ) : (
                              <span className="muted">Sin imagen</span>
                            )}
                          </td>
                          <td>{detection.especie ?? detection.species ?? '-'}</td>
                          <td>{detection.camera_id ?? 'UNKNOWN'}</td>
                          <td>{detection.fecha ?? '-'}</td>
                          <td>{detection.hora ?? '-'}</td>
                          <td>{detection.temperatura_c ?? '-'}</td>
                          <td>{formatConfidence(detection.confianza ?? detection.confidence)}</td>
                          <td>
                            {hasOcr ? (
                              <span className="status-ok">OK</span>
                            ) : rowOcrStatus === 'queued' ? (
                              <span className="status-muted">En cola</span>
                            ) : rowOcrStatus === 'running' ? (
                              <span className="status-loading">
                                <span className="spinner tiny" aria-hidden="true" />
                                Leyendo
                              </span>
                            ) : (
                              <button
                                type="button"
                                className="inline-button"
                                onClick={() => extractOcr(index)}
                                disabled={false}
                              >
                                {rowOcrStatus === 'error' ? 'Reintentar' : 'Extraer'}
                              </button>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

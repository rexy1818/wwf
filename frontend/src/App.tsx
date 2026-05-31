import { VideoModule } from './modules/Video'
import './App.css'

const simulatedModules = [
  {
    title: 'Camaras',
    value: '12',
    detail: '8 activas, 4 pendientes',
  },
  {
    title: 'Especies',
    value: '6',
    detail: 'Jaguar, Tapir, Puma, Ocelote',
  },
  {
    title: 'Alertas',
    value: '3',
    detail: 'Revisar OCR incompleto',
  },
  {
    title: 'Reportes',
    value: '18',
    detail: 'Excels generados este mes',
  },
]

function App() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">WWF camaras trampa</p>
          <h1>Panel de monitoreo</h1>
        </div>
      </header>

      <section className="mock-grid">
        {simulatedModules.map((module) => (
          <article className="mock-card" key={module.title}>
            <span>{module.title}</span>
            <strong>{module.value}</strong>
            <p>{module.detail}</p>
          </article>
        ))}
      </section>

      <VideoModule />
    </main>
  )
}

export default App

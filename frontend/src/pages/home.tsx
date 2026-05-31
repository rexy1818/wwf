import "../styles/home.css";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

import {
  Camera,
  PawPrint,
  Trees,
  TrendingUp,
} from "lucide-react";

const slides = [
  "/wwf1.png",
  "/wwf2.png",
  "/wwf3.png",
];

export default function Home() {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) =>
        prev === slides.length - 1 ? 0 : prev + 1
      );
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const nextSlide = () => {
    setCurrentSlide((prev) =>
      prev === slides.length - 1 ? 0 : prev + 1
    );
  };

  const prevSlide = () => {
    setCurrentSlide((prev) =>
      prev === 0 ? slides.length - 1 : prev - 1
    );
  };

  return (
    <div className="home">
      {/* NAVBAR */}
      <nav className="navbar">
        <div className="logo-container">
          <img
            src="/logowwf.png"
            alt="WWF"
            className="logo"
          />
          <span>WWF</span>
        </div>

        <ul>
          <li>Explorar Datos</li>
          <li>Tecnología</li>
          <li>Historias</li>
          <li>
            <Link to="/login" className="nav-link">
              Login
            </Link>
          </li>
        </ul>
      </nav>

      {/* HERO */}
      <section
        className="hero"
        style={{
          backgroundImage: `url(${slides[currentSlide]})`,
        }}
      >
        <div className="overlay"></div>

        {/* Flecha izquierda */}
        <button
          className="carousel-arrow left"
          onClick={prevSlide}
          aria-label="Anterior"
        >
          ❮
        </button>

        {/* Flecha derecha */}
        <button
          className="carousel-arrow right"
          onClick={nextSlide}
          aria-label="Siguiente"
        >
          ❯
        </button>

        <div className="hero-content">
          <motion.h1
            key={`title-${currentSlide}`}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Un futuro donde el ser humano,
            <span>viva en armonía con la naturaleza</span>
          </motion.h1>

          <motion.p
            key={`text-${currentSlide}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            Monitoreamos, analizamos y protegemos la
            biodiversidad animal utilizando modelos de IA.
          </motion.p>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Explorar Impacto
          </motion.button>

          <div className="carousel-dots">
            {slides.map((_, index) => (
              <span
                key={index}
                className={
                  index === currentSlide
                    ? "dot active"
                    : "dot"
                }
                onClick={() => setCurrentSlide(index)}
              />
            ))}
          </div>
        </div>

        {/* IMPACTO FLOTANTE */}
        <motion.div
          className="impact-card"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="stat">
            <Camera size={32} />
            <h3>1M+</h3>
            <span>Imágenes Analizadas</span>
          </div>

          <div className="stat">
            <PawPrint size={32} />
            <h3>500+</h3>
            <span>Especies Identificadas</span>
          </div>

          <div className="stat">
            <Trees size={32} />
            <h3>10M</h3>
            <span>Hectáreas Monitoreadas</span>
          </div>

          <div className="stat">
            <TrendingUp size={32} />
            <h3>85%</h3>
            <span>Precisión IA</span>
          </div>
        </motion.div>
      </section>

      {/* HISTORIAS */}
      <section className="stories">
        <h2>Historias de Campo</h2>

        <div className="stories-grid">
          <div className="story-card">
            <img
              src="https://images.unsplash.com/photo-1546182990-dffeafbe841d"
              alt=""
            />

            <div className="story-content">
              <h3>Monitoreo de Felinos</h3>
              <p>Bosques Tropicales</p>
            </div>
          </div>

          <div className="story-card">
            <img
              src="/jaguar.png"
              alt=""
            />

            <div className="story-content">
              <h3>Monitoreo de felinos</h3>
              <p>Bosques</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
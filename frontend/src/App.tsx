import { Routes, Route } from "react-router-dom";

import Home from "./pages/home";
import Login from "./pages/login";
import Dashboard from "./pages/dashboard";
import Videos from "./pages/videos";

import Statistics from "./pages/statistics";
import FrequencyAbundance from "./pages/frequencyAbundance";
import DiversityGuilds from "./pages/diversityGuilds";
import TemporalTrends from "./pages/temporalTrends";
import Validations from "./pages/validations";
import ValidationDetail from "./pages/validationDetail";


function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/videos" element={<Videos />} />
      <Route path="/statistics" element={<Statistics />} />
      <Route path="/statistics/frequency" element={<FrequencyAbundance />} />
      <Route path="/statistics/diversity" element={<DiversityGuilds />} />
      <Route path="/statistics/trends" element={<TemporalTrends />} />
      <Route path="/validaciones" element={<Validations />} />
      <Route path="/validaciones" element={<Validations />} />
      <Route path="/validaciones/:id" element={<ValidationDetail />} />
    </Routes>
  );
}

export default App;
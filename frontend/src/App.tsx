import { NavLink, Route, Routes } from "react-router-dom";
import { useTheme } from "./hooks/useTheme";
import { LabelPage } from "./pages/LabelPage";
import { MetricsPage } from "./pages/MetricsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { PredictPage } from "./pages/PredictPage";
import { TrainPage } from "./pages/TrainPage";

export default function App() {
  const [theme, toggle] = useTheme();
  return (
    <div className="layout">
      <nav className="sidebar" aria-label="Main">
        <h1>🏷️ Doc Classifier</h1>
        <NavLink to="/" end>
          1 · Label
        </NavLink>
        <NavLink to="/train">2 · Train</NavLink>
        <NavLink to="/metrics">3 · Metrics</NavLink>
        <NavLink to="/predict">4 · Predict</NavLink>
        <NavLink to="/models">Models</NavLink>
        <span className="spacer" />
        <button type="button" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? "☀ Light" : "🌙 Dark"}
        </button>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<LabelPage />} />
          <Route path="/train" element={<TrainPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/predict" element={<PredictPage />} />
          <Route path="/models" element={<ModelsPage />} />
        </Routes>
      </main>
    </div>
  );
}

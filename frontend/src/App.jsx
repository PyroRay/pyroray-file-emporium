import { Routes, Route } from "react-router-dom";
import Banner from "./components/Banner";
import HomePage from "./pages/HomePage";
import PdfToolPage from "./pages/PdfToolPage";
import FileToolPage from "./pages/FileToolPage";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      <Banner />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/pdf-tool" element={<PdfToolPage />} />
          <Route path="/file-tool" element={<FileToolPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;

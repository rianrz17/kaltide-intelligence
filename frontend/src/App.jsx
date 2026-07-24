import { MapContainer, TileLayer } from "react-leaflet";
import RingkasanStatus from "./components/RingkasanStatus.jsx";
import GenanganLayer from "./components/GenanganLayer.jsx";

// Titik tengah peta: dipilih agar mencakup seluruh 6 wilayah
// (Balikpapan, PPU, Kukar/Anggana, Samarinda, Bontang, Berau)
const PUSAT_PETA = [0.2, 117.2];

/**
 * Komponen utama dashboard KALTIDE Intelligence.
 * Menampilkan peta dasar + kartu ringkasan status + layer genangan
 * berwarna (hijau/kuning/oranye/merah) per wilayah, berdasarkan hasil
 * live dari Flood Simulation Engine.
 */
function App() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header style={{ padding: "12px 20px", background: "#0b3d59", color: "white" }}>
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>KALTIDE Intelligence</h1>
        <p style={{ margin: 0, fontSize: "0.85rem", opacity: 0.85 }}>
          Kalimantan Tidal Flood Intelligence System
        </p>
      </header>

      <RingkasanStatus />

      <div style={{ flex: 1 }}>
        <MapContainer center={PUSAT_PETA} zoom={7} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <GenanganLayer />
        </MapContainer>
      </div>
    </div>
  );
}

export default App;

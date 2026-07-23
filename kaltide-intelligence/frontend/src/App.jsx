import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import RingkasanStatus from "./components/RingkasanStatus.jsx";

// Titik tengah peta: sekitar wilayah MVP (Balikpapan-PPU-Kukar)
const PUSAT_PETA = [-0.9, 117.0];

/**
 * Komponen utama dashboard KALTIDE Intelligence.
 * Tahap 1: menampilkan peta dasar + kartu ringkasan status rob.
 * Layer DEM, genangan, dan time slider akan ditambahkan pada tahap berikutnya.
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
        <MapContainer center={PUSAT_PETA} zoom={9} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[-1.267, 116.831]}>
            <Popup>Balikpapan</Popup>
          </Marker>
          <Marker position={[-1.246, 116.744]}>
            <Popup>Penajam Paser Utara (IKN)</Popup>
          </Marker>
          <Marker position={[-0.478, 117.24]}>
            <Popup>Anggana, Kutai Kartanegara</Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
}

export default App;

import { useEffect, useState } from "react";
import { CircleMarker, Popup } from "react-leaflet";
import axios from "axios";

const URL_API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Warna sesuai tingkat risiko (sama dengan klasifikasi Early Warning KALTIDE)
const WARNA_RISIKO = {
  aman: "#22c55e", // hijau
  waspada: "#eab308", // kuning
  siaga: "#f97316", // oranye
  awas: "#ef4444", // merah
};

const URUTAN_RISIKO = ["aman", "waspada", "siaga", "awas"];

/**
 * Layer genangan: menampilkan satu lingkaran berwarna per stasiun/wilayah,
 * warnanya mengikuti tingkat risiko genangan TERTINGGI yang diprediksi
 * dalam 24 jam ke depan (aman=hijau, waspada=kuning, siaga=oranye, awas=merah).
 *
 * Data diambil langsung dari endpoint /flood/prediksi milik Flood Simulation
 * Engine -- jadi warna di peta ini benar-benar mencerminkan hasil model,
 * bukan data statis.
 */
function GenanganLayer() {
  const [titikGenangan, setTitikGenangan] = useState([]);
  const [sedangMemuat, setSedangMemuat] = useState(true);

  useEffect(() => {
    async function muatData() {
      try {
        const responsStasiun = await axios.get(`${URL_API}/stations/`);
        const daftarStasiun = responsStasiun.data;

        const hasil = await Promise.all(
          daftarStasiun.map(async (stasiun) => {
            try {
              const responsGenangan = await axios.get(
                `${URL_API}/flood/prediksi/${stasiun.id}`,
                { params: { kecamatan: stasiun.kecamatan, jumlah_hari: 1 } }
              );

              const daftarGenangan = responsGenangan.data;
              let risikoTertinggi = "aman";
              for (const genangan of daftarGenangan) {
                if (
                  URUTAN_RISIKO.indexOf(genangan.tingkat_risiko) >
                  URUTAN_RISIKO.indexOf(risikoTertinggi)
                ) {
                  risikoTertinggi = genangan.tingkat_risiko;
                }
              }

              return { ...stasiun, risiko: risikoTertinggi, jumlahPeriode: daftarGenangan.length };
            } catch {
              // Kalau satu stasiun gagal diambil, jangan sampai seluruh layer gagal
              return { ...stasiun, risiko: "aman", jumlahPeriode: 0, gagal: true };
            }
          })
        );

        setTitikGenangan(hasil);
      } catch (error) {
        console.error("Gagal memuat layer genangan:", error);
      } finally {
        setSedangMemuat(false);
      }
    }

    muatData();
  }, []);

  if (sedangMemuat || titikGenangan.length === 0) {
    return null;
  }

  return (
    <>
      {titikGenangan.map((titik) => (
        <CircleMarker
          key={titik.id}
          center={[titik.lat, titik.lon]}
          radius={14}
          pathOptions={{
            color: WARNA_RISIKO[titik.risiko],
            fillColor: WARNA_RISIKO[titik.risiko],
            fillOpacity: 0.6,
            weight: 2,
          }}
        >
          <Popup>
            <strong>{titik.nama}</strong>
            <br />
            Kecamatan: {titik.kecamatan}
            <br />
            Status: <strong>{titik.risiko.toUpperCase()}</strong>
            {titik.gagal && (
              <>
                <br />
                <em>(data tidak tersedia sementara)</em>
              </>
            )}
          </Popup>
        </CircleMarker>
      ))}
    </>
  );
}

export default GenanganLayer;

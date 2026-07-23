import { useEffect, useState } from "react";
import axios from "axios";

const URL_API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Kartu ringkasan status rob hari ini, memanggil endpoint
 * GET /analytics/ringkasan pada backend.
 */
function RingkasanStatus() {
  const [ringkasan, setRingkasan] = useState(null);
  const [sedangMemuat, setSedangMemuat] = useState(true);
  const [pesanGalat, setPesanGalat] = useState(null);

  useEffect(() => {
    axios
      .get(`${URL_API}/analytics/ringkasan`)
      .then((respons) => setRingkasan(respons.data))
      .catch(() => setPesanGalat("Gagal memuat ringkasan status dari backend."))
      .finally(() => setSedangMemuat(false));
  }, []);

  if (sedangMemuat) {
    return <div style={{ padding: "10px 20px" }}>Memuat ringkasan status...</div>;
  }

  if (pesanGalat) {
    return <div style={{ padding: "10px 20px", color: "#b91c1c" }}>{pesanGalat}</div>;
  }

  const kartu = [
    { label: "🟢 Aman", nilai: ringkasan.wilayah_status_aman },
    { label: "🟡 Waspada", nilai: ringkasan.wilayah_status_waspada },
    { label: "🟠 Siaga", nilai: ringkasan.wilayah_status_siaga },
    { label: "🔴 Awas", nilai: ringkasan.wilayah_status_awas },
  ];

  return (
    <div style={{ display: "flex", gap: "12px", padding: "12px 20px", background: "#f1f5f9" }}>
      {kartu.map((item) => (
        <div
          key={item.label}
          style={{
            background: "white",
            padding: "10px 16px",
            borderRadius: "8px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        >
          <div style={{ fontSize: "0.8rem", color: "#475569" }}>{item.label}</div>
          <div style={{ fontSize: "1.4rem", fontWeight: 600 }}>{item.nilai}</div>
        </div>
      ))}
    </div>
  );
}

export default RingkasanStatus;

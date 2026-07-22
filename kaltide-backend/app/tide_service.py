import math
from datetime import datetime, timedelta

def calculate_tide_harmonic(station_id="PUPR-TIDE-01", hours_ahead=24):
    """
    Model Prediksi Pasang Surut Harmonik untuk KALTIDE MVP.
    Menggunakan persamaan kosinus untuk menyimulasikan siklus semi-diurnal.
    """
    # Parameter Oseanografi (dikalibrasi estimasi untuk pesisir Kaltim)
    Z0 = 1.2       # Mean Sea Level (meter)
    A = 1.4        # Amplitudo maksimum (meter) -> Pasang tertinggi bisa ~2.6m
    T = 12.0       # Periode gelombang pasut (12 jam)
    phase_shift = 3.0  # Offset fasa agar pasang selaras dengan waktu riil
    
    now = datetime.now()
    tide_predictions = []
    
    # Menghitung elevasi air jam-per-jam ke depan
    for i in range(hours_ahead):
        target_time = now + timedelta(hours=i)
        
        # Konversi waktu ke dalam hitungan jam desimal
        t_hours = target_time.hour + (target_time.minute / 60.0)
        
        # Eksekusi Persamaan Harmonik Pasang Surut
        water_level = Z0 + A * math.cos((2 * math.pi / T) * t_hours - phase_shift)
        water_level = round(water_level, 2)
        
        # Klasifikasi Status (Rule-based simple)
        if water_level >= 2.2:
            status = "🔴 Pasang Sangat Tinggi (Bahaya Rob)"
        elif water_level >= 1.8:
            status = "🟡 Pasang Tinggi (Waspada)"
        elif water_level <= 0.6:
            status = "🟢 Surut (Aman)"
        else:
            status = "🟢 Normal"
            
        tide_predictions.append({
            "station_id": station_id,
            "timestamp": target_time.strftime("%Y-%m-%d %H:%M:%S"),
            "water_level_m": water_level,
            "status": status
        })
        
    return tide_predictions

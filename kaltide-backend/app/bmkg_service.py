import requests
import xml.etree.ElementTree as ET

def fetch_bmkg_forecast(city_name="Balikpapan"):
    """
    Menarik data prakiraan cuaca dari Open Data BMKG untuk wilayah Kalimantan Timur.
    City name yang tersedia di XML Kaltim biasanya: Balikpapan, Penajam, Tenggarong, Samarinda, dll.
    """
    url = "https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/DigitalForecast-KalimantanTimur.xml"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memastikan koneksi berhasil (Status 200)
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengambil data BMKG: {e}")
        return []

    # Parsing XML
    root = ET.fromstring(response.content)
    
    # Kamus Kode Cuaca BMKG
    weather_codes = {
        "0": "Cerah", "1": "Cerah Berawan", "2": "Cerah Berawan",
        "3": "Berawan", "4": "Tebal Berawan", "5": "Udara Kabur",
        "10": "Asap", "45": "Kabut", "60": "Hujan Ringan",
        "61": "Hujan Sedang", "63": "Hujan Lebat", "80": "Hujan Lokal",
        "95": "Hujan Petir", "97": "Hujan Petir"
    }

    forecast_data = []

    # Mencari area yang sesuai dengan input (misal: Balikpapan)
    for area in root.findall(".//area"):
        if area.get("description") == city_name:
            # Mengambil parameter cuaca (weather) dan kecepatan angin (wind speed / ws)
            weather_param = area.find(".//parameter[@id='weather']")
            wind_speed_param = area.find(".//parameter[@id='ws']")

            if weather_param is not None and wind_speed_param is not None:
                # Mengambil 4 data pertama (mewakili interval waktu terdekat)
                for i in range(4):
                    time_element = weather_param[i]
                    datetime_str = time_element.get("datetime")  # Format: YYYYMMDDHHMM
                    
                    # Ambil nilai cuaca
                    weather_val = time_element.find("value").text
                    weather_desc = weather_codes.get(weather_val, "Tidak Diketahui")
                    
                    # Ambil nilai kecepatan angin (knot)
                    ws_element = wind_speed_param[i]
                    ws_val = ws_element.find("value").text

                    forecast_data.append({
                        "datetime": datetime_str,
                        "weather_condition": weather_desc,
                        "wind_speed_knot": float(ws_val)
                    })
            break # Berhenti mencari jika kota sudah ditemukan
            
    return forecast_data

# --- Bagian ini hanya untuk testing lokal ---
if __name__ == "__main__":
    print("Mencoba menarik data cuaca Balikpapan dari BMKG...")
    hasil = fetch_bmkg_forecast("Balikpapan")
    for data in hasil:
        print(data)

import requests
import xml.etree.ElementTree as ET

def fetch_bmkg_forecast(city_name="Balikpapan"):
    """
    Menarik data prakiraan cuaca dari Open Data BMKG untuk wilayah Kalimantan Timur.
    Menggunakan penanganan error ekstra dan header User-Agent.
    """
    url = "https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/DigitalForecast-KalimantanTimur.xml"
    
    # Menambahkan identitas (User-Agent) agar server BMKG mengira ini adalah browser manusia
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Menambahkan timeout agar tidak menggantung jika server BMKG lambat
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        
        # Parsing XML yang aman (ditangkap jika formatnya rusak)
        root = ET.fromstring(response.content)
        
    except requests.exceptions.RequestException as e:
        print(f"Error Koneksi ke BMKG: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error Parsing XML (Data dari BMKG rusak/HTML): {e}")
        return []

    # Kamus Kode Cuaca BMKG
    weather_codes = {
        "0": "Cerah", "1": "Cerah Berawan", "2": "Cerah Berawan",
        "3": "Berawan", "4": "Tebal Berawan", "5": "Udara Kabur",
        "10": "Asap", "45": "Kabut", "60": "Hujan Ringan",
        "61": "Hujan Sedang", "63": "Hujan Lebat", "80": "Hujan Lokal",
        "95": "Hujan Petir", "97": "Hujan Petir"
    }

    forecast_data = []

    # Mencari area yang sesuai dengan input
    for area in root.findall(".//area"):
        if area.get("description") == city_name:
            weather_param = area.find(".//parameter[@id='weather']")
            wind_speed_param = area.find(".//parameter[@id='ws']")

            if weather_param is not None and wind_speed_param is not None:
                # Mengambil 4 data pertama
                for i in range(4):
                    time_element = weather_param[i]
                    datetime_str = time_element.get("datetime")
                    
                    weather_val = time_element.find("value").text
                    weather_desc = weather_codes.get(weather_val, "Tidak Diketahui")
                    
                    ws_element = wind_speed_param[i]
                    ws_val = ws_element.find("value").text

                    forecast_data.append({
                        "datetime": datetime_str,
                        "weather_condition": weather_desc,
                        "wind_speed_knot": float(ws_val)
                    })
            break 
            
    return forecast_data

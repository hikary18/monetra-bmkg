import requests
import time
from datetime import datetime

# Endpoint API Live BMKG AWS Maritim Bungus (ID: 3000000001)
BMKG_API_URL = "http://202.90.199.132/aws-new/data/station/latest/3000000001"

def get_latest_bmkg_data():
    """
    Fungsi untuk mengambil data sensor terkini dari server BMKG.
    Sudah dilengkapi fitur auto-conversion m/s ke knot jika data knot dari server bernilai 0.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Request data ke API BMKG dengan batas waktu tanggap 5 detik
        response = requests.get(BMKG_API_URL, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Mendukung struktur response berbentuk List maupun Object/Dict
            raw = data[0] if isinstance(data, list) else data.get('data', data)
            
            # Helper function untuk mengecek multiple key & konversi float secara aman
            def parse_sensor(keys, default_val=0.0):
                if isinstance(keys, str):
                    keys = [keys]
                for k in keys:
                    val = raw.get(k)
                    if val is not None and val != "":
                        try:
                            return round(float(val), 1)
                        except (ValueError, TypeError):
                            pass
                return default_val

            # Membaca Waktu/Timestamp
            raw_time = raw.get('datetime') or raw.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Pengecekan nama field alternatif dari server BMKG
            air_temp     = parse_sensor(['air_temp', 'temp', 't', 'temperature'])
            humidity     = parse_sensor(['humidity', 'rh', 'h'])
            air_pressure = parse_sensor(['pressure', 'p', 'barometer', 'mbar'])
            rain         = parse_sensor(['rain', 'rainfall', 'rr'])
            water_level  = parse_sensor(['water_level', 'wl', 'waterlevel'])
            
            # 📌 PERBAIKAN: Deteksi multi-key untuk kecepatan angin
            windspeed_ms = parse_sensor(['wind_speed', 'ws', 'windspeed', 'ff', 'windspeed_ms'])
            wind_speed   = parse_sensor(['wind_speed_knot', 'ws_knot', 'windspeed_knot', 'knot', 'ff_knot'])

            # 🔥 SISTEM BACKUP KONVERSI OTOMATIS (m/s ke knots)
            # Jika knots bernilai 0 tetapi m/s terbaca (misal 3.0 m/s seperti di gambar),
            # maka rumus konversinya adalah: 3.0 * 1.94384 = 5.8 knots
            if wind_speed == 0.0 and windspeed_ms > 0.0:
                wind_speed = round(windspeed_ms * 1.94384, 1)

            return {
                'timestamp': raw_time,
                'station_id': '3000000001',
                'station_name': 'AWS Maritim Bungus',
                'air_temp': air_temp,
                'humidity': humidity,
                'air_pressure': air_pressure,
                'wind_speed': wind_speed,     # Ini yang dikirim ke Dashboard & Model (knots)
                'rain': rain,
                'water_level': water_level,
                'status_server': 'CONNECTED'
            }
        else:
            print(f"[WARNING] HTTP Status Code Server BMKG: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("[ERROR] Timeout! Server BMKG tidak merespons dalam 5 detik.")
        return None
    except requests.exceptions.ConnectionError:
        print("[ERROR] Koneksi terputus! Periksa jaringan internet Anda.")
        return None
    except Exception as e:
        print(f"[ERROR] Kendala tak terduga: {e}")
        return None


# Perulangan otomatis jika file ini dijalankan secara langsung lewat Terminal
if __name__ == '__main__':
    print("=" * 65)
    print("🚀 MONITORING DATA REAL-TIME BMKG AWS BUNGUS (6 Parameter Utama)")
    print("=" * 65 + "\n")
    
    while True:
        data_terkini = get_latest_bmkg_data()
        
        if data_terkini:
            print(f"[{data_terkini['timestamp']}] ✅ Sinkronisasi Sukses:")
            print(f"  • Suhu Udara     : {data_terkini['air_temp']} °C")
            print(f"  • Kelembapan     : {data_terkini['humidity']} %")
            print(f"  • Tekanan Udara  : {data_terkini['air_pressure']} hPa")
            print(f"  • Kecepatan Angin : {data_terkini['wind_speed']} knot (Auto-Converted)")
            print(f"  • Curah Hujan    : {data_terkini['rain']} mm")
            print(f"  • Tinggi Air Laut : {data_terkini['water_level']} m")
            print("-" * 65)
        else:
            print("❌ Gagal mengambil data real-time dari server BMKG.\n")
            
        time.sleep(60)
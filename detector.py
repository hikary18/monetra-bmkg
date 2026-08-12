import numpy as np
import joblib
import os

def safe_float(val, default=0.0):
    """Mengubah None atau String menjadi Float secara aman agar terhindar dari crash TypeError"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class MLAnomalyDetector:
    def __init__(self, model_path='aws_isolation_forest.pkl'):
        # Toleransi sensor macet diubah menjadi 10 kali beruntun
        self.max_stuck_threshold = 10  
        
        self.stuck_counters = {
            'air_temp': 0, 'humidity': 0, 'air_pressure': 0,
            'wind_speed': 0, 'rain': 0, 'water_level': 0
        }
        self.last_values = {
            'air_temp': None, 'humidity': None, 'air_pressure': None,
            'wind_speed': None, 'rain': None, 'water_level': None
        }

        self.model = None
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"⚠️ Gagal memuat model ML ({model_path}): {e}")

    def analyze(self, live_data):
        alerts = []
        is_anomaly = False

        if not live_data:
            return ["Data kosong / API offline"], {}, "Anomali Sensor"

        # Proteksi Konversi Data Aman
        temp = safe_float(live_data.get('air_temp'), 0.0)
        hum = safe_float(live_data.get('humidity'), 0.0)
        press = safe_float(live_data.get('air_pressure'), 0.0)
        wind = safe_float(live_data.get('wind_speed'), 0.0)
        rain = safe_float(live_data.get('rain'), 0.0)
        water = safe_float(live_data.get('water_level'), 0.0)

        # -------------------------------------------------------------
        # LAPIS 1: LOGIKA PEMERIKSAAN BATAS MIN/MAX (ALARM JIKA KELUAR BATAS)
        # -------------------------------------------------------------
        if not (20.0 <= temp <= 40.0):
            alerts.append(f"Suhu udara di luar batas normal ({temp} °C). Batas: 20-40 °C")
            is_anomaly = True
            
        if not (30.0 <= hum <= 100.0):
            alerts.append(f"Kelembapan (RH) di luar batas normal ({hum} %). Batas: 30-100 %")
            is_anomaly = True
            
        if not (1006.0 <= press <= 1016.0):
            alerts.append(f"Tekanan udara di luar batas normal ({press} hPa). Batas: 1006-1016 hPa")
            is_anomaly = True
            
        if not (0.0 <= wind <= 20.0):
            alerts.append(f"Kecepatan angin di luar batas normal ({wind} knots). Batas: 0-20 knots")
            is_anomaly = True
            
        if not (0.0 <= rain <= 300.0):
            alerts.append(f"Curah hujan di luar batas normal ({rain} mm). Batas: 0-300 mm")
            is_anomaly = True
            
        if not (0.0 <= water <= 3.0):
            alerts.append(f"Tinggi air (Waterlevel) di luar batas normal ({water} m). Batas: 0-3 m")
            is_anomaly = True

        # -------------------------------------------------------------
       # -------------------------------------------------------------
        # -------------------------------------------------------------
        # LAPIS 2: DETEKSI SENSOR MACET / FLATLINE (Hanya untuk Suhu, Kelembapan, Tekanan, & Angin)
        # -------------------------------------------------------------
        current_data = {
            'air_temp': temp, 
            'humidity': hum, 
            'air_pressure': press,
            'wind_speed': wind
            # 💡 'rain' dan 'water_level' sengaja DIHAPUS agar nilai stabil/konstan tidak dianggap macet
        }

        param_names = {
            'air_temp': 'Suhu Udara', 
            'humidity': 'Kelembapan (RH)', 
            'air_pressure': 'Tekanan Udara', 
            'wind_speed': 'Kec. Angin'
        }

        for param, val in current_data.items():
            if self.last_values[param] is not None and val == self.last_values[param]:
                self.stuck_counters[param] += 1
            else:
                self.stuck_counters[param] = 1
                self.last_values[param] = val

            if self.stuck_counters[param] >= self.max_stuck_threshold:
                alerts.append(f"Sensor {param_names[param]} membeku/stuck ({val}) selama {self.stuck_counters[param]}x berturut-turut!")
                is_anomaly = True
                
        # -------------------------------------------------------------
        # LAPIS 3: MACHINE LEARNING MODEL (ISOLATION FOREST)
        # -------------------------------------------------------------
        if self.model and not is_anomaly:
            try:
                features = np.array([[temp, hum, press, wind, rain, water]])
                ml_pred = self.model.predict(features)[0]
                if ml_pred == -1:
                    alerts.append("Pola kombinasi parameter terisolasi dari tren normal (Machine Learning Outlier)")
                    is_anomaly = True
            except Exception:
                pass

        status = "Anomali Sensor" if is_anomaly else "Normal"
        stats = {
            'air_temp': temp, 'humidity': hum, 'air_pressure': press,
            'wind_speed': wind, 'rain': rain, 'water_level': water
        }

        return alerts, stats, status
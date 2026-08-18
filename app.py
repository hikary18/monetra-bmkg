from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, send_file
from bmkg_api import get_latest_bmkg_data
from detector import MLAnomalyDetector
from sheets_logger import save_to_google_sheets
import pandas as pd
import io
import threading
import os

app = Flask(__name__)
app.secret_key = 'monetra_secret_key_sangat_aman'  # Kunci enkripsi untuk session login

# Konfigurasi Akun Admin Sementara
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "bmkg2026"

detector = MLAnomalyDetector()
history_logs = []

# 🚀 ROUTE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = 'Username atau Password salah! Silakan coba lagi.'
            
    return render_template('login.html', error=error)

# 🚀 ROUTE LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 🔒 ROUTE UTAMA (Diproteksi Session Login)
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    # Proteksi API juga agar tidak bisa diakses secara ilegal jika belum login
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        live_data = get_latest_bmkg_data()
        status_anomali = "Normal"
        alerts = []
        stats = {}
        
        if live_data:
            raw_ts = str(live_data.get('timestamp', '--:--:-- WIB')).strip()
            current_minute = raw_ts[:16] if len(raw_ts) >= 16 else raw_ts
            last_minute = history_logs[0]['timestamp'][:16] if history_logs and len(history_logs[0]['timestamp']) >= 16 else None

            # Logika Menit Unik
            if current_minute != last_minute:
                alerts, stats, status_anomali = detector.analyze(live_data)
                
                # Pelindung awal agar tidak false alarm saat data awal di tabel < 10 baris
                if len(history_logs) < 9 and status_anomali == "Anomali Sensor":
                    if any("membeku" in a or "stuck" in a.lower() for a in alerts):
                        status_anomali = "Normal"
                        alerts = [a for a in alerts if "membeku" not in a and "stuck" not in a.lower()]
                
                log_entry = {
                    'timestamp': raw_ts,
                    'air_temp': live_data.get('air_temp', 0.0),
                    'humidity': live_data.get('humidity', 0.0),
                    'air_pressure': live_data.get('air_pressure', 0.0),
                    'wind_speed': live_data.get('wind_speed', 0.0),
                    'rain': live_data.get('rain', 0.0),
                    'water_level': live_data.get('water_level', 0.0),
                    'status': status_anomali
                }
                
                history_logs.insert(0, log_entry)
                if len(history_logs) > 50:
                    history_logs.pop()
                
                # Background thread Google Sheets (Bebas Lag)
                threading.Thread(
                    target=save_to_google_sheets, 
                    args=(live_data, status_anomali),
                    daemon=True
                ).start()
            else:
                if history_logs:
                    status_anomali = history_logs[0]['status']
                    _, stats, _ = detector.analyze(live_data)
                    alerts_sim, _, _ = detector.analyze(live_data)
                    alerts = alerts_sim if status_anomali == "Anomali Sensor" else []

        has_alarm = status_anomali == "Anomali Sensor"
        response = make_response(jsonify({
            'latest': live_data,
            'historical_stats': stats,
            'has_alarm': has_alarm,
            'alerts': alerts,
            'status_anomali': status_anomali,
            'log_length': len(history_logs),
            'history_logs': history_logs
        }))

        # Header Anti-Cache
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except Exception as e:
        print(f"❌ Eror pada /api/data: {e}")
        return jsonify({
            'latest': {}, 'historical_stats': {}, 'has_alarm': False,
            'alerts': [f"Koneksi gagal: {str(e)}"], 'status_anomali': "Error Server",
            'log_length': len(history_logs), 'history_logs': history_logs
        }), 200

@app.route('/download/csv')
def download_csv():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if not history_logs:
        return "Belum ada data riwayat untuk diekspor.", 400
        
    df = pd.DataFrame(history_logs)
    df_anomaly = df[df['status'] == 'Anomali Sensor'].copy()
    
    if df_anomaly.empty:
        return "<h3>Tidak ditemukan riwayat data anomali untuk diekspor saat ini.</h3><p>Kembali ke <a href='/'>Dashboard</a></p>", 200
        
    df_anomaly.columns = [
        'Waktu (WIB)', 'Suhu Udara (°C)', 'Kelembapan (%)', 
        'Tekanan Udara (hPa)', 'Kec. Angin (knots)', 'Curah Hujan (mm)', 
        'Tinggi Air (m)', 'Status Evaluasi AI'
    ]
    
    buffer = io.BytesIO()
    df_anomaly.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    
    return send_file(
        buffer, mimetype='text/csv',
        download_name='Laporan_Log_Anomali_MONETRA.csv', as_attachment=True
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

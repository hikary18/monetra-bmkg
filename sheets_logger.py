import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CREDS_FILE = BASE_DIR / "credentials.json"

# 📌 PERBAIKAN: Ubah namanya agar sama persis dengan judul Google Sheets kamu
SPREADSHEET_NAME = "Data_AWS_Normal_Anomali_BMKG_Bungus" 

def save_to_google_sheets(data, status_anomali):
    """
    Fungsi untuk menambahkan 1 baris data real-time BMKG ke Google Sheets.
    """
    if not CREDS_FILE.exists():
        print("⚠️ [GOOGLE SHEETS] File 'credentials.json' tidak ditemukan.")
        return False

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(str(CREDS_FILE), scope)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME).sheet1

        row = [
            data.get('timestamp', ''),
            data.get('air_temp', 0.0),
            data.get('humidity', 0.0),
            data.get('air_pressure', 0.0),
            data.get('wind_speed', 0.0),
            data.get('rain', 0.0),
            data.get('water_level', 0.0),
            status_anomali
        ]

        sheet.append_row(row)
        print(f"📊 [GOOGLE SHEETS] Sukses menyimpan data ({data.get('timestamp')}) ke Cloud!")
        return True
        
    except Exception as e:
        print(f"❌ [GOOGLE SHEETS ERROR] Gagal menyimpan data: {e}")
        return False
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from pathlib import Path

def main():
    # 📌 1. Path Absolut Tempat File Excel Berada (Folder Downloads)
    excel_path = Path(r"C:\Users\Zaky\Downloads\Data_AWS_2025.xlsx")
    
    # 📌 2. Path Output Model ML (Disimpan di Folder Proyek MONETRA)
    BASE_DIR = Path(__file__).parent.resolve()
    model_output_path = BASE_DIR / 'aws_isolation_forest.pkl'

    print("=" * 65)
    print(f"📂 Mengakses File Excel : {excel_path}")
    print(f"💾 Lokasi Simpan Model  : {model_output_path}")
    print("=" * 65)

    # 📌 3. Pengecekan Keberadaan File Excel
    if not excel_path.exists():
        print(f"❌ ERROR: File tidak ditemukan di path:")
        print(f"   {excel_path}")
        print("👉 Pastikan nama file dan foldernya sudah benar!")
        return

    try:
        # 📌 4. Membaca dataset historis
        df = pd.read_excel(excel_path)
        features = ['temp', 'rh', 'pressure', 'windspeed', 'solrad', 'watertemp', 'waterlevel']

        # Validasi nama kolom pada Excel
        missing_cols = [col for col in features if col not in df.columns]
        if missing_cols:
            print(f"❌ ERROR: Kolom berikut tidak ditemukan pada Excel: {missing_cols}")
            print(f"   Kolom yang ada di Excel: {list(df.columns)}")
            return

        # 📌 5. Batasan MIN & MAX PASTI BMKG (Kecepatan Angin = Knots)
        stats = {
            'temp':       {'min': 20.0, 'max': 40.0},
            'rh':         {'min': 30.0, 'max': 100.0},
            'waterlevel': {'min': 0.0,  'max': 3.0},
            'pressure':   {'min': 1006.0,'max': 1016.0},
            'windspeed':  {'min': 0.0,  'max': 40.0},  # Max 40 Knots
            'rain':       {'min': 0.0,  'max': 300.0},
            'solrad':     {'min': 0.0,  'max': 1200.0},
            'watertemp':  {'min': 20.0, 'max': 40.0}
        }

        # 📌 6. Training Model Isolation Forest
        print("⏳ Sedang memproses dan melatih model Isolation Forest...")
        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(df[features])

        # 📌 7. Membungkus Model dan Batasan BMKG ke Payload
        payload = {
            'model': model,
            'features': features,
            'stats': stats
        }

        # 📌 8. Simpan dan Menimpa (Overwrite) File .pkl
        joblib.dump(payload, model_output_path)

        print("=" * 65)
        print("✅ SUKSES! Model ML & Batasan BMKG berhasil dibuat:")
        print(f"   └─► {model_output_path.name}")
        print("=" * 65)

    except Exception as e:
        print(f"❌ Terjadi kesalahan saat membaca file Excel: {e}")

if __name__ == '__main__':
    main()
import pandas as pd
import sqlite3

# CSV dosyasını yükle
csv_file = "merged_game_data.csv"
data = pd.read_csv(csv_file)

# Steam ve Epic fiyatı null olanları filtrele
filtered_data = data[~(data["steam_fiyati"].isnull() & data["epic_fiyati"].isnull())]

# SQLite veritabanı bağlantısını oluştur
db_name = "game_data.db"
conn = sqlite3.connect(db_name)

# Filtrelenmiş veriyi SQLite tablosuna yaz
table_name = "games"
filtered_data.to_sql(table_name, conn, if_exists="replace", index=False)

print(f"[INFO] Veriler {db_name} veritabanında '{table_name}' tablosuna kaydedildi. Toplam {len(filtered_data)} kayıt eklendi.")

# Veritabanını kapat
conn.close()

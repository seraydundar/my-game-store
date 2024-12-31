import pandas as pd
from rapidfuzz import fuzz

# Dosya isimleri
steam_file = "steamverisi.csv"
metacritic_file = "metacritic_games.csv"
epic_file = "epic_games_results.csv"
output_file = "merged_game_data.csv"

# CSV'leri yükleme
steam_data = pd.read_csv(steam_file)
metacritic_data = pd.read_csv(metacritic_file)
epic_data = pd.read_csv(epic_file)

# Sütun isimlerini normalize etme
steam_data.columns = ["oyun_adi", "steam_fiyati", "steam_url"]
metacritic_data.columns = ["oyun_adi", "metascore", "metacritic_url"]
epic_data.columns = ["oyun_adi", "epic_fiyati", "epic_url"]

# Oyun adlarını normalize eden fonksiyon
def normalize_name(name):
    return name.strip().lower()

steam_data["oyun_adi_norm"] = steam_data["oyun_adi"].apply(normalize_name)
metacritic_data["oyun_adi_norm"] = metacritic_data["oyun_adi"].apply(normalize_name)
epic_data["oyun_adi_norm"] = epic_data["oyun_adi"].apply(normalize_name)

# RapidFuzz eşleşmesi için fonksiyon
def find_best_match(target_name, candidates, threshold=90):
    best_match = None
    best_score = 0
    for candidate in candidates:
        score = fuzz.token_set_ratio(target_name, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_match if best_score >= threshold else None

merged_data = []

for _, steam_row in steam_data.iterrows():
    steam_name = steam_row["oyun_adi_norm"]

    # Metacritic eşleşmesi
    metacritic_row = metacritic_data[metacritic_data["oyun_adi_norm"] == steam_name]
    if not metacritic_row.empty:
        metacritic_row = metacritic_row.iloc[0]
    else:
        # RapidFuzz devreye giriyor
        metacritic_match_name = find_best_match(steam_name, metacritic_data["oyun_adi_norm"], threshold=90)
        if metacritic_match_name:
            metacritic_row = metacritic_data[metacritic_data["oyun_adi_norm"] == metacritic_match_name].iloc[0]
        else:
            metacritic_row = {"metascore": None, "metacritic_url": None}

    # Epic Games eşleşmesi
    epic_row = epic_data[epic_data["oyun_adi_norm"] == steam_name]
    if not epic_row.empty:
        epic_row = epic_row.iloc[0]
    else:
        # RapidFuzz devreye giriyor
        epic_match_name = find_best_match(steam_name, epic_data["oyun_adi_norm"], threshold=90)
        if epic_match_name:
            epic_row = epic_data[epic_data["oyun_adi_norm"] == epic_match_name].iloc[0]
        else:
            epic_row = {"epic_fiyati": None, "epic_url": None}

    # Fiyat ve URL ayarlamaları
    steam_fiyat = steam_row["steam_fiyati"]
    epic_fiyat = epic_row.get("epic_fiyati")

    steam_url = steam_row["steam_url"] if steam_fiyat not in ["Free", "Ücretsiz", None] else None
    epic_url = epic_row.get("epic_url") if epic_fiyat not in ["Free", "Ücretsiz", None] else None

    # Birleştirilmiş veri
    merged_data.append({
        "oyun_adi": steam_row["oyun_adi"],
        "steam_fiyati": None if steam_fiyat in ["Free", "Ücretsiz", None] else steam_fiyat,
        "epic_fiyati": None if epic_fiyat in ["Free", "Ücretsiz", None] else epic_fiyat,
        "metascore": metacritic_row.get("metascore"),
        "steam_url": steam_url,
        "epic_url": epic_url,
    })

# Sonuçları CSV'ye kaydet
merged_df = pd.DataFrame(merged_data)
merged_df.to_csv(output_file, index=False, na_rep="null")

print(f"[INFO] Birleştirilmiş veriler {output_file} dosyasına kaydedildi.")

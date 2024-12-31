import aiohttp
import asyncio
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Hedef URL Şablonu
base_url = "https://store.steampowered.com/search/"
params = {
    "filter": "topsellers",
    "os": "win",
    "cc": "tr",  # Türk Lirası cinsinden fiyatlar için
    "count": 100,  # Sayfa başına çekilecek oyun sayısı artırıldı
}

# CSV Dosyasını Hazırlama
csv_file = "steamverisi.csv"
csv_headers = ["Oyun", "Fiyat", "URL"]  # URL sütunu eklendi

# Toplam Oyun Sayısı ve Hedef
total_games = 8000
collected_games = 0
start = 0
collected_titles = set()  # Yinelenen oyunları önlemek için başlıkları takip eden set
buffer = []  # Verileri geçici olarak burada tutacağız

# CSV Dosyasını Başlatma
with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(csv_headers)

# DLC Kontrol Fonksiyonu
async def check_dlc(session, url):
    """Bir oyun sayfasının DLC olup olmadığını kontrol eder."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return False
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            purchase_area = soup.find('div', class_='game_area_purchase')
            if purchase_area and purchase_area.find('div', class_='game_area_bubble game_area_dlc_bubble'):
                return True  # DLC ise True döner
            return False
    except Exception as e:
        print(f"[ERROR] DLC kontrolü sırasında hata oluştu: {e}")
        return False

# Oyunları Çekme ve İşleme Fonksiyonu
async def fetch_games():
    global collected_games, start, buffer
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as session:
        with tqdm(total=total_games, desc="Toplanan Oyun Sayısı") as pbar:
            while collected_games < total_games:
                # URL'yi Oluşturma
                params["start"] = start
                async with session.get(base_url, params=params) as response:
                    if response.status != 200:
                        print(f"Sayfa alınamadı, durum kodu: {response.status_code}")
                        break

                    # Sayfa İçeriğini Parse Etme
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    # Oyun Kartlarını Bulma
                    search_results = soup.find_all('a', class_='search_result_row')

                    # Eğer sonuç yoksa, döngüyü kır
                    if not search_results:
                        print("Daha fazla oyun bulunamadı.")
                        break

                    # DLC Kontrolleri İçin Görevler
                    buffer.clear()  # Yeni buffer temizlenir
                    tasks = []
                    for game in search_results:
                        if collected_games >= total_games:
                            break

                        # Başlık
                        title_tag = game.find('span', class_='title')
                        title = title_tag.text.strip() if title_tag else "Başlık Bulunamadı"

                        # Yinelenen Oyunu Kontrol Etme
                        if title in collected_titles:
                            continue

                        # Güncel Fiyat
                        price_tag = game.find('div', class_='discount_final_price')
                        price = price_tag.text.strip() if price_tag else "Fiyat Bilgisi Yok"

                        # Ücretsiz Oyunları Hariç Tutma
                        if price.lower() == "ücretsiz":
                            continue

                        # Fiyatın Geçerli Olduğunu Kontrol Etme
                        if price == "Fiyat Bilgisi Yok":
                            continue

                        # URL
                        url = game['href'] if game.has_attr('href') else "URL Bulunamadı"

                        # DLC Kontrolü için görev oluştur
                        tasks.append(asyncio.create_task(check_dlc(session, url)))

                        # Geçici olarak başlık, fiyat ve URL ekle
                        buffer.append([title, price, url])
                        collected_titles.add(title)  # Yinelenenleri engelle
                        collected_games += 1
                        pbar.update(1)

                    # DLC Kontrollerini Yap ve Buffer'ı Filtrele
                    dlc_results = await asyncio.gather(*tasks)
                    filtered_buffer = [
                        buffer[idx] for idx, is_dlc in enumerate(dlc_results) if not is_dlc
                    ]

                    # CSV'ye Yaz
                    with open(csv_file, mode='a', encoding='utf-8', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerows(filtered_buffer)

                # Sonraki Sayfaya Geçmek İçin 'start' Parametresini Güncelleme
                start += params["count"]

# Ana Fonksiyon
async def main():
    await fetch_games()
    # Kalan Veriyi CSV'ye Yaz
    if buffer:
        with open(csv_file, mode='a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(buffer)

# Asyncio Çalıştır
asyncio.run(main())

print(f"\nToplam {collected_games} oyun verisi 'steamverisi.csv' dosyasına kaydedildi.")

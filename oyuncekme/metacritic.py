import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import re

def setup_driver(chromedriver_path):
    """
    Selenium WebDriver'ı kurar ve başlatır (tarayıcı görünür şekilde çalışır).
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Otomasyon tespiti önleme
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36"
    )
    # Headless modu kaldırıldı, böylece tarayıcı görünür çalışacak
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)  # Sayfanın yüklenme süresi sınırı
    return driver

def sanitize_filename(name):
    """
    Dosya adında kullanılmaması gereken karakterleri temizler.
    """
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_image(image_url, game_name, folder_path, session):
    """
    Verilen URL'den resmi indirir ve belirtilen klasöre kaydeder.
    """
    if not image_url:
        print(f"Görsel URL'si boş olduğu için indirilmeyecek: {game_name}")
        return
    try:
        # Eğer image_url relatif bir URL ise, mutlak URL'ye dönüştür
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://www.metacritic.com' + image_url
        elif not image_url.startswith('http'):
            print(f"Geçersiz URL formatı ({game_name}): {image_url}")
            return

        # Başlıkları ekleyin
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36',
            'Referer': 'https://www.metacritic.com/'
        }

        # İsteği yapın
        response = session.get(image_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()

        # Dosya uzantısını al
        ext = os.path.splitext(image_url)[1].split('?')[0]
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            ext = '.jpg'

        safe_game_name = sanitize_filename(game_name)
        file_path = os.path.join(folder_path, f"{safe_game_name}{ext}")

        # Benzersiz dosya adı için oyun adının sonuna rastgele sayı ekleyebiliriz
        counter = 1
        original_file_path = file_path
        while os.path.exists(file_path):
            file_path = os.path.join(folder_path, f"{safe_game_name}_{counter}{ext}")
            counter += 1
            if counter > 100:
                print(f"Çok fazla dosya çakışması ({game_name}), görsel indirilmiyor.")
                return

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Görsel indirildi: {file_path}")
    except Exception as e:
        print(f"Görsel indirilemedi ({game_name}): {e}")

def scrape_metacritic_page(page_url, driver):
    """
    Bir sayfadaki oyunların adlarını, Metascore değerlerini ve görsel URL'lerini çeker.
    """
    driver.get(page_url)
    time.sleep(5)  # Sayfa yüklenmesi için 5 saniye bekleme
    games = []

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.c-finderProductCard'))
        )
        game_cards = driver.find_elements(By.CSS_SELECTOR, 'div.c-finderProductCard')

        for card in game_cards:
            try:
                # Oyun adı
                game_name_element = card.find_element(By.CSS_SELECTOR, 'div[data-title]')
                game_name = game_name_element.get_attribute("data-title").strip()

                # Metascore
                metascore_element = card.find_element(By.CSS_SELECTOR, 'div.c-siteReviewScore span')
                metascore = metascore_element.text.strip()

                # Görsel URL'si
                image_element = card.find_element(By.CSS_SELECTOR, 'img')
                image_url = image_element.get_attribute("src")
                if not image_url:
                    image_url = image_element.get_attribute("data-src")
                if not image_url:
                    print(f"Görsel URL'si bulunamadı ({game_name})")

                games.append({'Game Name': game_name, 'Metascore': metascore, 'Image URL': image_url})
            except Exception as e:
                print(f"Bir hata oluştu ({game_name}): {e}")
                continue

    except Exception as e:
        print(f"Sayfa {page_url} için oyun bilgileri bulunamadı: {e}")

    return games

def save_to_csv(games, file_name):
    """
    Verilen oyun listesini bir CSV dosyasına ekler.
    """
    df = pd.DataFrame(games)
    if not os.path.exists(file_name):
        df.to_csv(file_name, index=False, encoding='utf-8-sig')  # Dosya yoksa oluştur ve yaz
    else:
        df.to_csv(file_name, index=False, encoding='utf-8-sig', mode='a', header=False)  # Dosya varsa ekle
    print(f"{len(games)} oyun '{file_name}' dosyasına kaydedildi.")

def main():
    base_url = "https://www.metacritic.com/browse/game/?releaseYearMin=2003&releaseYearMax=2024&page={page_number}"
    total_pages = 100  # Toplam sayfa sayısı
    all_games = []
    file_name = 'metacritic_games.csv'
    images_folder = 'gorseller'

    # Görselleri kaydedeceğimiz klasörü oluştur
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)
        print(f"'{images_folder}' klasörü oluşturuldu.")

    # ChromeDriver'ın tam yolu
    chromedriver_path = r'C:\Users\Oğuzhan\steamoyuncekme\chromedriver.exe'  # ChromeDriver yolunuz

    # ChromeDriver dosyasının mevcut olup olmadığını kontrol edin
    if not os.path.exists(chromedriver_path):
        print(f"Hata: '{chromedriver_path}' dosyası bulunamadı. Lütfen yolu kontrol edin.")
        return

    driver = setup_driver(chromedriver_path)

    # Requests session oluşturun
    session = requests.Session()

    try:
        for page_number in range(1, total_pages + 1):  # page=1'den başla
            page_url = base_url.format(page_number=page_number)
            print(f"Fetching games from page: {page_number}")
            games = scrape_metacritic_page(page_url, driver)

            if games:
                all_games.extend(games)
                save_to_csv(games, file_name)  # Her sayfa sonunda CSV'ye ekleme

                # Görselleri indir
                for game in games:
                    game_name = game['Game Name']
                    image_url = game['Image URL']
                    if image_url:
                        download_image(image_url, game_name, images_folder, session)
                    else:
                        print(f"Görsel URL'si mevcut değil, indirilmeyecek: {game_name}")

            else:
                print(f"Sayfa {page_number} boş veya yüklenemedi.")

            # Sunucuyu yormamak için bekleme
            time.sleep(3)
    finally:
        driver.quit()

    print(f"Toplam {len(all_games)} oyun '{file_name}' dosyasına kaydedildi.")
    print(f"Görseller '{images_folder}' klasörüne indirildi.")

if __name__ == "__main__":
    main()

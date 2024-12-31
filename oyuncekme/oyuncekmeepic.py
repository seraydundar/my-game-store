import os
import csv
import time
import random
import re  # Regex kullanımı için ekledik
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

# Base URL ve diğer ayarlar
BASE_URL_TEMPLATE = "https://store.epicgames.com/tr/browse?sortBy=releaseDate&sortDir=DESC&category=Game&count=40&start={start}"
CSV_FILE = "epic_games_results.csv"
EXCLUDE_KEYWORDS = ["+18", "pack"]
START_INCREMENT = 40  # Her sayfada ilerleme miktarı

def setup_driver():
    """
    Selenium tarayıcı ayarlarını yapılandırır ve mevcut Chrome profilini kullanır.
    """
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0 Safari/537.36")
    driver = uc.Chrome(options=options)

    stealth(driver,
            languages=["tr-TR", "tr"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver

def clear_csv_file(file_path):
    """
    CSV dosyasını temizler veya yeniden oluşturur.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
    print(f"[INFO] '{file_path}' dosyası silindi ve yeniden oluşturulacak.")

def clean_title(title):
    """
    Eğer 'edition' kelimesi başlıkta geçiyorsa, 'edition' ve ondan önceki kelimeyi kaldırır.
    """
    try:
        # 'word edition' şeklindeki ifadeleri (case insensitive) bulur ve kaldırır
        # Burada 'word' alfasayısal, apostrof ve tire içerebilir
        pattern = re.compile(r'\b[\w\'\-]+\s+edition\b', re.IGNORECASE)
        cleaned_title = pattern.sub('', title).strip()
        
        # Eğer "edition" ifadesi birden fazla kez geçiyorsa, tekrar temizleme yapar
        while re.search(pattern, cleaned_title):
            cleaned_title = pattern.sub('', cleaned_title).strip()
        
        return cleaned_title
    except Exception as e:
        print(f"[ERROR] Başlık temizleme hatası: {e}")
        return title

def fetch_epic_games_data(driver):
    """
    Selenium kullanarak Epic Games Store'dan veri çeker.
    """
    games = []
    try:
        # Timeout süresini random bir aralıkta ayarlayın (örneğin 10-20 saniye)
        min_timeout = 10
        max_timeout = 20
        timeout_duration = random.randint(min_timeout, max_timeout)
        WebDriverWait(driver, timeout_duration).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.css-g3jcms"))
        )
        game_elements = driver.find_elements(By.CSS_SELECTOR, "a.css-g3jcms")
        for element in game_elements:
            try:
                # İlk olarak daha spesifik bir elementten oyun adını almaya çalış
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, "span.css-1ljj0lu")  # Doğru sınıfı kontrol edin
                    title = title_element.text.strip()
                except NoSuchElementException:
                    print("[WARNING] Oyun adı elementi bulunamadı, aria-label'dan deniyor.")
                    # Eğer spesifik element bulunamazsa, aria-label'dan oyun adını al
                    aria_label = element.get_attribute("aria-label").strip()
                    title = extract_title_from_aria_label(aria_label)

                # Oyun adını temizle
                title = clean_title(title)

                if not title or any(kw in title.lower() for kw in EXCLUDE_KEYWORDS):
                    continue

                try:
                    price_element = element.find_element(By.CSS_SELECTOR, "span.css-12s1vua")
                    price = price_element.text.strip() if price_element else "Ücretsiz"
                except NoSuchElementException:
                    price = "Ücretsiz"

                # Oyun URL'sini al
                game_url = element.get_attribute("href").strip()

                print(f"[DATA] {title} - Fiyat: {price} - URL: {game_url}")
                games.append({"Oyun Adı": title, "Fiyat": price, "URL": game_url})
            except Exception as e:
                print(f"[ERROR] Veri işleme hatası: {e}")
    except TimeoutException:
        print("[ERROR] Sayfa yükleme zaman aşımına uğradı.")
        driver.save_screenshot("page_load_timeout.png")
    return games

def extract_title_from_aria_label(aria_label):
    """
    aria-label içinden oyun adını çıkarır.
    Örneğin: "40 içerisinden 1, Ana Oyun, Vampire Survivors, Şimdi Epic'te, -%100, ₺67,00, Ücretsiz"
    oyun adını "Vampire Survivors" olarak çıkarır.
    """
    try:
        parts = [part.strip() for part in aria_label.split(",")]
        # Oyun adının bulunduğu kısmı belirlemek için mantık ekleyin
        # Örneğin, "Ana Oyun" ve "Şimdi Epic'te" arasında yer alıyorsa:
        ana_oyun_index = parts.index("Ana Oyun") if "Ana Oyun" in parts else -1
        if ana_oyun_index != -1 and len(parts) > ana_oyun_index + 1:
            return parts[ana_oyun_index + 1]
        else:
            # Alternatif olarak, belirli bir pozisyonu alabilirsiniz
            return parts[2] if len(parts) > 2 else aria_label
    except Exception as e:
        print(f"[ERROR] aria-label işleme hatası: {e}")
        return aria_label  # Fallback olarak tam aria-label'ı döndür

def is_captcha_present(driver):
    """
    Sayfada CAPTCHA'nın varlığını kontrol eder.
    """
    return "recaptcha" in driver.page_source.lower()

def solve_recaptcha_manually():
    """
    Kullanıcıdan CAPTCHA'yı manuel olarak çözmesini ister.
    """
    input("CAPTCHA'yı çözdükten sonra Enter tuşuna basın...")

def generate_page_urls(total_pages=100):
    """
    Belirtilen sayıda sayfanın URL'lerini oluşturur.
    """
    urls = []
    for page in range(total_pages):
        start = page * START_INCREMENT
        url = BASE_URL_TEMPLATE.format(start=start)
        urls.append(url)
    return urls

def save_to_csv(games, file_path, write_header=False):
    """
    Veriyi CSV dosyasına kaydeder.
    """
    write_mode = "w" if write_header else "a"
    with open(file_path, mode=write_mode, newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Oyun Adı", "Fiyat", "URL"])
        if write_header:
            writer.writeheader()
        writer.writerows(games)
    print(f"[INFO] {len(games)} kayıt kaydedildi -> {file_path}")

def human_like_actions(driver):
    """İnsan benzeri davranışlar ekler."""
    try:
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(100, 500), random.randint(100, 500)).perform()
        time.sleep(random.uniform(1, 3))
        if random.random() < 0.3:
            driver.execute_script("document.body.click();")
            time.sleep(random.uniform(0.5, 1.5))
        driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
        time.sleep(random.uniform(1, 3))
    except Exception as e:
        print(f"[ERROR] Human-like actions sırasında hata: {e}")

def main():
    driver = setup_driver()
    all_games = []

    clear_csv_file(CSV_FILE)
    save_to_csv([], CSV_FILE, write_header=True)

    print("[INFO] Veri çekme işlemi başlatılıyor...")

    page_urls = generate_page_urls(total_pages=100)

    try:
        for idx, url in enumerate(page_urls):
            print(f"[INFO] {idx + 1}. sayfa yükleniyor: {url}")
            driver.get(url)

            # Daha uzun rastgele bekleme süresi
            time.sleep(random.uniform(8, 15))

            if is_captcha_present(driver):
                print("[INFO] CAPTCHA algılandı. Lütfen CAPTCHA'yı manuel olarak çözün.")
                solve_recaptcha_manually()

            games = fetch_epic_games_data(driver)
            if not games:
                print("[INFO] Veri bulunamadı veya işlem tamamlandı.")
                break

            save_to_csv(games, CSV_FILE)
            all_games.extend(games)
            print(f"[INFO] Toplam {len(all_games)} oyun kaydedildi.\n")

            human_like_actions(driver)

    except Exception as e:
        print(f"[ERROR] Genel hata: {e}")
    finally:
        driver.quit()
        print(f"[INFO] Tüm oyunlar kaydedildi -> {CSV_FILE}")

if __name__ == "__main__":
    main()

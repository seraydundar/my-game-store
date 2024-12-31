import subprocess
import sys

def run_script(script_name):
    try:
        # subprocess.run kullanarak betiği çalıştırır
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} başarıyla tamamlandı.")
    except subprocess.CalledProcessError as e:
        print(f"{script_name} çalıştırılırken bir hata oluştu: {e}")
    except FileNotFoundError:
        print(f"{script_name} bulunamadı.")

def main():
    scripts = [
        "oyuncekmeepic.py",
        "oyuncekme.py",
        "metacritic.py",
        "soncsv.py"
        "databasecreater.py"
    ]
    
    for script in scripts:
        run_script(script)

if __name__ == "__main__":
    main()

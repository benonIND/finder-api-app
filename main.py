import banner, web_scraper, api_scanner
import time
import os

def main_menu():
    os.system("clear")
    banner.show_banner()
    print("Pilih Fitur:")
    print("1. Cari Website dari Aplikasi Android")
    print("2. Cari REST API dari Website")
    print("3. Keluar")
    
    choice = input("\nMasukkan pilihan (1/2/3): ")
    
    if choice == '1':
        app_input = input("Masukkan nama aplikasi atau link Play Store: ")
        print("\n" + "="*50)
        print("Mencari... Silakan tunggu")
        
        try:
            result = web_scraper.find_app_website(app_input)
            print(f"\nHasil: {result}")
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Mencoba metode alternatif...")
            time.sleep(2)
            if 'play.google.com' in app_input:
                result = web_scraper.fallback_scrape(app_input)
                print(f"\nHasil (alternatif): {result}")
        
        print("="*50 + "\n")
        
    elif choice == '2':
        domain_input = input("Masukkan URL website atau domain: ")
        print("\n" + "="*60)
        print("🚀 Memulai Advanced API Scanning")
        print(f"🔍 Target: {domain_input}")
        print("📋 Menggunakan pattern dari list.txt")
        print("⏳ Harap tunggu, proses mungkin memakan waktu 15-30 detik...")
    
        try:
            results = api_scanner.find_api_endpoints(domain_input)
        
            print("\n✅ Hasil Pemindaian API:")
            if len(results) == 1 and results[0].startswith(("Tidak ditemukan", "Error")):
                print(results[0])
            else:
                print(f"📊 Total ditemukan: {len(results)} endpoint")
                for i, api in enumerate(results, 1):
                    print(f"{i}. {api}")
        
            print("\n💡 Tips Analisis:")
            print("- Endpoint dengan domain utama lebih mungkin valid")
            print("- Cek endpoint dengan: curl -I <url>")
            print("- Gunakan Postman untuk test endpoint")
            print("- File list.txt bisa diedit untuk tambah pattern")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
        print("="*60 + "\n")
        
    elif choice == '3':
        print("Terima kasih telah menggunakan tool ini!")
        exit()
    else:
        print("Pilihan tidak valid!")
    
    input("Tekan Enter untuk melanjutkan...")
    main_menu()

if __name__ == "__main__":
    main_menu()

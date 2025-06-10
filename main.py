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
    
        try:
            start_time = time.time()
            print("🛠️ Memulai proses scanning...")
            results = api_scanner.find_api_endpoints(domain_input)
        
            print("\n" + "="*60)
            print("🎯 HASIL PEMINDAIAN API")
            print("="*60)
        
            if not results or (len(results) == 1 and results[0].startswith(("Tidak ditemukan", "Error"))):
                print(results[0] if results else "Tidak ditemukan API endpoint")
            else:
                print(f"✨ TOTAL DITEMUKAN: {len(results)} endpoint valid\n")
                for i, api in enumerate(results, 1):
                    print(f"{i}. {api}")
        
            print(f"\n⏱️ Waktu eksekusi: {time.time() - start_time:.2f} detik")
            print("="*60 + "\n")
        
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
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

import banner, web_scraper, api_scanner
from api_finder import banner, web_scraper, api_scanner
import time

def main_menu():
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
        # ... (kode sebelumnya tetap sama)
        domain_input = input("Masukkan URL website atau domain: ")
        results = api_scanner.find_api_endpoints(domain_input)
        print("\n" + "="*50)
        print("Ditemukan API Endpoint:")
        for api in results:
            print(f"- {api}")
        print("="*50 + "\n")
        
    elif choice == '3':
        print("Terima kasih telah menggunakan tool ini!")
        exit()
    else:
        print("Pilihan tidak valid!")
    
    input("Tekan Enter untuk melanjutkan...")
    main_menu()

if __name__ == "__main__":
    main_menu()

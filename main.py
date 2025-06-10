import banner, web_scraper, api_scanner
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
        domain_input = input("Masukkan URL website atau domain: ")
        print("\n" + "="*50)
        print("Memulai pemindaian API... Ini mungkin membutuhkan waktu beberapa detik")
    
        try:
            results = api_scanner.find_api_endpoints(domain_input)
            print("\nHasil Pemindaian API:")
            if len(results) == 1 and results[0].startswith(("Tidak ditemukan", "Error")):
                print(results[0])
            else:
                for i, api in enumerate(results, 1):
                     print(f"{i}. {api}")
        
                     print("\nTips:")
                     print("- Endpoint dengan domain utama biasanya lebih relevan")
                     print("- Coba endpoint dengan tools seperti Postman atau curl")
                     print("- Periksa dokumentasi API jika tersedia")
        except Exception as e:
            print(f"Error: {str(e)}")
    
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

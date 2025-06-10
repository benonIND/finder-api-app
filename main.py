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
        domain_input = input("Masukkan URL/domain utama: ")
        print("\n" + "="*60)
    
        try:
            start_time = time.time()
            domain_input = 'https://'+domain_input
            results = api_scanner.unified_scan(domain_input)
        
            print("\n" + "="*60)
            print("🎯 HASIL UNIFIED SCAN")
            print("="*60)
        
            if not results:
                print("Tidak ditemukan API endpoint")
            else:
                total_apis = sum(len(apis) for apis in results.values())
                print(f"✨ TOTAL DITEMUKAN: {total_apis} API endpoint pada {len(results)} domain\n")
            
                for domain, apis in results.items():
                    print(f"\n🔗 Domain: {domain}")
                    for i, api in enumerate(apis, 1):
                        print(f"  {i}. {api}")
        
            print(f"\n⏱️ Waktu eksekusi: {time.time()-start_time:.2f} detik")
            print("="*60 + "\n")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
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

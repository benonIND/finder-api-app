import requests
from bs4 import BeautifulSoup
from google_play_scraper import app, search

def find_app_website(input_data):
    if 'play.google.com' in input_data:
        return extract_from_playstore(input_data)
    else:
        return search_by_app_name(input_data)

def extract_from_playstore(url):
    try:
        # Ekstrak package name dari URL
        if 'id=' in url:
            package_name = url.split('id=')[1].split('&')[0]
        else:
            package_name = url.split('store/apps/details?id=')[1].split('&')[0]
        
        # Gunakan google-play-scraper
        result = app(
            package_name,
            lang='en',  # bahasa
            country='us'  # negara
        )
        
        if 'developerWebsite' in result and result['developerWebsite']:
            return result['developerWebsite']
        elif 'developerEmail' in result and result['developerEmail']:
            return f"Email Developer: {result['developerEmail']}"
        else:
            return "Informasi developer tidak ditemukan"
            
    except Exception as e:
        return f"Error: {str(e)}"

def search_by_app_name(app_name):
    try:
        # Gunakan fungsi search dari google-play-scraper
        results = search(
            app_name,
            lang='en',
            country='us',
            n_hits=1
        )
        
        if results:
            package_name = results[0]['appId']
            return extract_from_playstore(f"https://play.google.com/store/apps/details?id={package_name}")
        else:
            return "Aplikasi tidak ditemukan di Play Store"
            
    except Exception as e:
        return f"Error: {str(e)}"

# Alternatif fallback dengan mobile user-agent terbaru
def fallback_scrape(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Coba temukan website developer
        website = soup.find('a', {'href': True, 'itemprop': 'url'})
        if website:
            return website['href']
        
        return "Website developer tidak ditemukan (fallback)"
    except:
        return "Gagal melakukan scraping (fallback)"

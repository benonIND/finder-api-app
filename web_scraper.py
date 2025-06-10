import requests
from bs4 import BeautifulSoup

def find_app_website(input_data):
    if 'play.google.com' in input_data:
        return extract_from_playstore(input_data)
    else:
        return search_by_app_name(input_data)

def extract_from_playstore(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari link website developer
        website_link = soup.find('a', {'class': 'hrTbp R8zArc', 'href': True})
        if website_link:
            return website_link['href']
        
        # Fallback: Mencari informasi developer
        developer = soup.find('div', {'class': 'Vbfug auoIOc'})
        if developer:
            return f"Developer: {developer.text}"
        
        return "Website tidak ditemukan"
    except Exception as e:
        return f"Error: {str(e)}"

def search_by_app_name(app_name):
    try:
        search_url = f"https://play.google.com/store/search?q={app_name}&c=apps"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'}
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mengambil hasil pertama
        first_result = soup.find('div', {'class': 'vU6FJ p63iDd'})
        if first_result:
            app_link = "https://play.google.com" + first_result.a['href']
            return extract_from_playstore(app_link)
        
        return "Aplikasi tidak ditemukan"
    except Exception as e:
        return f"Error: {str(e)}"
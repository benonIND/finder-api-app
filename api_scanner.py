import requests
import re
import json
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

def find_api_endpoints(domain, max_results=10):
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Dapatkan konten utama
        print("\nMemindai halaman utama...")
        main_page = session.get(domain, timeout=10).text
        
        # Dapatkan semua link dari halaman
        print("Mengumpulkan link terkait...")
        all_links = get_all_links(main_page, domain)
        
        # Pattern untuk mendeteksi API endpoints
        api_patterns = {
            'REST': [
                r'(https?://[^"\'\s]+/api/v\d+/[^"\'\s]+)',
                r'(https?://api\.[^"\'\s]+/[^"\'\s]*)',
                r'(https?://[^"\'\s]+\.com/api/[^"\'\s]+)',
                r'(https?://[^"\'\s]+\.(io|net|org)/api/[^"\'\s]+)'
            ],
            'GraphQL': [
                r'(https?://[^"\'\s]+/graphql[^"\'\s]*)',
                r'(https?://[^"\'\s]+/gql[^"\'\s]*)'
            ],
            'JSON': [
                r'(https?://[^"\'\s]+\.json[^"\'\s]*)',
                r'(https?://[^"\'\s]+\.php\?[^"\'\s]*format=json[^"\'\s]*)'
            ],
            'Misc': [
                r'(https?://[^"\'\s]+\.php\?[^"\'\s]*api[^"\'\s]*)',
                r'(https?://[^"\'\s]+/rest/[^"\'\s]+)',
                r'(https?://[^"\'\s]+/v\d+/[^"\'\s]+)'
            ]
        }

        print("Memindai endpoint API...")
        api_endpoints = set()
        
        # Scan halaman utama
        api_endpoints.update(scan_text(main_page, api_patterns))
        
        # Scan link terkait (maksimal 5 link tambahan untuk efisiensi)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for link in list(all_links)[:5]:
                futures.append(executor.submit(scan_page, session, link, api_patterns))
            
            for future in as_completed(futures):
                try:
                    api_endpoints.update(future.result())
                except:
                    continue
        
        # Filter dan urutkan hasil
        filtered_apis = filter_and_sort_apis(api_endpoints, domain)
        
        return filtered_apis[:max_results] if filtered_apis else ["Tidak ditemukan API endpoint"]
        
    except Exception as e:
        return [f"Error: {str(e)}"]

def get_all_links(text, base_url):
    soup = BeautifulSoup(text, 'html.parser')
    links = set()
    
    for tag in soup.find_all(['a', 'link', 'script', 'img'], href=True):
        url = urljoin(base_url, tag['href'])
        links.add(url)
    
    for tag in soup.find_all(['script', 'img'], src=True):
        url = urljoin(base_url, tag['src'])
        links.add(url)
    
    return links

def scan_page(session, url, patterns):
    try:
        response = session.get(url, timeout=5)
        return scan_text(response.text, patterns)
    except:
        return set()

def scan_text(text, patterns):
    found = set()
    
    # Scan teks langsung
    for api_type in patterns:
        for pattern in patterns[api_type]:
            matches = re.findall(pattern, text)
            found.update(matches)
    
    # Scan di JavaScript
    js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL)
    for js in js_blocks:
        for api_type in patterns:
            for pattern in patterns[api_type]:
                matches = re.findall(pattern, js)
                found.update(matches)
    
    # Scan di komentar HTML
    comments = re.findall(r'<!--(.*?)-->', text, re.DOTALL)
    for comment in comments:
        for api_type in patterns:
            for pattern in patterns[api_type]:
                matches = re.findall(pattern, comment)
                found.update(matches)
    
    return found

def filter_and_sort_apis(api_endpoints, domain):
    parsed_domain = urlparse(domain)
    filtered = []
    
    for api in api_endpoints:
        # Filter URL yang valid
        if not api.startswith(('http://', 'https://')):
            continue
        
        # Filter parameter tracking
        if any(param in api for param in ['utm_', 'sessionid', 'token']):
            continue
        
        # Prioritaskan API dari domain yang sama
        priority = 0
        if parsed_domain.netloc in api:
            priority = 2
        elif 'api' in api:
            priority = 1
            
        filtered.append((priority, api))
    
    # Urutkan berdasarkan priority dan panjang URL
    filtered.sort(key=lambda x: (-x[0], len(x[1])))
    
    # Hapus duplikat
    seen = set()
    unique_apis = []
    for priority, api in filtered:
        clean_api = api.split('?')[0].split('#')[0]
        if clean_api not in seen:
            seen.add(clean_api)
            unique_apis.append(api)
    
    return unique_apis

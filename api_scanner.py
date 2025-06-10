import requests
import re
import os
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

class APIScanner:
    def __init__(self):
        self.common_patterns = self.load_common_patterns()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.request_delay = 1  # Jeda 1 detik antar request
        self.last_request_time = 0
    
    def load_common_patterns(self):
        patterns = []
        if os.path.exists('list.txt'):
            with open('list.txt', 'r') as f:
                patterns.extend([line.strip() for line in f if line.strip()])
        return patterns or [
            '/api/v1/', '/api/v2/', '/graphql', '/rest/', 
            '/json/', '/oauth/', '/auth/', '/users/'
        ]
    
    def animate_loading(self, frame):
        animation = ["⡿", "⣟", "⣯", "⣷", "⣾", "⣽", "⣻", "⢿"]
        print(f"\r{animation[frame % len(animation)]} Scanning...", end="", flush=True)
    
    def make_request(self, url):
        # Jeda antara request
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400
        except:
            return False
    
    def find_api_endpoints(self, domain, max_results=15):
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        try:
            parsed_domain = urlparse(domain)
            base_url = f"{parsed_domain.scheme}://{parsed_domain.netloc}"
            
            print(f"\n🔍 Memulai scanning pada: {base_url}")
            print("📋 Menggunakan pattern dari list.txt\n")
            
            # Scan halaman utama
            main_page = self.scan_with_progress(domain, "Halaman Utama")
            all_links = self.extract_links(main_page, base_url)
            
            # Scan link terkait
            api_candidates = set()
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i, link in enumerate(list(all_links)[:10], 1):
                    futures.append(executor.submit(
                        self.scan_with_progress, 
                        link, 
                        f"Link #{i}"
                    ))
                
                for future in as_completed(futures):
                    api_candidates.update(future.result())
            
            # Verifikasi endpoint
            print("\n🔎 Memverifikasi endpoint API:")
            verified_apis = []
            for i, api in enumerate(api_candidates, 1):
                if len(verified_apis) >= max_results:
                    break
                
                print(f"\r⏳ Memeriksa {i}/{len(api_candidates)}: {api[:60]}...", end="")
                if self.make_request(api):
                    verified_apis.append(api)
                    print(f"\r✅ Found: {api}")
                else:
                    print(f"\r❌ Not Found: {api}")
            
            return verified_apis or ["Tidak ditemukan API endpoint yang valid"]
            
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def scan_with_progress(self, url, label):
        try:
            for i in range(10):  # Animasi loading
                self.animate_loading(i)
                time.sleep(0.1)
            
            print(f"\r🌐 Scanning {label}: {url}")
            response = self.session.get(url, timeout=10)
            return self.deep_scan(response.text, url)
        except:
            return set()
    
    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for tag in soup.find_all(['a', 'link', 'script', 'img', 'form'], href=True):
            links.add(urljoin(base_url, tag['href']))
        
        for tag in soup.find_all(['script', 'img', 'iframe'], src=True):
            links.add(urljoin(base_url, tag['src']))
        
        return links
    
    def deep_scan(self, text, base_url):
        found = set()
        for pattern in self.common_patterns:
            matches = re.finditer(re.escape(pattern), text)
            for match in matches:
                full_url = self.build_full_url(match.group(), base_url)
                if full_url:
                    found.add(full_url)
        return found
    
    def build_full_url(self, path, base_url):
        if not path or path.startswith(('javascript:', 'mailto:', 'tel:')):
            return None
        
        if path.startswith(('http://', 'https://')):
            return path
        
        return urljoin(base_url, path)

def find_api_endpoints(domain, max_results=15):
    scanner = APIScanner()
    return scanner.find_api_endpoints(domain, max_results)

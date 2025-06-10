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
            return (url, response.status_code < 400)
        except Exception as e:
            return (url, False)
    
    def find_api_endpoints(self, domain, max_results=15):
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        try:
            parsed_domain = urlparse(domain)
            base_url = f"{parsed_domain.scheme}://{parsed_domain.netloc}"
            
            print(f"\n🔍 Memulai scanning pada: {base_url}")
            print("📋 Menggunakan pattern dari list.txt\n")
            
            # Scan halaman utama
            print("🌐 Scanning halaman utama...")
            main_page = self.session.get(domain, timeout=10).text
            main_page_apis = self.deep_scan(main_page, base_url)
            
            # Scan link terkait
            print("\n🔗 Mengumpulkan link terkait...")
            all_links = self.extract_links(main_page, base_url)
            link_apis = set()
            
            # Batasi jumlah thread untuk menghindari blocking
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for link in list(all_links)[:10]:  # Batasi jumlah link yang discan
                    futures.append(executor.submit(self.scan_page, link))
                
                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        apis = future.result()
                        link_apis.update(apis)
                        print(f"\r📡 Progress: {i}/{len(futures)} link discan", end="")
                    except:
                        continue
            
            # Gabungkan semua hasil
            all_apis = main_page_apis.union(link_apis)
            
            # Verifikasi endpoint
            print("\n\n🔎 Memverifikasi endpoint API:")
            verified_apis = []
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(self.make_request, api) for api in all_apis]
                for i, future in enumerate(as_completed(futures), 1):
                    url, is_valid = future.result()
                    status = "✅ Found" if is_valid else "❌ Not Found"
                    print(f"{status}: {url}")
                    if is_valid:
                        verified_apis.append(url)
                    if len(verified_apis) >= max_results:
                        break
            
            return verified_apis[:max_results] if verified_apis else ["Tidak ditemukan API endpoint yang valid"]
            
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def scan_page(self, url):
        try:
            response = self.session.get(url, timeout=8)
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

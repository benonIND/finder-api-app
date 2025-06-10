import requests
import re
import os
import time
import urllib3
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Nonaktifkan peringatan SSL untuk testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UnifiedScanner:
    def __init__(self):
        self.api_patterns = self.load_patterns('list_api.txt') or [
            '/api/v1', '/api/v2', '/graphql', '/rest', 
            '/json', '/auth', '/users', '/admin'
        ]
        self.subdomain_patterns = self.load_patterns('list_subdomain.txt') or [
            'www', 'api', 'admin', 'test', 'dev'
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.request_delay = 0.5
        self.last_request_time = 0
        
        # SSL Configuration
        self.session.verify = False  # Nonaktifkan verifikasi untuk testing

    def load_patterns(self, filename):
        try:
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"[!] File {filename} tidak ditemukan, menggunakan pattern default")
            return None

    def make_request(self, url):
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
    
        self.last_request_time = time.time()
        try:
            response = self.session.head(
                url, 
                timeout=3, 
                allow_redirects=True,
                verify=True  # Aktifkan verifikasi SSL
            )
            return (url, response.status_code < 400)
        except requests.exceptions.SSLError:
            print(f"  [!] SSL Error pada {url} - Sertifikat tidak valid")
            return (url, False)
        except Exception as e:
            return (url, False)

    def get_base_domain(self, url):
        """Ekstrak domain utama dari URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        netloc = parsed.netloc
        if ':' in netloc:  # Hapus port jika ada
            netloc = netloc.split(':')[0]
        return netloc

    def find_subdomains(self, base_domain):
        """Temukan subdomain yang aktif"""
        found = []
        print(f"\n[+] Scanning subdomain untuk {base_domain}...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for sub in set(self.subdomain_patterns[:50]):  # Batasi untuk testing
                url = f"https://{sub}.{base_domain}"
                futures.append(executor.submit(self.make_request, url))
            
            for future in as_completed(futures):
                url, is_active = future.result()
                if is_active:
                    print(f"  [+] Found: {url}")
                    found.append(url)
                else:
                    print(f"  [-] Not found: {url}", end='\r')
        
        return found

    def scan_apis(self, url):
        """Scan API endpoints pada sebuah URL"""
        found = set()
        try:
            print(f"\n[+] Scanning APIs di: {url}")
            response = self.session.get(url, timeout=10, verify=False)
            text = response.text
            
            # Cari di HTML
            soup = BeautifulSoup(text, 'html.parser')
            for tag in soup.find_all(['a', 'link', 'script'], href=True):
                self.check_pattern(found, tag['href'], url)
            
            for tag in soup.find_all(['script', 'img'], src=True):
                self.check_pattern(found, tag['src'], url)
            
            # Cari di JavaScript
            js_blocks = soup.find_all('script', {'type': 'text/javascript'})
            for js in js_blocks:
                if js.string:
                    for match in re.finditer(r'https?://[^\s"\']+', js.string):
                        self.check_pattern(found, match.group(), url)
            
            return list(found)
        except Exception as e:
            print(f"  [!] Error scanning {url}: {str(e)}")
            return []

    def check_pattern(self, found_set, path, base_url):
        """Cek apakah path cocok dengan pola API"""
        full_url = self.build_full_url(path, base_url)
        if full_url:
            for pattern in self.api_patterns:
                if re.search(re.escape(pattern), full_url):
                    found_set.add(full_url)

    def build_full_url(self, path, base_url):
        """Bangun URL lengkap dari path relatif/absolut"""
        if not path or path.startswith(('javascript:', 'mailto:', 'tel:')):
            return None
        
        if path.startswith(('http://', 'https://')):
            return path
        
        return urljoin(base_url, path)

    def unified_scan(self, domain_input):
        """Fungsi utama untuk unified scanning"""
        base_domain = self.get_base_domain(domain_input)
        all_targets = [f"https://{base_domain}"]
        
        # Temukan subdomain
        subdomains = self.find_subdomains(base_domain)
        all_targets.extend(subdomains)
        
        # Scan APIs di semua target
        api_results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scan_apis, url): url for url in all_targets}
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    apis = future.result()
                    if apis:
                        api_results[url] = apis
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
        
        return api_results

def unified_scan(domain):
    scanner = UnifiedScanner()
    return scanner.unified_scan(domain)

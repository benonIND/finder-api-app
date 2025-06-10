import requests
import re
import os
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

class UnifiedScanner:
    def __init__(self):
        self.api_patterns = self.load_patterns('list_api.txt')
        self.subdomain_patterns = self.load_patterns('list_subdomain.txt')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.request_delay = 1
        self.last_request_time = 0
        self.found_apis = []
        self.found_subdomains = []

    def load_patterns(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return []

    def make_request(self, url):
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return (url, response.status_code < 400)
        except:
            return (url, False)

    def scan_subdomain(self, base_domain, subdomain):
        url = f"https://{subdomain}.{base_domain}"
        try:
            response = self.session.head(url, timeout=5)
            if response.status_code < 400:
                self.found_subdomains.append(url)
                return url
        except:
            pass
        return None

    def scan_apis_on_url(self, url):
        try:
            response = self.session.get(url, timeout=10)
            found_apis = self.deep_scan(response.text, url)
            
            verified_apis = []
            for api in found_apis:
                api_url, is_valid = self.make_request(api)
                if is_valid:
                    verified_apis.append(api_url)
            
            return verified_apis
        except:
            return []

    def deep_scan(self, text, base_url):
        found = set()
        for pattern in self.api_patterns:
            matches = re.finditer(re.escape(pattern), text)
            for match in matches:
                full_url = self.build_full_url(match.group(), base_url)
                if full_url:
                    found.add(full_url)
        return found

    def build_full_url(self, path, base_url):
        if not path or path.startswith(('javascript:', 'mailto:', 'tel:')):
            return None
        return urljoin(base_url, path)

    def unified_scan(self, domain):
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain

        parsed = urlparse(domain)
        base_domain = parsed.netloc
        if ':' in base_domain:  # Remove port if exists
            base_domain = base_domain.split(':')[0]

        print(f"\n🔍 Memulai Unified Scan pada: {base_domain}")
        print("="*60)
        
        # Step 1: Scan subdomains
        print("\n🔗 Mencari subdomain aktif...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for sub in self.subdomain_patterns[:100]:  # Batasi 100 subdomain untuk demo
                futures.append(executor.submit(self.scan_subdomain, base_domain, sub))
            
            for future in as_completed(futures):
                future.result()  # Hasil disimpan di self.found_subdomains

        # Step 2: Scan APIs on each found domain
        print("\n🔎 Memindai API endpoints:")
        all_domains = [domain] + self.found_subdomains
        api_results = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.scan_apis_on_url, url): url for url in all_domains}
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    apis = future.result()
                    if apis:
                        api_results[url] = apis
                except:
                    continue

        return api_results

def unified_scan(domain):
    scanner = UnifiedScanner()
    return scanner.unified_scan(domain)

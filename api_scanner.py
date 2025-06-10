import requests
import re
import os
import time
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

class UnifiedScanner:
    def __init__(self):
        self.request_timeout = 10
        self.max_threads = 10
        self.request_delay = 0.5
        
        # Load patterns
        self.api_patterns = self.load_patterns('list_api.txt')
        self.subdomain_patterns = self.load_patterns('list_subdomain.txt')
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_patterns(self, filename):
        try:
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"⚠️ File {filename} tidak ditemukan")
            return []

    def check_url(self, url):
        """Check if URL is accessible"""
        try:
            time.sleep(self.request_delay)  # Rate limiting
            resp = self.session.head(
                url,
                timeout=self.request_timeout,
                allow_redirects=True
            )
            return resp.status_code < 400
        except:
            return False

    def find_subdomains(self, base_domain):
        """Discover active subdomains"""
        active_subdomains = []
        
        def test_subdomain(subdomain):
            url = f"http://{subdomain}.{base_domain}"
            if self.check_url(url):
                active_subdomains.append(url)
                return f"✅ {url}"
            return f"❌ {url}"

        print("\n🔍 Scanning subdomains...")
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            for sub in self.subdomain_patterns[:50]:  # Batasi untuk demo
                futures.append(executor.submit(test_subdomain, sub))
            
            for future in as_completed(futures):
                print(f"\r{future.result()}", end="", flush=True)
        
        return active_subdomains

    def scan_apis(self, base_url):
        """Find API endpoints on a specific URL"""
        found_apis = set()
        
        try:
            # Get page content
            resp = self.session.get(base_url, timeout=self.request_timeout)
            content = resp.text
            
            # Find all URLs matching API patterns
            for pattern in self.api_patterns:
                matches = re.finditer(re.escape(pattern), content)
                for match in matches:
                    full_url = urljoin(base_url, match.group())
                    if any(p in full_url for p in self.api_patterns):
                        found_apis.add(full_url)
            
            # Verify found APIs
            valid_apis = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(self.check_url, api): api for api in found_apis}
                for future in as_completed(futures):
                    if future.result():
                        valid_apis.append(futures[future])
            
            return valid_apis
        except Exception as e:
            print(f"\n⚠️ Error scanning {base_url}: {str(e)}")
            return []

    def unified_scan(self, domain):
        """Main scanning function"""
        # Normalize domain input
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        parsed = urlparse(domain)
        base_domain = parsed.netloc.split(':')[0]  # Remove port if exists
        
        print(f"\n🚀 Starting Unified Scan for: {base_domain}")
        print("="*50)
        
        # Step 1: Find active subdomains
        active_domains = [domain] + self.find_subdomains(base_domain)
        
        # Step 2: Scan each domain for APIs
        print("\n🔎 Scanning for APIs...")
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(self.scan_apis, url): url for url in active_domains}
            
            for future in as_completed(futures):
                url = futures[future]
                apis = future.result()
                if apis:
                    results[url] = apis
                print(f"\rScanned: {url} | Found: {len(apis)} APIs", end="", flush=True)
        
        return results

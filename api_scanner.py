import requests
import re
import os
import time
import sys, socket
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UnifiedScanner:
    def __init__(self):
        # Load patterns
        self.api_patterns = self.load_patterns('list_api.txt') or [
            '/api', '/graphql', '/rest', '/v1', '/v2', '/json'
        ]
        self.subdomain_patterns = self.load_patterns('list_subdomain.txt') or [
            'www', 'api', 'admin', 'test', 'dev', 'staging'
        ]
        
        # Session configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        })
        self.request_delay = 3  # 1 second delay between requests
        self.last_request_time = 0
        self.scanning_active = True

    def load_patterns(self, filename):
        try:
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"[!] File {filename} tidak ditemukan, menggunakan pattern default")
            return None

    def animate_loading(self, text, status=None):
        """Animasi loading dengan status"""
        frames = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        frame = frames[int(time.time() * 4) % len(frames)]
        
        if status == "found":
            sys.stdout.write(f"\r✅ Found: {text}\n")
        elif status == "error":
            sys.stdout.write(f"\r❌ Error: {text}\n")
        elif status == "not_found":
            sys.stdout.write(f"\r❌ Not Found: {text}\n")
        else:
            sys.stdout.write(f"\r{frame} Scanning: {text[:60]}...{' '*(65-len(text[:60]))}")
        
        sys.stdout.flush()

    def check_request_delay(self):
        """Enforce delay between requests"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def scan_subdomain(self, base_domain, subdomain):
        """Scan single subdomain dengan error handling"""
        url = f"https://{subdomain}.{base_domain}"
        
        try:
            # Cek DNS resolution terlebih dahulu
            socket.gethostbyname(f"{subdomain}.{base_domain}")
        except socket.gaierror:
            self.animate_loading(f"DNS tidak ditemukan: {url}", "error")
            return None
        except Exception as e:
            self.animate_loading(f"Error DNS: {url} ({str(e)})", "error")
            return None

        try:
            self.check_request_delay()
            
            response = self.session.head(
                url,
                timeout=5,
                allow_redirects=True,
                verify=False
            )
            
            if response.status_code < 400:
                self.animate_loading(url, "found")
                return url
            else:
                self.animate_loading(url, "not_found")
                return None

        except requests.exceptions.SSLError:
            self.animate_loading(f"SSL Error: {url}", "error")
            return None
        except requests.exceptions.ConnectionError as e:
            if isinstance(e.args[0], MaxRetryError):
                self.animate_loading(f"Tidak bisa terkoneksi: {url}", "error")
            else:
                self.animate_loading(f"Connection Error: {url}", "error")
            return None
        except requests.exceptions.Timeout:
            self.animate_loading(f"Timeout: {url}", "error")
            return None
        except Exception as e:
            self.animate_loading(f"Error: {url} ({str(e)})", "error")
            return None

    def scan_api_endpoint(self, base_url, api_path):
        """Scan API endpoint dengan error handling"""
        full_url = urljoin(base_url, api_path)
        
        try:
            # Cek validitas URL
            parsed = urlparse(full_url)
            if not parsed.netloc:
                return None

            self.check_request_delay()
            
            response = self.session.head(
                full_url,
                timeout=5,
                allow_redirects=True,
                verify=False
            )
            
            if response.status_code < 400:
                self.animate_loading(full_url, "found")
                return full_url
            else:
                self.animate_loading(full_url, "not_found")
                return None

        except requests.exceptions.SSLError:
            self.animate_loading(full_url, "error")
            return None
        except requests.exceptions.ConnectionError:
            self.animate_loading(f"Connection Error: {full_url}", "error")
            return None
        except requests.exceptions.Timeout:
            self.animate_loading(f"Timeout: {full_url}", "error")
            return None
        except Exception as e:
            self.animate_loading(f"Error: {full_url} ({str(e)})", "error")
            return None

    def find_subdomains(self, base_domain):
        """Find all active subdomains"""
        print(f"\n🔍 Scanning subdomains untuk {base_domain}")
        found_subdomains = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for subdomain in set(self.subdomain_patterns[:100]):  # Limit to 100 for demo
                futures.append(executor.submit(self.scan_subdomain, base_domain, subdomain))
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_subdomains.append(result)
        
        return found_subdomains

    def scan_apis_on_url(self, url):
        """Scan APIs on specific URL"""
        print(f"\n🔎 Scanning APIs di {url}")
        found_apis = []
        
        try:
            # Get page content
            self.check_request_delay()
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find potential API endpoints
            potential_apis = set()
            
            # Check HTML tags
            for tag in soup.find_all(['a', 'link', 'script'], href=True):
                href = tag['href']
                if any(api in href for api in self.api_patterns):
                    potential_apis.add(href)
            
            for tag in soup.find_all(['script', 'img'], src=True):
                src = tag['src']
                if any(api in src for api in self.api_patterns):
                    potential_apis.add(src)
            
            # Check JavaScript content
            scripts = soup.find_all('script', type='text/javascript')
            for script in scripts:
                if script.string:
                    matches = re.finditer(r'https?://[^\s"\']+', script.string)
                    for match in matches:
                        if any(api in match.group() for api in self.api_patterns):
                            potential_apis.add(match.group())
            
            # Verify found APIs
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for api in potential_apis:
                    futures.append(executor.submit(self.scan_api_endpoint, url, api))
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        found_apis.append(result)
        
        except Exception as e:
            print(f"\n❌ Error scanning {url}: {str(e)}")
        
        return found_apis

    def unified_scan(self, domain):
        """Main scanning function"""
        self.scanning_active = True
        
        # Extract base domain
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        parsed = urlparse(domain)
        base_domain = parsed.netloc.split(':')[0]  # Remove port if exists
        
        print(f"\n{'='*60}")
        print(f"🚀 MEMULAI UNIFIED SCAN PADA: {base_domain}")
        print(f"{'='*60}\n")
        
        all_results = {}
        
        try:
            # Step 1: Find subdomains
            subdomains = self.find_subdomains(base_domain)
            target_urls = [domain] + subdomains
            
            # Step 2: Scan APIs on each found URL
            for url in target_urls:
                apis = self.scan_apis_on_url(url)
                if apis:
                    all_results[url] = apis
            
            return all_results
            
        except KeyboardInterrupt:
            self.scanning_active = False
            print("\n🛑 Scan dibatalkan oleh pengguna")
            return {}
        
        except Exception as e:
            print(f"\n❌ Error: {domain}")
            return {}

def unified_scan(domain):
    scanner = UnifiedScanner()
    return scanner.unified_scan(domain)

import requests
import re
import os
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
    
    def load_common_patterns(self):
        patterns = []
        # Pattern bawaan
        patterns.extend([
            r'/api/v\d+/',
            r'/graphql',
            r'/rest/v\d+/',
            r'\.json',
            r'/oauth2/'
        ])
        
        # Load dari file list.txt jika ada
        if os.path.exists('list.txt'):
            with open('list.txt', 'r') as f:
                custom_patterns = [line.strip() for line in f if line.strip()]
                patterns.extend(custom_patterns)
        
        return list(set(patterns))  # Hapus duplikat

    def find_api_endpoints(self, domain, max_results=15):
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        try:
            print("\nMemuat pattern dari list.txt...")
            parsed_domain = urlparse(domain)
            base_url = f"{parsed_domain.scheme}://{parsed_domain.netloc}"
            
            print("Memindai struktur website...")
            main_page = self.session.get(domain, timeout=15).text
            all_links = self.extract_links(main_page, base_url)
            
            print("Mengidentifikasi endpoint API...")
            api_candidates = set()
            
            # Scan halaman utama
            api_candidates.update(self.deep_scan(main_page, base_url))
            
            # Scan link terkait (parallel)
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for link in list(all_links)[:10]:  # Batasi untuk efisiensi
                    futures.append(executor.submit(self.scan_page, link))
                
                for future in as_completed(futures):
                    try:
                        api_candidates.update(future.result())
                    except:
                        continue
            
            # Proses hasil
            scored_apis = self.score_and_filter(api_candidates, base_url)
            return scored_apis[:max_results] if scored_apis else ["Tidak ditemukan API endpoint"]
            
        except Exception as e:
            return [f"Error: {str(e)}"]

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for tag in soup.find_all(['a', 'link', 'script', 'img', 'form'], href=True):
            url = urljoin(base_url, tag['href'])
            links.add(url)
        
        for tag in soup.find_all(['script', 'img', 'iframe'], src=True):
            url = urljoin(base_url, tag['src'])
            links.add(url)
        
        for tag in soup.find_all('form', action=True):
            url = urljoin(base_url, tag['action'])
            links.add(url)
        
        return links

    def scan_page(self, url):
        try:
            response = self.session.get(url, timeout=8)
            return self.deep_scan(response.text, url)
        except:
            return set()

    def deep_scan(self, text, base_url):
        found = set()
        
        # Scan berdasarkan pattern
        for pattern in self.common_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                full_url = self.build_full_url(match.group(), base_url)
                if full_url:
                    found.add(full_url)
        
        # Scan JavaScript dan AJAX calls
        js_patterns = [
            r'fetch\(["\'](.*?)["\']',
            r'axios\.get\(["\'](.*?)["\']',
            r'\.ajax\(.*?url:\s?["\'](.*?)["\']',
            r'window\.location\.href\s?=\s?["\'](.*?)["\']'
        ]
        
        for pattern in js_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                full_url = self.build_full_url(match.group(1), base_url)
                if full_url and any(p in full_url for p in self.common_patterns):
                    found.add(full_url)
        
        return found

    def build_full_url(self, path, base_url):
        if not path or path.startswith('javascript:'):
            return None
        
        if path.startswith(('http://', 'https://')):
            return path
        
        if path.startswith('//'):
            return f"https:{path}" if base_url.startswith('https') else f"http:{path}"
        
        if path.startswith('/'):
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        
        return f"{base_url}/{path}"

    def score_and_filter(self, api_candidates, base_url):
        scored = []
        
        for api in api_candidates:
            score = 0
            
            # Scoring criteria
            if urlparse(base_url).netloc in api:
                score += 3
            
            if any(word in api for word in ['api', 'rest', 'graphql', 'json']):
                score += 2
            
            if any(p in api for p in self.common_patterns):
                score += 2
            
            if api.endswith(('.json', '.php', '.asp', '.aspx')):
                score += 1
            
            if '?' in api:  # Kurangi score untuk URL dengan parameter
                score -= 1
            
            if score > 0:
                scored.append((score, api))
        
        # Urutkan berdasarkan score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Hapus duplikat dan ambil URL saja
        seen = set()
        final_apis = []
        for score, api in scored:
            clean_api = api.split('?')[0].split('#')[0]
            if clean_api not in seen:
                seen.add(clean_api)
                final_apis.append(api)
        
        return final_apis

def find_api_endpoints(domain, max_results=15):
    scanner = APIScanner()
    return scanner.find_api_endpoints(domain, max_results)

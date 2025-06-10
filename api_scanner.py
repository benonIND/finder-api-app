import requests
import re
from urllib.parse import urlparse

def find_api_endpoints(domain):
    if not domain.startswith('http'):
        domain = 'https://' + domain
    
    try:
        response = requests.get(domain)
        api_patterns = [
            r'https?://[^\s"\']+?/api/v\d+/[^\s"\']+',
            r'https?://api\.[^\s"\']+',
            r'https?://[^\s"\']+?\.com/api/[^\s"\']+',
            r'https?://[^\s"\']+?\.json',
            r'https?://[^\s"\']+?\.php\?[^\s"\']+api[^\s"\']+'
        ]
        
        api_endpoints = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, response.text)
            api_endpoints.update(matches)
        
        # Filter hasil
        parsed_domain = urlparse(domain)
        filtered_apis = [
            api for api in api_endpoints 
            if parsed_domain.netloc in api or 'api' in api
        ]
        
        return filtered_apis if filtered_apis else ["Tidak ditemukan API endpoint"]
    except Exception as e:
        return [f"Error: {str(e)}"]
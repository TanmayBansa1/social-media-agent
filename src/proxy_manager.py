import requests
import random
from typing import List, Optional
import time
import json
import urllib3
import warnings

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxyManager:
    def __init__(self, proxy_source: str = 'file', proxy_config: dict = None):
        print("Initializing ProxyManager...")
        self.proxies: List[dict] = []
        self.current_proxy: Optional[dict] = None
        self.failed_proxies: set = set()  # Will store proxy server URLs as strings
        self.last_rotation: float = 0
        self.rotation_interval: int = 300  # 5 minutes
        
        if proxy_source == 'file' and proxy_config and 'path' in proxy_config:
            self.load_proxies_from_file(proxy_config['path'])
        elif proxy_source == 'service' and proxy_config:
            self.load_service_proxies(proxy_config)
        elif proxy_source == 'free':
            print("Fetching free proxies...")
            from proxy_scraper import scrape_free_proxies
            self.proxies = scrape_free_proxies()
            print(f"Found {len(self.proxies)} proxies")
        elif proxy_source == 'brightdata':
            self.setup_brightdata(proxy_config)
    
    def setup_brightdata(self, config: dict):
        """Setup Bright Data proxy"""
        if not all(k in config for k in ['username', 'password', 'host']):
            raise ValueError("Bright Data config must include username, password, and host")
        
        # Create proxy with country rotation
        countries = config.get('countries', ['us', 'uk', 'ca', 'au'])
        self.proxies = [{
            'server': f"http://{config['username']}-country-{country}:{config['password']}@{config['host']}"
            for country in countries
        }]
        print(f"Initialized Bright Data proxy with {len(self.proxies)} country options")
    
    def load_service_proxies(self, config: dict):
        """Load proxies from a proxy service"""
        if config.get('service') == 'brightdata':
            self.proxies = [{
                'server': f"http://{config['username']}-country-{country}:{config['password']}@zproxy.lum-superproxy.io:22225"
                for country in config.get('countries', ['us'])
            }]
        # Add more services as needed
    
    def load_proxies_from_file(self, filepath: str):
        """Load proxies from file"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    
                    try:
                        # Try JSON format first
                        proxy = json.loads(line)
                        self.proxies.append(proxy)
                    except json.JSONDecodeError:
                        # Fall back to simple format (ip:port:username:password)
                        parts = line.strip().split(':')
                        if len(parts) >= 2:
                            self.proxies.append({
                                'server': f'http://{parts[0]}:{parts[1]}',
                                'username': parts[2] if len(parts) > 2 else None,
                                'password': parts[3] if len(parts) > 3 else None
                            })
        except Exception as e:
            print(f"Error loading proxies: {e}")
    
    def add_proxy(self, proxy: dict):
        """Add a single proxy to the pool"""
        self.proxies.append(proxy)
    
    def get_proxy(self) -> Optional[dict]:
        """Get a working proxy"""
        current_time = time.time()
        
        # Check if we need to rotate
        if (not self.current_proxy or 
            current_time - self.last_rotation > self.rotation_interval):
            
            available_proxies = [p for p in self.proxies 
                               if p['server'] not in self.failed_proxies]
            
            if not available_proxies:
                self.failed_proxies.clear()  # Reset failed proxies
                available_proxies = self.proxies
            
            if available_proxies:
                self.current_proxy = random.choice(available_proxies)
                self.last_rotation = current_time
                print(f"Using Bright Data proxy: {self.current_proxy['server']}")
            else:
                print("No working proxies available!")
                return None
        
        return self.current_proxy
    
    def mark_proxy_failed(self, proxy: dict):
        """Mark a proxy as failed"""
        if proxy in self.proxies:
            # Store just the server URL in the set
            self.failed_proxies.add(proxy['server'])
            if proxy == self.current_proxy:
                self.current_proxy = None
    
    def test_proxy(self, proxy: dict) -> bool:
        """Test if a proxy is working"""
        try:
            print(f"Testing proxy: {proxy['server']}")
            response = requests.get(
                'https://www.instagram.com',
                proxies={
                    'http': proxy['server'],
                    'https': proxy['server']
                },
                auth=(proxy['username'], proxy['password']) if proxy.get('username') else None,
                timeout=5,
                verify=False
            )
            success = response.status_code == 200
            print(f"Proxy {proxy['server']} {'worked' if success else 'failed'}")
            return success
        except Exception as e:
            print(f"Proxy {proxy['server']} failed with error: {str(e)}")
            return False 
import requests
from bs4 import BeautifulSoup
import time
import random

def scrape_free_proxies():
    """Scrape free proxies from multiple public proxy lists"""
    proxies = []
    
    # List of free proxy sources
    sources = [
        {
            'url': 'https://free-proxy-list.net/',
            'scraper': scrape_free_proxy_list
        },
        {
            'url': 'https://www.sslproxies.org/',
            'scraper': scrape_ssl_proxies
        }
    ]
    
    for source in sources:
        try:
            new_proxies = source['scraper'](source['url'])
            proxies.extend(new_proxies)
            # Add delay between requests to avoid getting blocked
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error scraping {source['url']}: {e}")
    
    # Remove duplicates
    unique_proxies = []
    seen = set()
    
    for proxy in proxies:
        proxy_str = proxy['server']
        if proxy_str not in seen:
            seen.add(proxy_str)
            unique_proxies.append(proxy)
    
    print(f"Found {len(unique_proxies)} unique proxies")
    return unique_proxies

def scrape_free_proxy_list(url):
    """Scrape proxies from free-proxy-list.net"""
    proxies = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    proxy_table = soup.find('table')
    if not proxy_table:
        return proxies
        
    for row in proxy_table.find_all('tr')[1:]:  # Skip header
        cols = row.find_all('td')
        if len(cols) >= 7:
            ip = cols[0].text.strip()
            port = cols[1].text.strip()
            https = cols[6].text.strip()
            
            if https == 'yes':
                proxies.append({
                    'server': f'http://{ip}:{port}',
                    'username': None,
                    'password': None
                })
    
    return proxies

def scrape_ssl_proxies(url):
    """Scrape proxies from sslproxies.org"""
    # Similar implementation to free-proxy-list as they have same structure
    return scrape_free_proxy_list(url)

def test_proxy(proxy):
    """Test if a proxy is working"""
    try:
        response = requests.get(
            'https://www.google.com',
            proxies={
                'http': proxy['server'],
                'https': proxy['server']
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False 
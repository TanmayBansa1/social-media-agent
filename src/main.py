import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from playwright.sync_api import sync_playwright
import asyncio
import pandas as pd
import time
import json
from fake_useragent import UserAgent
from proxy_manager import ProxyManager
import random
import urllib3
import warnings

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

class SocialMediaAnalyzer:
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        
        # Add Google Sheets setup
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        self.sheets_creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.sheets = build('sheets', 'v4', credentials=self.sheets_creds)
        
        # Initialize playwright
        self.playwright = sync_playwright().start()
        
        # Initialize proxy manager with Bright Data
        brightdata_config = {
            'username': os.getenv('BRIGHTDATA_USERNAME'),
            'password': os.getenv('BRIGHTDATA_PASSWORD'),
            'host': os.getenv('BRIGHTDATA_HOST', 'zproxy.lum-superproxy.io:22225'),
            'countries': ['us', 'uk', 'ca', 'au']  # Add more countries as needed
        }
        self.proxy_manager = ProxyManager(proxy_source='brightdata', proxy_config=brightdata_config)
        self.ua = UserAgent()
        
        # Setup browser
        self.setup_browser()
        
        # Test connection
        if not self.test_brightdata_connection():
            raise Exception("Failed to connect to Bright Data Scraping Browser")
        
    def setup_browser(self):
        """Setup Bright Data Scraping Browser"""
        print("Connecting to Bright Data Scraping Browser...")
        
        # Construct the WebSocket URL from environment variables
        ws_url = f"wss://{os.getenv('BRIGHTDATA_USERNAME')}:{os.getenv('BRIGHTDATA_PASSWORD')}@{os.getenv('BRIGHTDATA_HOST')}"
        
        try:
            self.browser = self.playwright.chromium.connect_over_cdp(ws_url)
            print("Successfully connected to Bright Data Scraping Browser")
            
            # Create a context with enhanced stealth configurations
            self.context = self.browser.new_context(
                viewport={'width': random.randint(1024, 1920), 
                         'height': random.randint(768, 1080)},
                user_agent=self.ua.random,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                color_scheme='dark'
            )
            print("Browser context created successfully")
            
        except Exception as e:
            print(f"Error connecting to Bright Data Scraping Browser: {str(e)}")
            raise
    
    def add_stealth_scripts(self, page):
        """Add advanced stealth scripts to the page"""
        # Mask WebDriver
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Mask automation
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Add language preferences
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Modify hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // Add fake battery data
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 0.98
            });
        """)
    
    def get_instagram_data(self, username):
        """Fetch Instagram data using Playwright with enhanced stealth"""
        print(f"\nFetching data for Instagram user: {username}")
        max_retries = 3
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                print(f"Attempt {current_retry + 1} of {max_retries}")
                page = self.context.new_page()
                self.add_stealth_scripts(page)
                
                # First, go to Instagram homepage to handle any initial redirects
                print("Navigating to Instagram homepage...")
                page.goto('https://www.instagram.com/', 
                         wait_until='networkidle',
                         timeout=30000)
                
                # Check if we're on the login page
                if page.locator('input[name="username"]').count() > 0:
                    print("Login page detected, attempting to login...")
                    # Try to login with environment variables
                    username_input = page.locator('input[name="username"]')
                    password_input = page.locator('input[name="password"]')
                    
                    if username_input and password_input:
                        username_input.fill(os.getenv('INSTAGRAM_USERNAME', ''))
                        password_input.fill(os.getenv('INSTAGRAM_PASSWORD', ''))
                        page.locator('button[type="submit"]').click()
                        
                        # Wait for login to complete
                        page.wait_for_load_state('networkidle', timeout=30000)
                        
                        # Check if login was successful
                        if page.locator('input[name="username"]').count() > 0:
                            raise Exception("Login failed")
                
                # Now navigate to the profile
                print(f"Navigating to profile: {username}")
                response = page.goto(
                    f'https://www.instagram.com/{username}/',
                    wait_until='networkidle',
                    timeout=30000
                )
                
                if not response:
                    raise Exception("No response from page")
                    
                if response.status >= 400:
                    raise Exception(f"HTTP {response.status}")
                
                print("Waiting for content to load...")
                # Try multiple selectors for the main content
                main_content = None
                for selector in [
                    'div[role="main"]',
                    'main',
                    'article',
                    'div._aagv',
                    'div[style*="padding-bottom: 100%"]'
                ]:
                    try:
                        main_content = page.wait_for_selector(selector, 
                                                           state='visible', 
                                                           timeout=5000)
                        if main_content:
                            print(f"Found main content with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Selector {selector} not found: {str(e)}")
                        continue
                
                if not main_content:
                    raise Exception("Could not find main content on page")
                
                # Take a screenshot for debugging
                page.screenshot(path=f"debug_{username}_{current_retry}.png")
                print(f"Saved debug screenshot to debug_{username}_{current_retry}.png")
                
                print("Getting follower count...")
                # Try different selectors for follower count
                followers = None
                for selector in [
                    'text=/\\d+\\s*(followers|Followers)/',
                    'div[role="main"] ul li:nth-child(2) span',
                    'div[role="main"] ul li:nth-child(2) a span',
                    'div._aacl._aaco._aacw._aacx._aad6._aade'
                ]:
                    try:
                        followers = page.locator(selector).first
                        if followers:
                            break
                    except Exception as e:
                        print(f"Follower selector {selector} failed: {str(e)}")
                        continue
                
                followers_text = followers.text_content() if followers else "N/A"
                print(f"Found {followers_text} followers")
                
                print("Getting bio...")
                # Try different selectors for bio
                bio = None
                for selector in [
                    'div._aa_c',
                    'div[role="main"] div._aa_c',
                    'div[role="main"] div._aacl._aaco._aacu._aacx._aad6._aade',
                    'div._aacl._aaco._aacu._aacx._aad6._aade'
                ]:
                    try:
                        bio = page.locator(selector).first
                        if bio:
                            break
                    except Exception as e:
                        print(f"Bio selector {selector} failed: {str(e)}")
                        continue
                
                bio_text = bio.text_content() if bio else ""
                
                print("Getting recent posts...")
                # Try different selectors for posts
                posts = []
                post_elements = page.locator('article img, div[role="main"] img, div._aagv img').all()[:15]
                print(f"Found {len(post_elements)} posts")
                
                for i, post in enumerate(post_elements, 1):
                    print(f"Processing post {i}/15")
                    post_url = post.get_attribute('src')
                    post_alt = post.get_attribute('alt')
                    
                    try:
                        post.click()
                        page.wait_for_selector('div[role="dialog"]', timeout=5000)
                        
                        views = page.locator('text=/\\d+\\s*views/').first
                        view_count = views.text_content() if views else None
                        
                        posts.append({
                            'url': post_url,
                            'alt': post_alt,
                            'views': view_count
                        })
                        
                        page.keyboard.press('Escape')
                    except Exception as e:
                        print(f"Error processing post {i}: {str(e)}")
                        posts.append({
                            'url': post_url,
                            'alt': post_alt,
                            'views': None
                        })
                
                page.close()
                print("Successfully fetched all data!")
                
                return {
                    'followers': followers_text,
                    'bio': bio_text,
                    'recent_posts': posts
                }
                
            except Exception as e:
                current_retry += 1
                print(f"Attempt {current_retry} failed: {str(e)}")
                
                if current_retry < max_retries:
                    print("Rotating proxy and retrying...")
                    current_proxy = self.proxy_manager.get_proxy()
                    if current_proxy:
                        self.proxy_manager.mark_proxy_failed(current_proxy)
                        self.setup_browser()
                        time.sleep(random.uniform(5, 10))
                    else:
                        print("No more proxies available!")
                        return None
                else:
                    print(f"All retries failed for {username}")
                    return None
            
    def get_youtube_data(self, channel_handle):
        """Fetch YouTube data using the YouTube Data API"""
        print(f"\nFetching data for YouTube channel: {channel_handle}")
        try:
            # First, try to get channel ID from handle
            print("Converting channel handle to ID...")
            search_response = self.youtube.search().list(
                part='id',
                q=channel_handle,
                type='channel',
                maxResults=1
            ).execute()
            
            if not search_response.get('items'):
                print(f"No channel found with handle: {channel_handle}")
                return None
                
            channel_id = search_response['items'][0]['id']['channelId']
            print(f"Found channel ID: {channel_id}")
            
            # Now get channel data
            print("Fetching channel data...")
            channel_response = self.youtube.channels().list(
                part='statistics,snippet',
                id=channel_id
            ).execute()
            
            if not channel_response.get('items'):
                print(f"No channel data found for ID: {channel_id}")
                return None
                
            channel_data = channel_response['items'][0]
            print(f"Found channel: {channel_data['snippet']['title']}")
            
            # Get recent videos
            print("Fetching recent videos...")
            videos_response = self.youtube.search().list(
                part='id',
                channelId=channel_id,
                order='date',
                type='video',
                maxResults=15
            ).execute()
            
            if not videos_response.get('items'):
                print("No videos found for this channel")
                return {
                    'subscriber_count': channel_data['statistics'].get('subscriberCount', 'N/A'),
                    'channel_info': channel_data['snippet'],
                    'recent_videos': []
                }
            
            video_ids = [item['id']['videoId'] for item in videos_response['items']]
            print(f"Found {len(video_ids)} recent videos")
            
            # Get video statistics
            print("Fetching video statistics...")
            videos_stats = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            if not videos_stats.get('items'):
                print("Could not fetch video statistics")
                return {
                    'subscriber_count': channel_data['statistics'].get('subscriberCount', 'N/A'),
                    'channel_info': channel_data['snippet'],
                    'recent_videos': []
                }
            
            print("Successfully fetched all YouTube data")
            return {
                'subscriber_count': channel_data['statistics'].get('subscriberCount', 'N/A'),
                'channel_info': channel_data['snippet'],
                'recent_videos': videos_stats['items']
            }
            
        except Exception as e:
            print(f"Error fetching YouTube data: {str(e)}")
            print("Full error details:", e.__class__.__name__)
            if hasattr(e, 'response'):
                print("API Response:", e.response)
            return None

    def read_sheet_data(self, spreadsheet_id, range_name):
        """
        Read influencer handles from Google Sheet
        Example range_name: 'Sheet1!A2:B20'
        """
        try:
            result = self.sheets.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                print('No data found in sheet')
                return []
                
            # Convert to list of dicts
            headers = ['platform', 'handle']
            return [dict(zip(headers, row)) for row in rows]
            
        except Exception as e:
            print(f"Error reading from sheet: {str(e)}")
            return []
    
    def write_analytics_data(self, spreadsheet_id, range_name, data):
        """
        Write analytics data back to Google Sheet
        data should be a list of lists matching the sheet structure
        """
        try:
            body = {
                'values': data
            }
            result = self.sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            print(f"{result.get('updatedCells')} cells updated")
            return True
            
        except Exception as e:
            print(f"Error writing to sheet: {str(e)}")
            return False
    
    def process_influencers(self, spreadsheet_id):
        """Main function to process all influencers from sheet"""
        print("\nStarting to process influencers...")
        
        # Read influencer handles
        print("Reading from Google Sheet...")
        influencers = self.read_sheet_data(spreadsheet_id, 'Input!A2:B')
        print(f"Found {len(influencers)} influencers to process")
        
        # Prepare results array
        results = []
        headers = [
            'Platform', 'Handle', 'Followers/Subscribers', 'Location',
            'Content Language', 'Avg Views (15)', 'Avg Reach (15)',
            'Avg Views (Branded)', 'Est. Gender Split', 'Est. State Split',
            'Est. Age Split'
        ]
        results.append(headers)
        
        for i, influencer in enumerate(influencers, 1):
            print(f"\nProcessing influencer {i}/{len(influencers)}")
            platform = influencer['platform'].lower()
            handle = influencer['handle']
            print(f"Platform: {platform}, Handle: {handle}")
            
            if platform == 'instagram':
                data = self.get_instagram_data(handle)
                if data:
                    print("Successfully processed Instagram data")
                    # Process Instagram data
                    row = [
                        'Instagram',
                        handle,
                        data['followers'],
                        self.extract_location(data['bio']),
                        self.detect_language(data['bio'], platform='instagram'),
                        self.calculate_avg_views(data['recent_posts']),
                        self.calculate_avg_reach(data['recent_posts']),
                        self.calculate_branded_views(data['recent_posts']),
                        'TBD',  # Gender split
                        'TBD',  # State split
                        'TBD'   # Age split
                    ]
                    results.append(row)
                    
            elif platform == 'youtube':
                data = self.get_youtube_data(handle)
                if data:
                    print("Successfully processed YouTube data")
                    # Process YouTube data
                    row = [
                        'YouTube',
                        handle,
                        data['subscriber_count'],
                        data['channel_info'].get('country', 'Unknown'),
                        self.detect_language(
                            data['channel_info'].get('description', ''),
                            platform='youtube',
                            channel_info=data['channel_info']
                        ),
                        self.calculate_yt_avg_views(data['recent_videos']),
                        'N/A',  # YouTube doesn't provide reach data
                        self.calculate_yt_branded_views(data['recent_videos']),
                        'TBD',  # Gender split
                        'TBD',  # State split
                        'TBD'   # Age split
                    ]
                    results.append(row)
        
        print("\nWriting results to Google Sheet...")
        self.write_analytics_data(spreadsheet_id, 'Output!A1:K', results)
        print("Done!")
        
    def calculate_avg_views(self, posts):
        """Calculate average views for Instagram posts"""
        if not posts:
            return "N/A"
            
        total_views = 0
        valid_posts = 0
        
        for post in posts:
            if post.get('views'):
                try:
                    # Extract numeric value from views string (e.g., "1.2M views" -> 1200000)
                    views_str = post['views'].lower()
                    if 'k' in views_str:
                        views = float(views_str.replace('k', '').replace('views', '').strip()) * 1000
                    elif 'm' in views_str:
                        views = float(views_str.replace('m', '').replace('views', '').strip()) * 1000000
                    else:
                        views = float(views_str.replace('views', '').strip())
                    total_views += views
                    valid_posts += 1
                except (ValueError, TypeError):
                    continue
        
        if valid_posts == 0:
            return "N/A"
            
        avg_views = total_views / valid_posts
        return f"{avg_views:,.0f}"
        
    def calculate_avg_reach(self, posts):
        """Calculate average reach for Instagram posts"""
        if not posts:
            return "N/A"
            
        # Estimate reach based on views (typically 2-3x views)
        avg_views = self.calculate_avg_views(posts)
        if avg_views == "N/A":
            return "N/A"
            
        try:
            views = float(avg_views.replace(',', ''))
            # Use a conservative estimate of 2x views for reach
            reach = views * 2
            return f"{reach:,.0f}"
        except ValueError:
            return "N/A"
        
    def calculate_yt_avg_views(self, videos):
        """Calculate average views for YouTube videos"""
        if not videos:
            return "N/A"
            
        total_views = 0
        valid_videos = 0
        
        for video in videos:
            try:
                views = int(video['statistics'].get('viewCount', 0))
                total_views += views
                valid_videos += 1
            except (ValueError, TypeError):
                continue
        
        if valid_videos == 0:
            return "N/A"
            
        avg_views = total_views / valid_videos
        return f"{avg_views:,.0f}"
        
    def detect_language(self, text, platform=None, channel_info=None):
        """Detect content language using multiple methods"""
        # For YouTube, use channel information first
        if platform == 'youtube' and channel_info:
            # Try defaultLanguage first
            lang = channel_info.get('defaultLanguage')
            if lang:
                return lang.split('-')[0]  # Convert 'en-US' to 'en'
                
            # Try default audio language
            lang = channel_info.get('defaultAudioLanguage')
            if lang:
                return lang.split('-')[0]
                
        # For text-based detection
        if not text or not text.strip():
            return 'Unknown'
            
        try:
            # Import here to avoid potential import issues
            from langdetect import detect, LangDetectException
            
            # Clean the text
            text = text.strip()
            
            # Handle very short texts
            if len(text) < 20:  # Increased minimum length for better accuracy
                return 'Unknown'
                
            # Try to detect language
            try:
                lang = detect(text)
                # Map language codes to more readable format
                language_map = {
                    'en': 'English',
                    'es': 'Spanish',
                    'fr': 'French',
                    'de': 'German',
                    'it': 'Italian',
                    'pt': 'Portuguese',
                    'ru': 'Russian',
                    'ja': 'Japanese',
                    'ko': 'Korean',
                    'zh-cn': 'Chinese',
                    'hi': 'Hindi'
                }
                return language_map.get(lang, lang)
            except LangDetectException:
                return 'Unknown'
                
        except ImportError:
            print("Warning: langdetect library not installed. Installing now...")
            try:
                import subprocess
                subprocess.check_call(['pip', 'install', 'langdetect'])
                from langdetect import detect, LangDetectException
                lang = detect(text)
                return lang
            except Exception as e:
                print(f"Error installing/using langdetect: {str(e)}")
                return 'Unknown'
        except Exception as e:
            print(f"Error detecting language: {str(e)}")
            return 'Unknown'

    def extract_location(self, bio):
        """Extract location from bio using NLP patterns"""
        if not bio or not bio.strip():
            return 'Unknown'
            
        # Common location patterns
        location_patterns = [
            r'📍\s*([^,\n]+)',  # Emoji followed by location
            r'Location:\s*([^,\n]+)',  # "Location:" prefix
            r'Based in\s*([^,\n]+)',  # "Based in" prefix
            r'From\s*([^,\n]+)',  # "From" prefix
            r'Living in\s*([^,\n]+)',  # "Living in" prefix
            r'📍\s*([^,\n]+)',  # Location emoji
            r'🌍\s*([^,\n]+)',  # Globe emoji
            r'🌎\s*([^,\n]+)',  # Earth emoji
        ]
        
        import re
        for pattern in location_patterns:
            match = re.search(pattern, bio, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common suffixes
                location = re.sub(r'[.,;].*$', '', location)
                return location
                
        return 'Unknown'

    def calculate_branded_views(self, posts):
        """Calculate average views for branded Instagram posts"""
        if not posts:
            return "N/A"
            
        branded_posts = []
        for post in posts:
            # Check for common branded content indicators
            alt_text = post.get('alt', '').lower()
            if any(indicator in alt_text for indicator in [
                'sponsored', 'ad', 'branded', 'collab', 'partnership',
                'paid', 'promotion', 'sponsor', 'brand', 'product'
            ]):
                branded_posts.append(post)
        
        if not branded_posts:
            return "N/A"
            
        # Calculate average views for branded posts
        total_views = 0
        valid_posts = 0
        
        for post in branded_posts:
            if post.get('views'):
                try:
                    views_str = post['views'].lower()
                    if 'k' in views_str:
                        views = float(views_str.replace('k', '').replace('views', '').strip()) * 1000
                    elif 'm' in views_str:
                        views = float(views_str.replace('m', '').replace('views', '').strip()) * 1000000
                    else:
                        views = float(views_str.replace('views', '').strip())
                    total_views += views
                    valid_posts += 1
                except (ValueError, TypeError):
                    continue
        
        if valid_posts == 0:
            return "N/A"
            
        avg_views = total_views / valid_posts
        return f"{avg_views:,.0f}"

    def calculate_yt_branded_views(self, videos):
        """Calculate average views for branded YouTube videos"""
        if not videos:
            return "N/A"
            
        branded_videos = []
        for video in videos:
            # Check for common branded content indicators in title and description
            title = video['snippet'].get('title', '').lower()
            description = video['snippet'].get('description', '').lower()
            
            if any(indicator in title or indicator in description for indicator in [
                'sponsored', 'ad', 'branded', 'collab', 'partnership',
                'paid', 'promotion', 'sponsor', 'brand', 'product'
            ]):
                branded_videos.append(video)
        
        if not branded_videos:
            return "N/A"
            
        # Calculate average views for branded videos
        total_views = 0
        valid_videos = 0
        
        for video in branded_videos:
            try:
                views = int(video['statistics'].get('viewCount', 0))
                total_views += views
                valid_videos += 1
            except (ValueError, TypeError):
                continue
        
        if valid_videos == 0:
            return "N/A"
            
        avg_views = total_views / valid_videos
        return f"{avg_views:,.0f}"

    def test_brightdata_connection(self):
        """Test if Bright Data Scraping Browser is working"""
        try:
            print("Testing Bright Data Scraping Browser connection...")
            page = self.context.new_page()
            
            # Try to access Instagram
            response = page.goto('https://www.instagram.com', timeout=30000)
            
            if response and response.status == 200:
                print("Successfully connected to Instagram through Bright Data")
                page.close()
                return True
            else:
                print(f"Failed to connect to Instagram. Status: {response.status if response else 'No response'}")
                page.close()
                return False
            
        except Exception as e:
            print(f"Error testing Bright Data connection: {str(e)}")
            return False

    def __del__(self):
        """Cleanup Playwright resources"""
        if hasattr(self, 'browser'):
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop() 
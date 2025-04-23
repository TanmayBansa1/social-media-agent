import random

STEALTH_CONFIGS = {
    'VIEWPORT_SIZES': [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
    ],
    
    'TIMEZONES': [
        'America/New_York',
        'America/Chicago',
        'America/Los_Angeles',
        'America/Phoenix',
    ],
    
    'LANGUAGES': [
        'en-US',
        'en-GB',
        'en-CA',
        'en-AU',
    ],
    
    'PLATFORMS': [
        'Windows NT 10.0',
        'Windows NT 6.3',
        'Macintosh; Intel Mac OS X 10_15_7',
        'Macintosh; Intel Mac OS X 10_14_6',
    ]
}

def get_random_config():
    return {
        'viewport': random.choice(STEALTH_CONFIGS['VIEWPORT_SIZES']),
        'timezone': random.choice(STEALTH_CONFIGS['TIMEZONES']),
        'language': random.choice(STEALTH_CONFIGS['LANGUAGES']),
        'platform': random.choice(STEALTH_CONFIGS['PLATFORMS']),
    } 
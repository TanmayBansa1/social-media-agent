INSTAGRAM_SELECTORS = {
    'followers': "//span[@class='_ac2a']",
    'bio': "//div[@class='_aa_c']",
    'posts': "//article//img"
}

YOUTUBE_API_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly'
]

# AI model configuration for demographic estimation
DEMOGRAPHIC_ESTIMATION = {
    'model_name': 'bert-base-uncased',
    'labels': {
        'gender': ['male', 'female', 'other'],
        'age': ['13-17', '18-24', '25-34', '35-44', '45+'],
        'location': 'state_wise'
    }
} 
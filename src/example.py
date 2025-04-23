from main import SocialMediaAnalyzer
import os
def main():
    analyzer = SocialMediaAnalyzer()
    
    # Replace with your actual spreadsheet ID
    # You can get this from the Google Sheets URL
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    
    analyzer.process_influencers(spreadsheet_id)

if __name__ == '__main__':
    main() 
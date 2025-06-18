import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EUCommissionerScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://commission.europa.eu"
        self.meeting_links = []
        
    def get_page_content(self, url, max_retries=3):
        """Fetch page content with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def extract_commissioner_links(self, main_page_url):
        """Extract all commissioner profile links from the main page"""
        content = self.get_page_content(main_page_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        commissioner_links = []
        
        # Find all links that contain the commissioner pattern
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/about/organisation/college-commissioners/' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in commissioner_links:
                    commissioner_links.append(full_url)
                    logger.info(f"Found commissioner link: {full_url}")
        
        logger.info(f"Found {len(commissioner_links)} unique commissioner links")
        return commissioner_links
    
    def extract_meeting_links(self, commissioner_url):
        """Extract transparency initiative meeting links from a commissioner page"""  
        content = self.get_page_content(commissioner_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        meeting_links = []
        
        # Find all links that contain the meeting pattern
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'https://ec.europa.eu/transparencyinitiative/meetings/meeting.do?host=' in href:
                if href not in meeting_links:
                    meeting_links.append(href)
                    logger.info(f"Found meeting link: {href}")
        
        logger.info(f"Found {len(meeting_links)} meeting links on {commissioner_url}")
        return meeting_links
    
    def scrape_all_meeting_links(self, main_page_url):
        """Main scraping method to get all meeting links"""
        logger.info("Starting EU Commissioner meeting links scraping...")
        
        # Step 1: Get all commissioner links
        commissioner_links = self.extract_commissioner_links(main_page_url)
        
        if not commissioner_links:
            logger.error("No commissioner links found!")
            return []
        
        # Step 2: Extract meeting links from each commissioner page
        all_meeting_links = []
        
        for i, commissioner_url in enumerate(commissioner_links, 1):
            logger.info(f"Processing commissioner {i}/{len(commissioner_links)}: {commissioner_url}")
            
            meeting_links = self.extract_meeting_links(commissioner_url)
            
            # Store meeting links with source commissioner info
            for meeting_link in meeting_links:
                all_meeting_links.append({
                    'commissioner_url': commissioner_url,
                    'commissioner_name': self.extract_commissioner_name(commissioner_url),
                    'meeting_link': meeting_link
                })
            
            # Be respectful with delays between requests
            time.sleep(1)
        
        self.meeting_links = all_meeting_links
        logger.info(f"Total meeting links found: {len(all_meeting_links)}")
        return all_meeting_links
    
    def extract_commissioner_name(self, commissioner_url):
        """Extract commissioner name from URL"""
        # Extract the last part of the URL path as the name
        path_parts = urlparse(commissioner_url).path.strip('/').split('/')
        if path_parts:
            return path_parts[-1].replace('-', ' ').title()
        return "Unknown"
    
    def export_to_csv(self, filename='eu_meeting_links.csv'):
        """Export meeting links to CSV file"""
        if not self.meeting_links:
            logger.warning("No meeting links to export!")
            return
        
        logger.info(f"Exporting {len(self.meeting_links)} meeting links to {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['commissioner_name', 'commissioner_url', 'meeting_link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for link_data in self.meeting_links:
                writer.writerow(link_data)
        
        logger.info(f"Successfully exported to {filename}")

def main():
    """Main function to run the scraper"""
    scraper = EUCommissionerScraper()
    main_url = "https://commission.europa.eu/about/organisation/college-commissioners_en"
    
    try:
        # Scrape all meeting links
        meeting_links = scraper.scrape_all_meeting_links(main_url)
        
        if meeting_links:
            # Export to CSV
            scraper.export_to_csv('eu_commissioner_meeting_links.csv')
            
            # Print summary
            print(f"\n=== SCRAPING SUMMARY ===")
            print(f"Total meeting links found: {len(meeting_links)}")
            print(f"Data exported to: eu_commissioner_meeting_links.csv")
            
            # Show first few examples
            print(f"\nFirst few meeting links:")
            for i, link in enumerate(meeting_links[:5], 1):
                print(f"{i}. {link['commissioner_name']}: {link['meeting_link']}")
        else:
            print("No meeting links found!")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
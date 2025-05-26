import requests
from bs4 import BeautifulSoup
import feedgenerator
import datetime
import hashlib
import os
import logging
import csv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_table(url):
    """Scrape a table from a given URL using Beautiful Soup."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust the table selector based on your specific websites
    table = soup.select_one('#listMeetingsTable')
    directorate = soup.select_one("h3").text.strip().replace("Meetings held by the ", "").replace(" with interest representatives","")
    
    if not table:
        logger.warning(f"No table found at {url}")
        return None
    
    return parse_table(table, directorate, url)

def parse_table(table, directorate, source_url):
    """Parse the table into a list of dictionaries."""
    rows = table.find_all('tr')
    if not rows:
        return []
    
    # Extract headers
    headers = [header.text.strip() for header in rows[0].find_all(['th', 'td'])]
    
    # Extract data
    items = []
    for row in rows[1:]:  # Skip the header row
        cells = row.find_all(['td', 'th'])
        if len(cells) == len(headers):
            item = {}
            for i, cell in enumerate(cells):
                item[headers[i]] = cell.text.strip()
            item['source_url'] = source_url
            item['Directorate'] = directorate
            items.append(item)
    
    return items

def create_rss_feed(items, feed_title, feed_description, feed_link, output_file):
    """Create an RSS feed from the parsed items."""
    
    # First, process all dates in your items
    for item in items:
        # Parse the date from item["date"] if it exists, or use Unix epoch beginning (very old date) as fallback
        if "Date" in item and item["Date"]:
            try:
                # Parse date in format "DD/MM/YYYY"
                day, month, year = item["Date"].split('/')
                # Store the parsed datetime object in the item for sorting
                # Use zeros for time components to show only the date
                item["parsed_date"] = datetime.datetime(int(year), int(month), int(day), 0, 0, 0)
            except (ValueError, AttributeError) as e:
                # If date parsing fails, use a very old date for sorting
                logger.warning(f"Could not parse date '{item.get('Date')}': {e}, using epoch start instead")
                item["parsed_date"] = datetime.datetime(1970, 1, 1, 0, 0, 0)
        else:
            # If no date is available, use a very old date for sorting
            item["parsed_date"] = datetime.datetime(1970, 1, 1, 0, 0, 0)
    
    # Sort items by the parsed_date (newest first)
    sorted_items = sorted(items, key=lambda x: x["parsed_date"], reverse=True)
    logger.info(f"Sorted {len(sorted_items)} items by date (newest first)")
    
    feed = feedgenerator.Rss201rev2Feed(
        title=feed_title,
        link=feed_link,
        description=feed_description,
        language="en"
    )
    
    for item in sorted_items:
        # Create a unique ID for each item
        item_id = hashlib.md5(str(item).encode()).hexdigest()
        
        # Create a title from the item data
        # Adjust this to use the most appropriate fields from your table
        #title = " - ".join([f"{k}: {v}" for k, v in item.items() if k != 'source_url'][:2])
        title = f'{item["Subject matter"]}'
        
        # Create a description that includes all the data
        description = "<br>".join([f"<strong>{k}:</strong> {str(v).strip()}" for k, v in item.items() if k != 'source_url'])
        
        pub_date = item["parsed_date"].date()
        
        feed.add_item(
            title=title,
            link=item['source_url'],
            description=description,
            unique_id=item_id,
            pubdate=pub_date
        )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        feed.write(f, 'utf-8')
    
    print(f"RSS feed created: {output_file}")

def main():
    # List of websites to scrape
    host_ids = [
    "cfe4759a-94d7-4925-b721-be0694aeaeee",
    "a8793855-8d00-4dbe-8df4-5a368e3aa86e",
    "0fbdad0a-4342-4091-b766-91b393b97617",
    "5f4689e0-014c-4bec-8125-f9e6d3592c86",
    "8d411331-1f9c-49ad-bf3f-54c9723c5496",
    "394df231-6f63-43a1-ac2f-a5c6c2aea0b7",
    "9c8a817a-8b63-494f-b8aa-7f1d9a3d4aa7",
    "836198d9-3839-4b03-861c-7d7b2dc923bf",
    "19a6da2c-5659-48c1-b351-b8014dd4d54d",
    "c9dd58ff-4f2e-4e64-83c0-0ef45573239d",
    "ed82401c-d412-44bd-bdbc-3d0c5d051337",
    "4a2b905b-d91f-421a-870a-3f9387018669",
    "24e12322-567f-4305-8a81-46e4261aca02",
    "0bdcfdaf-b25f-4fa4-9843-6d8aff622df9",
    "09ed44d4-9995-496b-b508-61f84006ff93",
    "b7f75e74-dd34-4911-8942-3b84e241424d",
    "30674a4b-0bbe-4243-9500-704f334ced64",
    "df6d8307-5772-45fb-a234-be95f3186c1f",
    "19bd5d17-a3ef-4a2b-899c-28126a38b0c2",
    "66b9a93e-bac3-4820-8f21-9576b54e3428",
    "35e322b6-e216-42e2-9b87-b21c41ac0d2a",
    "fd8d5cd6-d490-4257-af03-d5fbb0abca14",
    "5f6cf615-e3f3-495a-846a-9ccc191e86fc",
    "33bb1312-1e91-47f1-afeb-d4d1313630d6",
    "357c8eea-da5c-49bc-9d63-a5c1b76c770e",
    "3bb86a7d-035a-4a39-8226-c46622754eb2",
    "1451b45a-b39b-48ee-a50a-00a440ef2f09",
    "b85b3c8d-483b-4e3d-b066-160c467e2884",
    "e1df1b18-cb0f-47e6-bd6b-9643b9eb5c5c",
    "ca175ad3-c2c5-457e-8f6d-f17956bdcc4e",
    "e780754a-50f5-41fe-b42f-8ffe6165ad35",
    "61569260-525e-42f8-aa52-51d7bfc30d4f",
    "6c877f62-58d1-4645-aa27-bbbc7b872de3",
    "9bd9f7c0-836e-4ff6-abf4-a1f8650861cb",
    "e2ac53f7-cf9c-4aa7-a7fd-06a355c8b361",
    "06fb3b80-76a8-43f1-b1a5-e703cfe8d625",
    "3c3c8b28-6aa7-4b6b-b3d1-c06e22e002b4",
    "ffdb1b81-84a9-4ce1-8974-164aa26ce7e8",
    "aae7124c-b839-4139-9ffe-ad5660fe9404",
    "2aac00d9-fbaf-425f-af65-c697a37d51bb",
    "e5538979-4674-413c-9912-75853e91bdc5",
    "1eefac79-31f7-41ef-b1f0-3d1270ce33a9",
    "d41e42be-7ff1-4635-bb4f-e47d38f886ed"
]
    
    urls = [f"https://ec.europa.eu/transparencyinitiative/meetings/meeting.do?host={host}" for host in host_ids]
    
    all_items = []
    
    for url in urls:
        logger.info(f"Scraping {url}")
        items = scrape_table(url)
        if items:
            all_items.extend(items)
    
    # Ensure the docs directory exists
    os.makedirs('docs', exist_ok=True)
    
    # Create the RSS feed
    create_rss_feed(
        items=all_items,
        feed_title="Table Data RSS Feed",
        feed_description="RSS feed generated from all the available DG minutes websites",
        feed_link="https://followthemoney.github.io/eu_minutes_rss/feed.xml",
        output_file="docs/feed.xml"
    )
    
    # Create a simple HTML page that links to the feed
    with open('docs/index.html', 'w') as f:
        f.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>EU minutes RSS Feed</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="alternate" type="application/rss+xml" title="EU minutes RSS Feed" href="feed.xml" />
</head>
<body>
    <h1>Table Data RSS Feed</h1>
    <p>This page hosts an RSS feed generated from all the available DG minutes websites.</p>
    <p>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><a href="feed.xml">Subscribe to the RSS Feed</a></p>
</body>
</html>''')
    
    logger.info(f"Processed {len(all_items)} items from {len(urls)} websites")
    logger.info("Feed and index page created in the docs directory")

if __name__ == "__main__":
    main()

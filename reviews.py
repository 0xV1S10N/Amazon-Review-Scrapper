from selectorlib import Extractor
import requests 
import csv
from dateutil import parser as dateparser
from time import sleep

# Load the YAML file for the selector
e = Extractor.from_yaml_file('selectors.yml')

def scrape(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    }

    print(f"Downloading {url}")
    r = requests.get(url, headers=headers)

    # Check if the page is blocked or redirected to login page
    if r.status_code == 200 and "signin" not in r.url:  # Avoid login redirects
        return e.extract(r.text)
    elif "signin" in r.url:
        print(f"Page {url} was redirected to Amazon login. Skipping.")
        return None
    else:
        print(f"Page {url} was blocked or encountered an error. Status code: {r.status_code}")
        return None

def scrape_all_reviews(url):
    all_reviews = []
    while url:
        data = scrape(url)
        if not data or 'reviews' not in data:
            break
        
        # Extract reviews from the current page
        all_reviews.extend(data['reviews'])
        
        # Check if there is a next page and update the URL
        next_page = data.get('next_page')
        if next_page:
            url = next_page  # Set the URL for the next page
            sleep(2)  # Be polite and wait before sending the next request
        else:
            url = None  # Exit loop when no more pages are found
    
    return all_reviews

# Write the data to CSV
with open("urls.txt", 'r') as urllist, open('data.csv', 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=["title", "content", "date", "variant", "images", "verified", "author", "rating", "product", "url"], quoting=csv.QUOTE_ALL)
    writer.writeheader()
    
    for url in urllist.readlines():
        reviews = scrape_all_reviews(url.strip())
        if reviews:
            for r in reviews:
                r["product"] = reviews[0].get("product_title", "Unknown Product")
                r['url'] = url.strip()
                
                # Clean up and format data
                if 'verified' in r:
                    r['verified'] = 'Yes' if 'Verified Purchase' in r['verified'] else 'No'
                
                if 'rating' in r:
                    r['rating'] = r['rating'].split(' out of')[0]
                
                date_posted = r['date'].split('on ')[-1]
                r['date'] = dateparser.parse(date_posted).strftime('%d %b %Y')
                
                if r.get('images'):
                    r['images'] = "\n".join(r['images'])
                
                writer.writerow(r)

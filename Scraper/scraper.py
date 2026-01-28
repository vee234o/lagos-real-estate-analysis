import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

LOCATIONS = [
    "https://nigeriapropertycentre.com/for-rent/lagos/lekki/lekki-phase-1",
    "https://nigeriapropertycentre.com/for-rent/lagos/lekki/ikate",
    "https://nigeriapropertycentre.com/for-rent/lagos/lekki/agungi",
    "https://nigeriapropertycentre.com/for-rent/lagos/lekki/chevron"
]

STATE_FILE = "state_lekki_central.txt"
CSV_FILE = "Lekki_Central_Data.csv"
PAGES_PER_RUN = 5

scraper = cloudscraper.create_scraper()

def get_last_page():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def save_last_page(page_num):
    with open(STATE_FILE, "w") as f:
        f.write(str(page_num))

def scrape_zone():
    all_results = []
    
    start_page = get_last_page() + 1
    end_page = start_page + PAGES_PER_RUN
    
    print(f"Starting Run from Page {start_page}...")

    for base_url in LOCATIONS:
        area_name = base_url.split('/')[-1].upper()
        print(f"--- Scraping Zone: {area_name} ---")

        for page in range(start_page, end_page):
            url = f"{base_url}?page={page}"
            try:
                response = scraper.get(url)
                
                if response.status_code == 403:
                    print(f"Still Blocked on {url}. Change internet connection.")
                    continue
                elif response.status_code != 200:
                    print(f"Error {response.status_code} on page {page}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                props = soup.find_all('div', class_='wp-block') 

                if not props:
                    print(f"   No houses found on page {page}. Moving on.")
                    break

                for p in props:
                    try:
                        title_tag = p.find('h4', class_='content-title')
                        title = title_tag.get_text(strip=True) if title_tag else "N/A"

                        loc_tag = p.find('address') 
                        if not loc_tag:
                            content_div = p.find('div', class_='wp-block-content')
                            if content_div:
                                loc_tag = content_div.find('strong')

                        if loc_tag:
                            location = loc_tag.get_text(strip=True)
                        else:
                            location = "N/A" 
                        
                        price_span = p.find('span', class_='pull-sm-left')
                        price = price_span.get_text(strip=True) if price_span else "0"
                        
                        link_tag = p.find('a', itemprop='url')
                        link = "https://nigeriapropertycentre.com" + link_tag['href'] if link_tag else "N/A"

                        bed, bath, toilet = 0, 0, 0
                        aux_info = p.find('ul', class_='aux-info')
                        if aux_info:
                            for li in aux_info.find_all('li'):
                                txt = li.get_text(strip=True).lower()
                                val_span = li.find('span')
                                val = val_span.get_text(strip=True) if val_span else "0"
                                if "bed" in txt: bed = val
                                elif "bath" in txt: bath = val
                                elif "toilet" in txt: toilet = val

                        all_results.append({
                            'title': title,
                            'location': location,
                            'price': price,
                            'bedrooms': bed,
                            'bathrooms': bath,
                            'toilets': toilet,
                            'property_type': title,
                            'url': link
                        })
                    except:
                        continue 

                print(f"   {area_name} Page {page}: Found {len(props)} listings.")
                
                time.sleep(random.uniform(4, 7))

            except Exception as e:
                print(f"Error: {e}")

    if all_results:
        df_new = pd.DataFrame(all_results)
        
        if os.path.exists(CSV_FILE):
            df_old = pd.read_csv(CSV_FILE)
            df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['url'], keep='last')
        else:
            df_final = df_new

        df_final.to_csv(CSV_FILE, index=False)
        save_last_page(end_page)
        print(f"Success! Saved {len(df_final)} listings.")
    else:
        print("No data collected. Please change internet connection.")

if __name__ == "__main__":
    while True:
        scrape_zone()
        
        print("-" * 30)
        choice = input("Batch finished! Type 'y' to continue or 'n' to stop: ")
        
        if choice.lower() != 'y':
            print("Stopping script. Your data is saved.")
            break
            
        print("Continuing to next batch...")
        time.sleep(2)
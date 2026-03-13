import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import pytz

URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
# Using a specific string to match your club variations without including 'WECOLORS'
MY_CLUB_MATCH = "AB PREMIÀ"

# Exact keys from the website table in your screenshot
CAT_CONFIG = {
    "C.C. SOTS-25 MASCULÍ NIVELL A": "🔵",
    "C.T. JÚNIOR FEMENÍ PROMOCIÓ": "⚪️",
    "ESCOBOL (LLIGA)": "🐣"
}

def scrape():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(URL, headers=headers)
        res.encoding = 'utf-8' # Crucial for 'À' and 'Í'
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch URL: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Basketball Games')

    # Selecting rows within the table body to avoid header issues
    rows = soup.find_all("tr")
    found_count = 0

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        
        # Clean text: replace non-breaking spaces and normalize
        cat_text = cells[4].get_text(" ", strip=True).replace('\xa0', ' ').upper()
        
        # 1. Match Category
        matched_emoji = None
        for cat_name, emoji in CAT_CONFIG.items():
            if cat_name.upper() in cat_text:
                matched_emoji = emoji
                break
        
        # If the category doesn't match one of your 3, skip it (this ignores SUPER COPA)
        if not matched_emoji:
            continue

        try:
            local_team = cells[2].get_text(strip=True).upper()
            visitor_team = cells[3].get_text(strip=True).upper()
            
            # 2. Determine Home/Away
            if MY_CLUB_MATCH in local_team:
                travel_emoji = "🏠"
                opponent = cells[3].get_text(strip=True)
            else:
                travel_emoji = "✈️"
                opponent = cells[2].get_text(strip=True)

            title = f"{matched_emoji} {travel_emoji} {opponent}"

            # 3. Parse Time
            date_val = cells[0].get_text(strip=True)
            time_val = cells[1].get_text(strip=True)
            
            if ":" not in time_val:
                time_val = "00:00"

            dt_start = datetime.strptime(f"{date_val} {time_val}", '%d/%m/%Y %H:%M')
            dt_start = pytz.timezone("Europe/Madrid").localize(dt_start)
            dt_end = dt_start + timedelta(minutes=90)
            
            # 4. Build Event
            event = Event()
            event.add('summary', title)
            event.add('dtstart', dt_start)
            event.add('dtend', dt_end)
            event.add('location', cells[5].get_text(" ", strip=True))
            
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(minutes=-30))
            event.add_component(alarm)

            cal.add_component(event)
            found_count += 1
            print(f"Added: {title} on {date_val}")

        except Exception as e:
            print(f"Error parsing row: {e}")

    print(f"Total events created: {found_count}")
    
    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    scrape()

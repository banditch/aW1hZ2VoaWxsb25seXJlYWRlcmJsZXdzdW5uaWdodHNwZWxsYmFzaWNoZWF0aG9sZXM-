import cloudscraper
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import pytz

URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
# Target club variation
MY_CLUB_MATCH = "AB PREMIÀ"

# Category mapping
CAT_CONFIG = {
    "C.C. SOTS-25 MASCULÍ NIVELL A": "🔵",
    "C.T. JÚNIOR FEMENÍ PROMOCIÓ": "⚪️",
    "ESCOBOL (LLIGA)": "🐣"
}

def scrape():
    # Initialize the scraper to bypass 403 blocks
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    print(f"Fetching URL: {URL}")
    
    try:
        res = scraper.get(URL)
        res.encoding = 'utf-8' # Ensure Catalan characters are read correctly
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Basketball Games')

    rows = soup.find_all("tr")
    found_count = 0

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        
        # Get category text and normalize it
        cat_text = cells[4].get_text(" ", strip=True).replace('\xa0', ' ').upper()
        
        # 1. Match Category (ignores others like SUPER COPA)
        matched_emoji = None
        for cat_name, emoji in CAT_CONFIG.items():
            if cat_name.upper() in cat_text:
                matched_emoji = emoji
                break
        
        if not matched_emoji:
            continue

        try:
            local_team = cells[2].get_text(strip=True).upper()
            visitor_team = cells[3].get_text(strip=True).upper()
            
            # 2. Determine Home/Away and Opponent
            if MY_CLUB_MATCH in local_team:
                travel_emoji = "🏠"
                opponent = cells[3].get_text(strip=True)
            else:
                travel_emoji = "✈️"
                opponent = cells[2].get_text(strip=True)

            title = f"{matched_emoji} {travel_emoji} {opponent}"

            # 3. Parse Date and Time
            date_val = cells[0].get_text(strip=True) # DD/MM/YYYY
            time_val = cells[1].get_text(strip=True) # HH:MM
            
            # Handle cases where time is not yet defined
            if ":" not in time_val:
                time_val = "00:00"

            dt_start = datetime.strptime(f"{date_val} {time_val}", '%d/%m/%Y %H:%M')
            dt_start = pytz.timezone("Europe/Madrid").localize(dt_start)
            dt_end = dt_start + timedelta(minutes=90)
            
            # 4. Build Ical Event
            event = Event()
            event.add('summary', title)
            event.add('dtstart', dt_start)
            event.add('dtend', dt_end)
            event.add('location', cells[5].get_text(" ", strip=True))
            
            # Add 30-minute alert
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(minutes=-30))
            event.add_component(alarm)

            cal.add_component(event)
            found_count += 1
            print(f"✅ Added: {title} ({date_val})")

        except Exception as e:
            print(f"⚠️ Error parsing row: {e}")

    print(f"\n--- Process finished. Total games added: {found_count} ---")
    
    # Save the file
    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())
    print("File 'basketball.ics' updated successfully.")

if __name__ == "__main__":
    scrape()

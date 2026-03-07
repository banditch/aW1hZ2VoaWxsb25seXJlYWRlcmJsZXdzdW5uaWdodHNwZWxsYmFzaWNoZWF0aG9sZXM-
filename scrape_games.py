import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import pytz

# Config
URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
CATEGORIES_TO_KEEP = [
    "C.T. JÚNIOR FEMENÍ PROMOCIÓ",
    "C.C. SOTS-25 MASCULÍ NIVELL A",
    "ESCOBOL (LLIGA)"
]

def scrape():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')

    # FCBQ usually stores games in table rows <tr>
    rows = soup.find_all('tr')
    
    for row in rows:
        text = row.get_text()
        # Only process if one of your categories is in this row
        if any(cat in text for cat in CATEGORIES_TO_KEEP):
            cols = row.find_all('td')
            if len(cols) < 5: continue
            
            # Note: FCBQ table structure varies, usually:
            # Date/Time | Matchup | Category | Location
            date_str = cols[0].get_text(strip=True) # e.g. 27/09/2025 19:30
            summary = cols[1].get_text(strip=True)  # Team A - Team B
            category = cols[2].get_text(strip=True) 
            location = cols[3].get_text(strip=True)

            try:
                # Parse date (Adjust format if FCBQ uses a different one)
                dt = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                dt = pytz.timezone("Europe/Madrid").localize(dt)
                
                event = Event()
                event.add('summary', f"[{category}] {summary}")
                event.add('dtstart', dt)
                event.add('location', location)
                cal.add_component(event)
            except Exception as e:
                print(f"Error parsing row: {e}")

    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    scrape()

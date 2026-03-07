import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz

URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
CATEGORIES = ["C.T. JÚNIOR FEMENÍ PROMOCIÓ", "C.C. SOTS-25 MASCULÍ NIVELL A", "ESCOBOL (LLIGA)"]

def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')

    rows = soup.select("table tr") 
    
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6: continue
        
        # Mapping based on your screenshot:
        # 0: Data | 1: Hora | 2: Equip Local | 3: Equip Visitant | 4: Categoria | 5: Camp
        date_val = cells[0].get_text(strip=True)
        time_val = cells[1].get_text(strip=True)
        local = cells[2].get_text(strip=True)
        visitor = cells[3].get_text(strip=True)
        cat_text = cells[4].get_text(strip=True)
        location = cells[5].get_text(strip=True)
        
        if any(cat in cat_text for cat in CATEGORIES):
            try:
                # Parse start time
                full_dt_str = f"{date_val} {time_val}"
                dt_start = datetime.strptime(full_dt_str, '%d/%m/%Y %H:%M')
                dt_start = pytz.timezone("Europe/Madrid").localize(dt_start)
                
                # Correct math for end time (Start + 90 minutes)
                dt_end = dt_start + timedelta(minutes=90)
                
                event = Event()
                event.add('summary', f"🏀 {local} vs {visitor}")
                event.add('description', f"Cat: {cat_text}")
                event.add('dtstart', dt_start)
                event.add('dtend', dt_end)
                event.add('location', location)
                cal.add_component(event)
            except Exception as e:
                print(f"Error parsing game: {e}")

    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    scrape()

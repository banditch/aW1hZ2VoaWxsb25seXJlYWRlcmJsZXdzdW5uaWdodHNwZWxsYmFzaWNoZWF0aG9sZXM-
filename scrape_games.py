import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime
import pytz

URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
CATEGORIES = ["C.T. JÚNIOR FEMENÍ PROMOCIÓ", "C.C. SOTS-25 MASCULÍ NIVELL A", "ESCOBOL (LLIGA)"]

def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')

    # Find the main table rows
    rows = soup.select("table tr") 
    
    for row in rows:
        cells = row.find_all("td")
        # Based on your image, we expect at least 6 columns
        if len(cells) < 6: continue
        
        # Mapping based on your provided screenshot:
        # 0: Data | 1: Hora | 2: Equip Local | 3: Equip Visitant | 4: Categoria | 5: Camp de joc
        date_val = cells[0].get_text(strip=True)
        time_val = cells[1].get_text(strip=True)
        local = cells[2].get_text(strip=True)
        visitor = cells[3].get_text(strip=True)
        cat_text = cells[4].get_text(strip=True)
        location = cells[5].get_text(strip=True)
        
        if any(cat in cat_text for cat in CATEGORIES):
            try:
                # Combine Date and Time (e.g., 27/09/2025 + 19:30)
                full_dt_str = f"{date_val} {time_val}"
                dt = datetime.strptime(full_dt_str, '%d/%m/%Y %H:%M')
                dt = pytz.timezone("Europe/Madrid").localize(dt)
                
                event = Event()
                event.add('summary', f"{local} vs {visitor}")
                event.add('description', f"Category: {cat_text}")
                event.add('dtstart', dt)
                # Setting end time to 1.5 hours after start
                event.add('dtend', dt.replace(minute=dt.minute + 90) if dt.minute < 30 else dt.replace(hour=dt.hour + 2))
                event.add('location', location)
                cal.add_component(event)
            except Exception as e:
                print(f"Error parsing game: {e}")

    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    scrape()

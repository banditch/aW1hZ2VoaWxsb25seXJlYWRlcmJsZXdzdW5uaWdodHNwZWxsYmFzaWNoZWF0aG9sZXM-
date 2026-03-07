import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import pytz

URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
# Your club name to determine Home/Away
MY_CLUB = "AB PREMIÀ"

# Category mapping with your requested emojis
CAT_CONFIG = {
    "C.C. SOTS-25 MASCULÍ NIVELL A": "🔵",
    "C.T. JÚNIOR FEMENÍ PROMOCIÓ": "⚪️",
    "ESCOBOL (LLIGA)": "🐣"
}

def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Basketball Games')

    rows = soup.select("table tr") 
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6: continue
        
        cat_text = cells[4].get_text(strip=True)
        
        # Check if the row belongs to one of your 3 categories
        if any(cat in cat_text for cat in CAT_CONFIG):
            try:
                # 1. Determine Category Emoji
                cat_emoji = next(emoji for cat, emoji in CAT_CONFIG.items() if cat in cat_text)
                
                # 2. Determine Home/Away and Opponent
                local_team = cells[2].get_text(strip=True)
                visitor_team = cells[3].get_text(strip=True)
                
                if MY_CLUB in local_team.upper():
                    travel_emoji = "🏠"
                    opponent = visitor_team
                else:
                    travel_emoji = "✈️"
                    opponent = local_team

                # 3. Create Title: "Emoji Emoji Opponent"
                title = f"{cat_emoji} {travel_emoji} {opponent}"

                # 4. Parse Time
                date_val = cells[0].get_text(strip=True)
                time_val = cells[1].get_text(strip=True)
                dt_start = datetime.strptime(f"{date_val} {time_val}", '%d/%m/%Y %H:%M')
                dt_start = pytz.timezone("Europe/Madrid").localize(dt_start)
                dt_end = dt_start + timedelta(minutes=90)
                
                # 5. Build Event
                event = Event()
                event.add('summary', title)
                event.add('dtstart', dt_start)
                event.add('dtend', dt_end)
                event.add('location', cells[5].get_text(strip=True))
                
                # Alarm reminder
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('trigger', timedelta(minutes=-30))
                event.add_component(alarm)

                cal.add_component(event)
            except Exception as e:
                print(f"Error processing row: {e}")

    with open('basketball.ics', 'wb') as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    scrape()

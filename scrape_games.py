import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import pytz

# The global calendar URL
URL = "https://www.basquetcatala.cat/partits/calendari_club_global/16"
MY_CLUB = "AB PREMIÀ"

CAT_CONFIG = {
    "C.C. SOTS-25 MASCULÍ NIVELL A": "🔵",
    "C.T. JÚNIOR FEMENÍ PROMOCIÓ": "⚪️",
    "ESCOBOL (LLIGA)": "🐣"
}

def scrape():
    # Realistic browser headers to bypass the 403 block
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ca;q=0.8,es;q=0.7',
        'Referer': 'https://www.basquetcatala.cat/',
        'Connection': 'keep-alive',
    }

    print(f"Connecting to BasquetCatala...")

    session = requests.Session()
    try:
        response = session.get(URL, headers=headers, timeout=15)
        response.raise_for_status() # This will raise an error if we get a 403 or 404
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    cal = Calendar()
    cal.add('prodid', '-//FCBQ Club Sync//mx//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Basketball Games')

    rows = soup.select("table tr")
    print(f"Found {len(rows)} potential rows.")

    games_count = 0
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        cat_text = cells[4].get_text(strip=True).upper()

        match_emoji = None
        for cat_name, emoji in CAT_CONFIG.items():
            if cat_name.upper() in cat_text:
                match_emoji = emoji
                break

        if match_emoji:
            try:
                local_team = cells[2].get_text(strip=True)
                visitor_team = cells[3].get_text(strip=True)

                travel_emoji = "🏠" if MY_CLUB.upper() in local_team.upper() else "✈️"
                opponent = visitor_team if travel_emoji == "🏠" else local_team

                title = f"{match_emoji} {travel_emoji} {opponent}"

                date_val = cells[0].get_text(strip=True)
                time_val = cells[1].get_text(strip=True)

                # Check for "Ajornat" (Postponed) or empty times
                if ":" not in time_val:
                    print(f"Skipping game on {date_val} - No valid time (likely postponed)")
                    continue

                dt_start = datetime.strptime(f"{date_val} {time_val}", '%d/%m/%Y %H:%M')
                dt_start = pytz.timezone("Europe/Madrid").localize(dt_start)
                dt_end = dt_start + timedelta(minutes=90)

                event = Event()
                event.add('summary', title)
                event.add('dtstart', dt_start)
                event.add('dtend', dt_end)
                event.add('location', cells[5].get_text(strip=True))

                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('trigger', timedelta(minutes=-30))
                event.add_component(alarm)

                cal.add_component(event)
                games_count += 1
                print(f"Added: {title} ({date_val})")
            except Exception as e:
                print(f"Error processing row: {e}")

    if games_count > 0:
        with open('basketball.ics', 'wb') as f:
            f.write(cal.to_ical())
        print(f"\nSuccess! Created basketball.ics with {games_count} games.")
    else:
        print("\nScraper finished, but 0 games matched your filters.")

if __name__ == "__main__":
    scrape()

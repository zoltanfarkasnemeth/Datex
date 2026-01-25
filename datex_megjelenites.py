import requests
import xml.etree.ElementTree as ET
import folium
from datetime import datetime

# Beállítások
URL = "https://napphub.kozut.hu/hub-web//datex2/3_3/4a8b2505-df5e-4191-8c96-b98263a771b5/pullSnapshotData"
OUTPUT_FILE = "index.html"

# Datex v3.3 Névterek
NS = {
    'ns19': 'http://datex2.eu/schema/3/situation',
    'ns11': 'http://datex2.eu/schema/3/locationReferencing',
    'ns24': 'http://datex2.eu/schema/3/common',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

def update_map():
    print(f"Lekérdezés indítása: {datetime.now()}")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # Alaptérkép (Magyarország)
        m = folium.Map(location=[47.1625, 19.5033], zoom_start=8)
        
        # Automatikus oldalfrissítés a böngészőnek (5 perc)
        m.get_root().header.add_child(folium.Element('<meta http-equiv="refresh" content="300">'))

        count = 0
        for record in root.findall('.//ns19:situationRecord', NS):
            xsi_type = record.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
            type_label = xsi_type.split(':')[-1] if xsi_type else "Esemény"

            lat = record.find('.//ns11:latitude', NS)
            lon = record.find('.//ns11:longitude', NS)
            road = record.find('.//ns11:roadNumber', NS)
            
            # Leírás kinyerése
            vals = record.findall('.//ns24:value', NS)
            desc = next((v.text for v in vals if v.text), "Nincs leírás")

            if lat is not None and lon is not None:
                color = 'red' if 'Accident' in type_label else 'orange' if 'Works' in type_label else 'blue'
                folium.CircleMarker(
                    location=[float(lat.text), float(lon.text)],
                    radius=8,
                    popup=f"<b>{type_label}</b><br>Út: {road.text if road is not None else '?'}<br>{desc}",
                    tooltip=f"{type_label} - {road.text if road is not None else '?'}",
                    fill=True,
                    fill_color=color,
                    color='white',
                    weight=1,
                    fill_opacity=0.8
                ).add_to(m)
                count += 1

        m.save(OUTPUT_FILE)
        print(f"Siker: {count} esemény mentve az {OUTPUT_FILE} fájlba.")
    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    update_map()
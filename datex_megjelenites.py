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

# Magyar vármegyék GeoJSON forrásai (GitHub - futáskor töltődik le)
COUNTIES_SOURCES = [
    "https://raw.githubusercontent.com/onaci/hungarian-counties/main/counties.geojson",
    "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/hungary.geojson",
    "https://raw.githubusercontent.com/ginseng666/GeoJSON-TopoJSON-Austria/master/2021/gemeinden_999_geo.json",  # fallback teszt
]

def fetch_counties_geojson():
    """Magyar vármegyék GeoJSON letöltése több forrásból."""
    sources = [
        "https://raw.githubusercontent.com/onaci/hungarian-counties/main/counties.geojson",
        "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/hungary.geojson",
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                print(f"  GeoJSON OK: {url}")
                print(f"  Feature-ök száma: {len(data.get('features', []))}")
                return data, url
        except Exception as e:
            print(f"  Forrás sikertelen ({url}): {e}")
    return None, None

def update_map():
    print(f"Lekérdezés indítása: {datetime.now()}")
    try:
        # --- DATEX II adatok lekérése ---
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # --- Alaptérkép ---
        m = folium.Map(location=[47.1625, 19.5033], zoom_start=8)
        m.get_root().header.add_child(folium.Element('<meta http-equiv="refresh" content="300">'))

        # --- Vármegyék réteg ---
        print("Vármegyék GeoJSON letöltése...")
        counties_data, counties_url = fetch_counties_geojson()

        counties_layer = folium.FeatureGroup(name="🗺️ Magyar vármegyék", show=True)

        if counties_data:
            # Próbáljuk meg kideríteni a name property kulcsát
            sample_props = counties_data.get('features', [{}])[0].get('properties', {})
            name_key = None
            for key in ['name', 'NAME', 'Name', 'COUNTY', 'county', 'MEGYE', 'megye', 'vm_nev', 'NAME_1']:
                if key in sample_props:
                    name_key = key
                    break
            print(f"  Név property: {name_key}, elérhető kulcsok: {list(sample_props.keys())[:8]}")

            geojson_layer = folium.GeoJson(
                counties_data,
                name="counties_geojson",
                style_function=lambda feature: {
                    'fillColor': '#4A90D9',
                    'color': '#1a5276',
                    'weight': 2,
                    'fillOpacity': 0.3,
                    'opacity': 1.0,
                },
                highlight_function=lambda feature: {
                    'fillColor': '#2E6DA4',
                    'weight': 3,
                    'fillOpacity': 0.5,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=[name_key],
                    aliases=['Vármegye:'],
                    localize=True,
                    sticky=True,
                ) if name_key else None
            )
            geojson_layer.add_to(counties_layer)
            print("  Vármegyék réteg hozzáadva.")
        else:
            print("  FIGYELEM: Vármegyék GeoJSON nem érhető el!")

        counties_layer.add_to(m)

        # --- Közlekedési események réteg ---
        events_layer = folium.FeatureGroup(name="🚦 Közlekedési események", show=True)

        count = 0
        for record in root.findall('.//ns19:situationRecord', NS):
            xsi_type = record.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
            type_label = xsi_type.split(':')[-1] if xsi_type else "Esemény"
            lat = record.find('.//ns11:latitude', NS)
            lon = record.find('.//ns11:longitude', NS)
            road = record.find('.//ns11:roadNumber', NS)

            vals = record.findall('.//ns24:value', NS)
            desc = next((v.text for v in vals if v.text), "Nincs leírás")

            if lat is not None and lon is not None:
                if 'Accident' in type_label:
                    color = 'red'
                elif 'Works' in type_label:
                    color = 'orange'
                else:
                    color = 'blue'

                folium.CircleMarker(
                    location=[float(lat.text), float(lon.text)],
                    radius=8,
                    popup=folium.Popup(
                        f"<b>{type_label}</b><br>Út: {road.text if road is not None else '?'}<br>{desc}",
                        max_width=300
                    ),
                    tooltip=f"{type_label} – {road.text if road is not None else '?'}",
                    fill=True,
                    fill_color=color,
                    color='white',
                    weight=1,
                    fill_opacity=0.8
                ).add_to(events_layer)
                count += 1

        events_layer.add_to(m)

        # --- Rétegvezérlő (bal felső sarok) ---
        folium.LayerControl(position='topleft', collapsed=False).add_to(m)

        # --- Átlátszóság csúszka (a rétegvezérlő alatt, bal felső sarok) ---
        opacity_control_html = """
        <div id="county-opacity-box" style="
            position: fixed;
            top: 140px;
            left: 10px;
            z-index: 9999;
            background: white;
            padding: 10px 14px 12px 14px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.25);
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 12px;
            min-width: 200px;
            border: 1px solid #ccc;
        ">
            <div style="
                font-weight: bold;
                margin-bottom: 8px;
                color: #1a5276;
                font-size: 13px;
                display: flex;
                align-items: center;
                gap: 5px;
            ">
                🗺️ Vármegyék átlátszósága
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <input
                    type="range"
                    id="countyOpacitySlider"
                    min="0" max="100" value="30" step="5"
                    style="
                        flex: 1;
                        accent-color: #1a5276;
                        cursor: pointer;
                        height: 4px;
                    "
                    oninput="setCountyOpacity(this.value)"
                >
                <span id="countyOpacityLabel" style="
                    min-width: 38px;
                    text-align: right;
                    color: #333;
                    font-weight: bold;
                    font-size: 13px;
                ">30%</span>
            </div>
            <div style="
                margin-top: 6px;
                font-size: 10px;
                color: #888;
            ">Csúszka: 0% (átlátszó) – 100% (teli)</div>
        </div>

        <script>
        // GeoJSON path-ok gyűjtése a vármegye réteghez
        // A Leaflet GeoJSON réteg path elemeit a 'leaflet-interactive' class jelöli
        function setCountyOpacity(val) {
            var pct = parseInt(val);
            document.getElementById('countyOpacityLabel').textContent = pct + '%';
            var fillOpacity = pct / 100;

            // Leaflet overlay pane-ban keresünk polygon path-okat
            // (a CircleMarker-ek 'r' attribútummal rendelkeznek, ezeket kihagyjuk)
            var allPaths = document.querySelectorAll(
                '.leaflet-overlay-pane path.leaflet-interactive'
            );
            allPaths.forEach(function(path) {
                // Ha van 'r' attribútum -> CircleMarker -> nem módosítjuk
                if (path.hasAttribute('r')) return;
                // Polygon (vármegye) -> módosítjuk
                path.style.fillOpacity = fillOpacity;
            });
        }

        // Inicializálás: térkép renderelés utáni késleltetéssel
        window.addEventListener('load', function() {
            setTimeout(function() { setCountyOpacity(30); }, 800);
        });
        </script>
        """

        m.get_root().html.add_child(folium.Element(opacity_control_html))

        m.save(OUTPUT_FILE)
        print(f"\nSiker: {count} esemény + vármegyeréteg -> {OUTPUT_FILE}")
        print(f"Nyisd meg böngészőben: {OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"Hálózati hiba: {e}")
    except ET.ParseError as e:
        print(f"XML parse hiba: {e}")
    except Exception as e:
        print(f"Hiba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_map()

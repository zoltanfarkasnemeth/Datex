import requests
import xml.etree.ElementTree as ET
import folium
from datetime import datetime

URLS = [
    "https://napphub.kozut.hu/hub-web//datex2/3_3/4a8b2505-df5e-4191-8c96-b98263a771b5/pullSnapshotData",
    "https://napphub.kozut.hu/hub-web//datex2/3_3/c5a43ed1-8b33-4907-be59-1e6dd1cd5f92/pullSnapshotData",
]
OUTPUT_FILE = "index.html"
COUNTIES_GEOJSON_URL = "https://raw.githubusercontent.com/zoltanfarkasnemeth/Datex/main/megyek.geojson"

NS = {
    'ns19': 'http://datex2.eu/schema/3/situation',
    'ns11': 'http://datex2.eu/schema/3/locationReferencing',
    'ns24': 'http://datex2.eu/schema/3/common',
    'xsi':  'http://www.w3.org/2001/XMLSchema-instance'
}

# -----------------------------------------------------------------------
# Részletes SVG piktogramok – Utinform-szerű stílus
# Minden bejegyzés: (svg_body, popup_szín, magyar_cimke)
# -----------------------------------------------------------------------
SVG_ICONS = {
    'Accident': (
        '<circle cx="20" cy="20" r="19" fill="#C0392B"/>'
        '<circle cx="20" cy="20" r="15.5" fill="none" stroke="white" stroke-width="1.2" opacity="0.5"/>'
        '<rect x="4" y="18" width="12" height="7" rx="2" fill="white"/>'
        '<rect x="5.5" y="15.5" width="8" height="3.5" rx="1" fill="white"/>'
        '<circle cx="6.5" cy="25.5" r="2" fill="#C0392B"/>'
        '<circle cx="14" cy="25.5" r="2" fill="#C0392B"/>'
        '<rect x="24" y="18" width="12" height="7" rx="2" fill="white"/>'
        '<rect x="26.5" y="15.5" width="8" height="3.5" rx="1" fill="white"/>'
        '<circle cx="26" cy="25.5" r="2" fill="#C0392B"/>'
        '<circle cx="33.5" cy="25.5" r="2" fill="#C0392B"/>'
        '<polygon points="20,10 21.5,15 26.5,15 22.5,18 24,23 20,20.5 16,23 17.5,18 13.5,15 18.5,15" fill="#FFD700"/>',
        '#C0392B', 'Baleset'
    ),
    'MaintenanceWorks': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#E67E22"/>'
        '<clipPath id="wc"><rect x="1" y="1" width="38" height="38" rx="7"/></clipPath>'
        '<g clip-path="url(#wc)" fill="black" opacity="0.15">'
        '<polygon points="-4,40 4,40 40,4 40,-4 32,-4"/>'
        '<polygon points="10,40 18,40 40,18 40,10"/>'
        '<polygon points="24,40 32,40 40,32 40,24"/></g>'
        '<path d="M13 28 L22 19 Q24 15 28 14 Q29 17 27 19 L26 20 L28 22 L27 23 Q24 26 20 24 L11 33 Q9.5 34.5 8.5 33.5 Q7.5 32.5 9 31 Z" fill="white"/>'
        '<ellipse cx="26" cy="10" rx="7" ry="5" fill="#FFD700"/>'
        '<rect x="19" y="13" width="14" height="2.5" rx="1.2" fill="#FFD700"/>',
        '#E67E22', 'Karbantartás'
    ),
    'ConstructionWorks': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#D35400"/>'
        '<clipPath id="cc"><rect x="1" y="1" width="38" height="38" rx="7"/></clipPath>'
        '<g clip-path="url(#cc)" fill="black" opacity="0.15">'
        '<polygon points="-4,40 4,40 40,4 40,-4 32,-4"/>'
        '<polygon points="10,40 18,40 40,18 40,10"/>'
        '<polygon points="24,40 32,40 40,32 40,24"/></g>'
        '<rect x="5" y="22" width="18" height="12" rx="3" fill="white"/>'
        '<rect x="7" y="16" width="10" height="8" rx="2" fill="white"/>'
        '<rect x="5" y="32" width="18" height="3" rx="1.5" fill="#BDC3C7"/>'
        '<circle cx="7" cy="33.5" r="2" fill="#BDC3C7"/>'
        '<circle cx="21" cy="33.5" r="2" fill="#BDC3C7"/>'
        '<line x1="23" y1="20" x2="32" y2="11" stroke="white" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="32" y1="11" x2="36" y2="16" stroke="white" stroke-width="2.5" stroke-linecap="round"/>'
        '<path d="M34 15 Q38 17 37 21 L32 19 Z" fill="white"/>',
        '#D35400', 'Útépítés'
    ),
    'RoadOrCarriagewayOrLaneManagement': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#E74C3C"/>'
        '<rect x="5" y="24" width="30" height="8" rx="3" fill="white"/>'
        '<clipPath id="bc"><rect x="5" y="24" width="30" height="8" rx="3"/></clipPath>'
        '<g clip-path="url(#bc)">'
        '<rect x="5" y="24" width="6" height="8" fill="#E74C3C"/>'
        '<rect x="17" y="24" width="6" height="8" fill="#E74C3C"/>'
        '<rect x="29" y="24" width="6" height="8" fill="#E74C3C"/></g>'
        '<rect x="10" y="31" width="3" height="6" rx="1.5" fill="white"/>'
        '<rect x="27" y="31" width="3" height="6" rx="1.5" fill="white"/>'
        '<circle cx="20" cy="13" r="9" fill="none" stroke="white" stroke-width="3"/>'
        '<line x1="13.5" y1="13" x2="26.5" y2="13" stroke="white" stroke-width="3" stroke-linecap="round"/>',
        '#E74C3C', 'Útlezárás / sávlezárás'
    ),
    'AbnormalTraffic': (
        '<circle cx="20" cy="20" r="19" fill="#7D3C98"/>'
        '<rect x="4" y="19" width="9" height="6" rx="1.5" fill="white"/>'
        '<rect x="5" y="17" width="6" height="3" rx="1" fill="white"/>'
        '<circle cx="5.5" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<circle cx="11.5" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<rect x="15.5" y="19" width="9" height="6" rx="1.5" fill="white"/>'
        '<rect x="16.5" y="17" width="6" height="3" rx="1" fill="white"/>'
        '<circle cx="17" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<circle cx="23" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<rect x="27" y="19" width="9" height="6" rx="1.5" fill="white"/>'
        '<rect x="28" y="17" width="6" height="3" rx="1" fill="white"/>'
        '<circle cx="28.5" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<circle cx="34.5" cy="25.5" r="1.8" fill="#7D3C98"/>'
        '<path d="M9 28.5 L9 31 L7 31 L9 34 L11 31 L9 31" fill="#FFD700"/>'
        '<path d="M20 28.5 L20 31 L18 31 L20 34 L22 31 L20 31" fill="#FFD700"/>'
        '<path d="M31 28.5 L31 31 L29 31 L31 34 L33 31 L31 31" fill="#FFD700"/>',
        '#7D3C98', 'Rendellenes forgalom'
    ),
    'Congestion': (
        '<circle cx="20" cy="20" r="19" fill="#6C3483"/>'
        '<rect x="3" y="17" width="10" height="6.5" rx="1.8" fill="white"/>'
        '<rect x="4" y="14.5" width="7" height="3" rx="1" fill="white"/>'
        '<circle cx="5" cy="24" r="2" fill="#6C3483"/>'
        '<circle cx="11" cy="24" r="2" fill="#6C3483"/>'
        '<rect x="15" y="17" width="10" height="6.5" rx="1.8" fill="white"/>'
        '<rect x="16" y="14.5" width="7" height="3" rx="1" fill="white"/>'
        '<circle cx="17" cy="24" r="2" fill="#6C3483"/>'
        '<circle cx="23" cy="24" r="2" fill="#6C3483"/>'
        '<rect x="27" y="17" width="10" height="6.5" rx="1.8" fill="white"/>'
        '<rect x="28" y="14.5" width="7" height="3" rx="1" fill="white"/>'
        '<circle cx="29" cy="24" r="2" fill="#6C3483"/>'
        '<circle cx="35" cy="24" r="2" fill="#6C3483"/>'
        '<rect x="5" y="27" width="30" height="3.5" rx="1.7" fill="#E74C3C" opacity="0.85"/>',
        '#6C3483', 'Torlódás'
    ),
    'Obstruction': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#2C3E50"/>'
        '<polygon points="20,5 36,34 4,34" fill="#E74C3C"/>'
        '<polygon points="20,8 33.5,33 6.5,33" fill="#2C3E50"/>'
        '<rect x="18.8" y="13" width="2.4" height="11" rx="1.2" fill="white"/>'
        '<circle cx="20" cy="28" r="1.5" fill="white"/>',
        '#2C3E50', 'Akadály'
    ),
    'VehicleObstruction': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#34495E"/>'
        '<rect x="3" y="16" width="22" height="13" rx="2.5" fill="#BDC3C7"/>'
        '<rect x="3" y="12" width="13" height="5.5" rx="1.5" fill="#BDC3C7"/>'
        '<rect x="25" y="19" width="12" height="10" rx="2" fill="#95A5A6"/>'
        '<rect x="25.5" y="19.5" width="11" height="6" rx="1.5" fill="#AEC6CF"/>'
        '<circle cx="9" cy="29.5" r="3.2" fill="#2C3E50"/>'
        '<circle cx="9" cy="29.5" r="1.5" fill="#7F8C8D"/>'
        '<circle cx="21" cy="29.5" r="3.2" fill="#2C3E50"/>'
        '<circle cx="21" cy="29.5" r="1.5" fill="#7F8C8D"/>'
        '<circle cx="32" cy="29.5" r="3.2" fill="#2C3E50"/>'
        '<circle cx="32" cy="29.5" r="1.5" fill="#7F8C8D"/>'
        '<polygon points="33,6 39,17 27,17" fill="#E74C3C"/>'
        '<polygon points="33,8 37.5,16.5 28.5,16.5" fill="#34495E"/>'
        '<rect x="32.3" y="10.5" width="1.4" height="4" rx="0.7" fill="white"/>'
        '<circle cx="33" cy="15.5" r="0.8" fill="white"/>',
        '#34495E', 'Leállt jármű'
    ),
    'AnimalPresenceObstruction': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#1E8449"/>'
        '<ellipse cx="20" cy="28" rx="9" ry="6" fill="white"/>'
        '<rect x="17.5" y="16" width="5" height="10" rx="2.5" fill="white"/>'
        '<ellipse cx="20" cy="15" rx="4" ry="3.5" fill="white"/>'
        '<rect x="12" y="32" width="2.8" height="6.5" rx="1.4" fill="white"/>'
        '<rect x="16.5" y="33" width="2.8" height="6.5" rx="1.4" fill="white"/>'
        '<rect x="21" y="33" width="2.8" height="6.5" rx="1.4" fill="white"/>'
        '<rect x="25.5" y="32" width="2.8" height="6.5" rx="1.4" fill="white"/>'
        '<circle cx="22" cy="14.5" r="1" fill="#1E8449"/>'
        '<path d="M18 13.5 L15 7 M15 7 L12 5 M15 7 L15.5 4.5 M15 7 L17 5" stroke="white" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        '<path d="M22 13.5 L25 7 M25 7 L28 5 M25 7 L24.5 4.5 M25 7 L23 5" stroke="white" stroke-width="1.6" fill="none" stroke-linecap="round"/>',
        '#1E8449', 'Állat az úton'
    ),
    'WeatherRelatedRoadConditions': (
        '<circle cx="20" cy="20" r="19" fill="#1565C0"/>'
        '<line x1="20" y1="8" x2="20" y2="32" stroke="white" stroke-width="2.2" stroke-linecap="round"/>'
        '<line x1="8" y1="20" x2="32" y2="20" stroke="white" stroke-width="2.2" stroke-linecap="round"/>'
        '<line x1="11.5" y1="11.5" x2="28.5" y2="28.5" stroke="white" stroke-width="2.2" stroke-linecap="round"/>'
        '<line x1="28.5" y1="11.5" x2="11.5" y2="28.5" stroke="white" stroke-width="2.2" stroke-linecap="round"/>'
        '<line x1="20" y1="11" x2="17" y2="8" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="20" y1="11" x2="23" y2="8" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="20" y1="29" x2="17" y2="32" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="20" y1="29" x2="23" y2="32" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="11" y1="20" x2="8" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="11" y1="20" x2="8" y2="23" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="29" y1="20" x2="32" y2="17" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<line x1="29" y1="20" x2="32" y2="23" stroke="white" stroke-width="1.4" stroke-linecap="round"/>'
        '<circle cx="20" cy="20" r="3" fill="white"/>',
        '#1565C0', 'Időjárási útviszonyok'
    ),
    'EnvironmentalObstruction': (
        '<circle cx="20" cy="20" r="19" fill="#546E7A"/>'
        '<ellipse cx="18" cy="19" rx="9" ry="6" fill="white" opacity="0.95"/>'
        '<ellipse cx="26" cy="21" rx="7" ry="5" fill="white" opacity="0.95"/>'
        '<ellipse cx="14" cy="22" rx="6" ry="4" fill="white" opacity="0.95"/>'
        '<ellipse cx="20" cy="14" rx="5" ry="4.5" fill="white" opacity="0.95"/>'
        '<line x1="9" y1="27" x2="17" y2="27" stroke="#546E7A" stroke-width="2" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="20" y1="27" x2="31" y2="27" stroke="#546E7A" stroke-width="2" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="9" y1="31" x2="22" y2="31" stroke="#546E7A" stroke-width="2" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="25" y1="31" x2="31" y2="31" stroke="#546E7A" stroke-width="2" stroke-linecap="round" opacity="0.7"/>',
        '#546E7A', 'Köd / láthatóság'
    ),
    'Conditions': (
        '<circle cx="20" cy="20" r="19" fill="#0277BD"/>'
        '<ellipse cx="18" cy="16" rx="8" ry="6" fill="white"/>'
        '<ellipse cx="26" cy="18" rx="6" ry="5" fill="white"/>'
        '<ellipse cx="13" cy="19" rx="5" ry="4" fill="white"/>'
        '<ellipse cx="20" cy="11" rx="4.5" ry="4" fill="white"/>'
        '<ellipse cx="12" cy="27" rx="1.5" ry="2.5" transform="rotate(-15 12 27)" fill="#AED6F1"/>'
        '<ellipse cx="18" cy="29" rx="1.5" ry="2.5" transform="rotate(-15 18 29)" fill="#AED6F1"/>'
        '<ellipse cx="24" cy="27" rx="1.5" ry="2.5" transform="rotate(-15 24 27)" fill="#AED6F1"/>'
        '<ellipse cx="30" cy="29" rx="1.5" ry="2.5" transform="rotate(-15 30 29)" fill="#AED6F1"/>'
        '<ellipse cx="15" cy="33" rx="1.5" ry="2.5" transform="rotate(-15 15 33)" fill="#AED6F1"/>'
        '<ellipse cx="27" cy="33" rx="1.5" ry="2.5" transform="rotate(-15 27 33)" fill="#AED6F1"/>',
        '#0277BD', 'Csapadék / útviszonyok'
    ),
    'PoorRoadInfrastructure': (
        '<rect x="1" y="1" width="38" height="38" rx="7" fill="#6D4C41"/>'
        '<rect x="4" y="24" width="32" height="12" rx="3" fill="#546E7A"/>'
        '<path d="M10 24 L14 28 L11 32 M14 28 L17 25 M17 25 L20 29 L24 26 M20 29 L18 33" stroke="#263238" stroke-width="1.5" fill="none" stroke-linecap="round"/>'
        '<ellipse cx="23" cy="30" rx="4.5" ry="3" fill="#37474F"/>'
        '<rect x="14" y="4" width="12" height="16" rx="2" fill="#FFC107"/>'
        '<polygon points="20,6 26,17.5 14,17.5" fill="#E65100"/>'
        '<polygon points="20,7.8 25,17" fill="#FFC107"/>'
        '<rect x="19.3" y="10" width="1.4" height="5" rx="0.7" fill="#E65100"/>'
        '<circle cx="20" cy="16" r="0.9" fill="#E65100"/>',
        '#6D4C41', 'Úthibák / burkolat'
    ),
    'GeneralInstructionOrMessageToRoadUsers': (
        '<circle cx="20" cy="20" r="19" fill="#0D47A1"/>'
        '<circle cx="20" cy="20" r="15.5" fill="none" stroke="white" stroke-width="1" opacity="0.35"/>'
        '<circle cx="20" cy="12" r="2.8" fill="white"/>'
        '<rect x="17.2" y="17" width="5.6" height="13" rx="2.8" fill="white"/>'
        '<rect x="14.5" y="29" width="11" height="2.5" rx="1.2" fill="white"/>',
        '#0D47A1', 'Tájékoztatás'
    ),
    'PublicEvent': (
        '<circle cx="20" cy="20" r="19" fill="#00838F"/>'
        '<rect x="7" y="29" width="26" height="5" rx="2.5" fill="white"/>'
        '<rect x="11" y="25" width="18" height="5.5" rx="2" fill="white" opacity="0.85"/>'
        '<circle cx="20" cy="16" r="4" fill="white"/>'
        '<path d="M14 25 Q14 21 20 21 Q26 21 26 25" fill="white"/>'
        '<line x1="5" y1="14" x2="3" y2="11" stroke="white" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="5" y1="18" x2="2.5" y2="18" stroke="white" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="35" y1="14" x2="37" y2="11" stroke="white" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="35" y1="18" x2="37.5" y2="18" stroke="white" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>'
        '<line x1="20" y1="6" x2="20" y2="3" stroke="white" stroke-width="1.4" stroke-linecap="round" opacity="0.7"/>',
        '#00838F', 'Rendezvény'
    ),
    'Delays': (
        '<circle cx="20" cy="20" r="19" fill="#AD1457"/>'
        '<circle cx="20" cy="20" r="12" fill="white"/>'
        '<line x1="20" y1="10" x2="20" y2="11.5" stroke="#AD1457" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>'
        '<line x1="20" y1="28.5" x2="20" y2="30" stroke="#AD1457" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>'
        '<line x1="10" y1="20" x2="11.5" y2="20" stroke="#AD1457" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>'
        '<line x1="28.5" y1="20" x2="30" y2="20" stroke="#AD1457" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>'
        '<line x1="20" y1="20" x2="20" y2="12.5" stroke="#AD1457" stroke-width="2.2" stroke-linecap="round"/>'
        '<line x1="20" y1="20" x2="26" y2="23.5" stroke="#AD1457" stroke-width="1.8" stroke-linecap="round"/>'
        '<circle cx="20" cy="20" r="1.8" fill="#AD1457"/>'
        '<circle cx="31" cy="9" r="5.5" fill="#E53935"/>'
        '<rect x="29.8" y="5.5" width="2.4" height="5" rx="1.2" fill="white"/>'
        '<circle cx="31" cy="12.5" r="1.2" fill="white"/>',
        '#AD1457', 'Késés'
    ),
    '_default': (
        '<circle cx="20" cy="20" r="19" fill="#546E7A"/>'
        '<path d="M20 8 C13.4 8 8 13.4 8 20 C8 28 20 36 20 36 C20 36 32 28 32 20 C32 13.4 26.6 8 20 8 Z" fill="white" opacity="0.9"/>'
        '<circle cx="20" cy="19" r="5" fill="#546E7A"/>',
        '#546E7A', 'Esemény'
    ),
}

TYPE_ALIASES = {
    'accident':           'Accident',
    'collision':          'Accident',
    'maintenanceworks':   'MaintenanceWorks',
    'constructionworks':  'ConstructionWorks',
    'roadOrCarriageway':  'RoadOrCarriagewayOrLaneManagement',
    'lanemanagement':     'RoadOrCarriagewayOrLaneManagement',
    'abnormaltraffic':    'AbnormalTraffic',
    'trafficconstriction':'AbnormalTraffic',
    'congestion':         'Congestion',
    'trafficheadway':     'Congestion',
    'vehicleobstruction': 'VehicleObstruction',
    'obstruction':        'Obstruction',
    'animalpresence':     'AnimalPresenceObstruction',
    'weatherrelated':     'WeatherRelatedRoadConditions',
    'environmental':      'EnvironmentalObstruction',
    'conditions':         'Conditions',
    'poorroadinfra':      'PoorRoadInfrastructure',
    'generalinstruction': 'GeneralInstructionOrMessageToRoadUsers',
    'publicevent':        'PublicEvent',
    'delays':             'Delays',
    'delay':              'Delays',
}


def get_category(xsi_type: str):
    type_name = xsi_type.split(':')[-1] if xsi_type else ''
    if type_name in SVG_ICONS:
        return type_name, SVG_ICONS[type_name]
    lower = type_name.lower()
    for alias, key in TYPE_ALIASES.items():
        if alias.lower() in lower:
            return key, SVG_ICONS[key]
    return '_default', SVG_ICONS['_default']


def make_div_icon(svg_body: str, size: int = 40) -> folium.DivIcon:
    html = (
        f'<div style="width:{size}px;height:{size}px;'
        f'filter:drop-shadow(0 2px 4px rgba(0,0,0,0.5));">'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
        f'width="{size}" height="{size}">{svg_body}</svg></div>'
    )
    return folium.DivIcon(
        html=html,
        icon_size=(size, size),
        icon_anchor=(size // 2, size // 2),
        popup_anchor=(0, -size // 2 - 4),
    )


def build_legend_html(used_categories: set) -> str:
    rows = ""
    for key in sorted(used_categories):
        svg_body, color, label = SVG_ICONS.get(key, SVG_ICONS['_default'])
        rows += (
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
            f'<div style="width:28px;height:28px;flex-shrink:0;filter:drop-shadow(0 1px 2px rgba(0,0,0,0.3));">'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="28" height="28">'
            f'{svg_body}</svg></div>'
            f'<span style="font-size:11px;color:#222;">{label}</span></div>'
        )
    return (
        '<div id="legend-box" style="position:fixed;bottom:30px;right:10px;z-index:9999;'
        'background:white;padding:12px 14px;border-radius:10px;'
        'box-shadow:0 2px 14px rgba(0,0,0,0.22);'
        'font-family:\'Helvetica Neue\',Arial,sans-serif;border:1px solid #ddd;max-width:200px;">'
        '<div style="font-weight:bold;margin-bottom:9px;color:#1a3a5c;font-size:13px;'
        'border-bottom:1px solid #e0e0e0;padding-bottom:6px;">Jelmagyarázat</div>'
        f'{rows}</div>'
    )


def fetch_counties_geojson():
    try:
        r = requests.get(COUNTIES_GEOJSON_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        print(f"  GeoJSON OK: {len(data.get('features', []))} feature")
        return data
    except Exception as e:
        print(f"  HIBA GeoJSON: {e}")
        return None


def fetch_situation_records(url: str):
    """Egy DATEX II snapshot letöltése és a situationRecord elemek visszaadása."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        records = root.findall('.//ns19:situationRecord', NS)
        print(f"  {url.split('/')[-2][:8]}...: {len(records)} rekord")
        return records
    except requests.exceptions.RequestException as e:
        print(f"  Hálózati hiba ({url}): {e}")
    except ET.ParseError as e:
        print(f"  XML parse hiba ({url}): {e}")
    return []


def update_map():
    print(f"Lekérdezés: {datetime.now()}")
    try:
        # --- Összes forrás beolvasása, duplikátumszűréssel ---
        print("Adatforrások letöltése...")
        all_records = []
        seen_ids = set()
        for url in URLS:
            for rec in fetch_situation_records(url):
                rec_id = rec.get('id')
                if rec_id:
                    if rec_id in seen_ids:
                        continue
                    seen_ids.add(rec_id)
                all_records.append(rec)

        if not all_records:
            print("Nincs feldolgozható esemény, kilépés.")
            return

        print(f"Összesen {len(all_records)} egyedi rekord.")

        m = folium.Map(location=[47.1625, 19.5033], zoom_start=8)
        m.get_root().header.add_child(
            folium.Element('<meta http-equiv="refresh" content="300">')
        )

        # --- Vármegyék réteg ---
        print("Vármegyék betöltése...")
        counties_data = fetch_counties_geojson()
        counties_layer = folium.FeatureGroup(name="Magyar vármegyék", show=True)
        if counties_data:
            sample_props = counties_data.get('features', [{}])[0].get('properties', {})
            name_key = next(
                (k for k in ['name','NAME','Name','megye','MEGYE','vm_nev','NAME_1','label','COUNTY','county']
                 if k in sample_props), None)
            folium.GeoJson(
                counties_data,
                style_function=lambda f: {
                    'fillColor': '#4A90D9', 'color': '#1a5276',
                    'weight': 2, 'fillOpacity': 0.3, 'opacity': 1.0
                },
                highlight_function=lambda f: {
                    'fillColor': '#2E6DA4', 'weight': 3, 'fillOpacity': 0.5
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=[name_key], aliases=['Vármegye:'],
                    localize=True, sticky=True
                ) if name_key else None
            ).add_to(counties_layer)
        counties_layer.add_to(m)

        # --- Esemény rétegek ---
        used_categories = set()
        event_layers = {}
        count = 0

        NS_LOC = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common',
        }

        for record in all_records:
            xsi_type = record.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
            cat_key, (svg_body, popup_color, label) = get_category(xsi_type)

            lat = record.find('.//ns11:latitude', NS_LOC)
            lon = record.find('.//ns11:longitude', NS_LOC)
            road = record.find('.//ns11:roadNumber', NS_LOC)
            vals = record.findall('.//ns24:value', NS_LOC)
            desc = next((v.text for v in vals if v.text), "Nincs leírás")

            if lat is None or lon is None:
                continue

            used_categories.add(cat_key)
            if cat_key not in event_layers:
                event_layers[cat_key] = folium.FeatureGroup(
                    name=label, show=True
                )

            road_text = road.text if road is not None else '?'
            popup_html = (
                '<div style="font-family:\'Helvetica Neue\',Arial,sans-serif;'
                'min-width:210px;border-radius:8px;overflow:hidden;">'
                f'<div style="background:{popup_color};color:white;padding:7px 12px;'
                'font-weight:bold;font-size:13px;display:flex;align-items:center;gap:8px;">'
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="22" height="22" '
                f'style="flex-shrink:0">{svg_body}</svg>{label}</div>'
                f'<div style="padding:9px 12px;font-size:12px;color:#333;line-height:1.5;">'
                f'<b>Út:</b> {road_text}<br>'
                f'<span style="margin-top:4px;display:block;color:#555;">{desc[:200]}</span>'
                '</div></div>'
            )

            folium.Marker(
                location=[float(lat.text), float(lon.text)],
                popup=folium.Popup(popup_html, max_width=310),
                tooltip=f"{label} – {road_text}",
                icon=make_div_icon(svg_body, size=38)
            ).add_to(event_layers[cat_key])
            count += 1

        for layer in event_layers.values():
            layer.add_to(m)

        # --- Rétegvezérlő ---
        folium.LayerControl(position='topleft', collapsed=False).add_to(m)

        # --- Átlátszóság csúszka ---
        opacity_html = (
            '<div id="county-opacity-box" style="position:fixed;top:140px;left:10px;z-index:9999;'
            'background:white;padding:10px 14px 12px;border-radius:8px;'
            'box-shadow:0 2px 10px rgba(0,0,0,0.25);'
            'font-family:\'Helvetica Neue\',Arial,sans-serif;font-size:12px;'
            'min-width:200px;border:1px solid #ccc;">'
            '<div style="font-weight:bold;margin-bottom:8px;color:#1a5276;font-size:13px;">'
            'Vármegyék átlátszósága</div>'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<input type="range" id="cOp" min="0" max="100" value="30" step="5" '
            'style="flex:1;accent-color:#1a5276;cursor:pointer;" oninput="setOp(this.value)">'
            '<span id="cOpLabel" style="min-width:38px;text-align:right;'
            'color:#333;font-weight:bold;font-size:13px;">30%</span></div>'
            '<div style="margin-top:5px;font-size:10px;color:#999;">'
            '0% = átlátszó &nbsp;|&nbsp; 100% = teli</div></div>'
            '<script>'
            'function setOp(val){'
            'document.getElementById("cOpLabel").textContent=parseInt(val)+"%";'
            'var op=parseInt(val)/100;'
            'document.querySelectorAll(".leaflet-overlay-pane path.leaflet-interactive")'
            '.forEach(function(p){if(!p.hasAttribute("r"))p.style.fillOpacity=op;});}'
            'window.addEventListener("load",function(){setTimeout(function(){setOp(30);},800);});'
            '</script>'
        )
        m.get_root().html.add_child(folium.Element(opacity_html))

        # --- Jelmagyarázat ---
        m.get_root().html.add_child(folium.Element(build_legend_html(used_categories)))

        m.save(OUTPUT_FILE)
        print(f"\nSiker: {count} esemény, {len(used_categories)} kategória -> {OUTPUT_FILE}")

    except Exception as e:
        print(f"Hiba: {e}")
        import traceback; traceback.print_exc()


if __name__ == "__main__":
    update_map()

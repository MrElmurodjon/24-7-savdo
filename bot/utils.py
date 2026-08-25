import logging
from thefuzz import process, fuzz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

logger = logging.getLogger(__name__)

# Predefined standard products for matching
STANDARD_PRODUCTS = [
    "olma", "gilos", "o'rik", "nok", "shaftoli", "uzum", "anjir", "anor", 
    "olxo'ri", "behi", "yong'oq", "bodom", "xurmo", "qulupnay", "tarvuz", "qovun",
    "pomidor", "bodring", "piyoz", "kartoshka", "sabzi", "karam", "sarimsoq",
    "terak", "qora terak", "gullar", "atirgul", "archa", "limon", "apelsin", "mandarin"
]

def cyrillic_to_latin(text):
    mapping = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z',
        'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
        'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': "'", 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya', 'Ў': "O'", 'Қ': 'Q', 'Ғ': "G'", 'Ҳ': 'H',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': "'", 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h'
    }
    for cyr, lat in mapping.items():
        text = text.replace(cyr, lat)
    return text

def standardize_product_name(input_name, threshold=60):
    """
    Kiritilgan nomni standartlashtiradi (Fuzzy matching).
    Krillchani lotinchaga o'girib keyin tekshiradi.
    """
    if not input_name:
        return ""
    
    # Krillchani lotinchaga o'tkazish
    latin_name = cyrillic_to_latin(input_name)
    input_lower = latin_name.lower().strip()
    
    # 'x' va 'h' xatolarini ham kamaytirish uchun qisqa almashtirish
    input_lower_normalized = input_lower.replace('x', 'h')
    
    best_match = None
    best_score = 0
    
    for prod in STANDARD_PRODUCTS:
        prod_norm = prod.lower().replace('x', 'h')
        score = fuzz.token_sort_ratio(input_lower_normalized, prod_norm)
        if score > best_score:
            best_score = score
            best_match = prod
            
    if best_match and best_score >= threshold:
        return best_match.capitalize()
    
    return latin_name.capitalize()

def reverse_geocode(lat, lon):
    """
    Koordinatalardan Viloyat va Tuman nomini ajratib olish (OpenStreetMap API)
    """
    if not lat or not lon:
        return "", ""
        
    try:
        geolocator = Nominatim(user_agent="quvanihol_marketplace_bot_v1")
        # Tilni o'zbekcha so'raymiz
        location = geolocator.reverse((lat, lon), language='uz', timeout=5)
        
        if location and location.raw.get('address'):
            address = location.raw['address']
            
            # Viloyat (state)
            region = address.get('state', address.get('region', ''))
            
            # Tuman yoki shahar (county, city, town)
            district = address.get('county', address.get('city', address.get('town', address.get('village', ''))))
            
            # Viloyati/tumani so'zlarini tozalaymiz
            if region:
                region = region.replace("viloyati", "").replace("Viloyati", "").strip()
            
            if district:
                district = district.replace("tumani", "").replace("Tumani", "").strip()
            
            return region, district
            
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.error(f"Geocoding xatosi: {e}")
        
    return "", ""

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

def standardize_product_name(input_name, threshold=70):
    """
    Kiritilgan nomni standartlashtiradi (Fuzzy matching).
    Kiritilgan so'z STANDARD_PRODUCTS ichidagilardan biriga o'xshasa, o'shani qaytaradi.
    Agar o'xshashlik threshold dan past bo'lsa, asli qanday bo'lsa shunday qaytaradi.
    """
    if not input_name:
        return ""
    
    input_lower = input_name.lower().strip()
    
    # O'zbek lotin harflari uchun kichik normallashtirish (o' -> o, g' -> g) 
    # Bu thefuzz ishlashini yaxshilaydi, lekin TheFuzz o'zi ham eplaydi.
    
    best_match = process.extractOne(input_lower, STANDARD_PRODUCTS, scorer=fuzz.token_sort_ratio)
    
    if best_match and best_match[1] >= threshold:
        return best_match[0].capitalize()
    
    return input_name.capitalize()

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

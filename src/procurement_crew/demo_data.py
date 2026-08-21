"""Bundled realistic demo data.

Lets the entire crew (search -> scrape -> compare -> report) run end-to-end
with zero external API keys, so the pipeline can be smoke-tested and
demoed reliably. Set DEMO_MODE=true (see .env.example) to activate.
"""

DEMO_SEARCH_RESULTS = [
    {"product_name": "Dell Latitude 5450", "vendor": "dell.com", "url": "https://dell.com/latitude-5450"},
    {"product_name": "Lenovo ThinkPad T14 Gen 5", "vendor": "lenovo.com", "url": "https://lenovo.com/thinkpad-t14-g5"},
    {"product_name": "HP EliteBook 640 G11", "vendor": "hp.com", "url": "https://hp.com/elitebook-640-g11"},
    {"product_name": "ASUS ExpertBook B5", "vendor": "asus.com", "url": "https://asus.com/expertbook-b5"},
    {"product_name": "Acer TravelMate P4", "vendor": "acer.com", "url": "https://acer.com/travelmate-p4"},
    {"product_name": "Microsoft Surface Laptop 6", "vendor": "microsoft.com", "url": "https://microsoft.com/surface-laptop-6"},
    {"product_name": "Dell Latitude 5350 (budget)", "vendor": "bestbuy.com", "url": "https://bestbuy.com/dell-latitude-5350"},
    {"product_name": "Lenovo V15 G4 (budget)", "vendor": "newegg.com", "url": "https://newegg.com/lenovo-v15-g4"},
]

DEMO_PRODUCT_RECORDS = {
    "https://dell.com/latitude-5450": {
        "price_usd": 1149,
        "specs": {
            "ram_gb": 16, "storage_gb": 512, "storage_type": "SSD",
            "cpu": "Intel Core Ultra 5 125U", "battery_life_hours": 10,
            "screen_size_inches": 14, "weight_kg": 1.55,
            "backlit_keyboard": True, "fingerprint_reader": True,
        },
        "seller_rating": 4.5, "warranty_months": 36,
    },
    "https://lenovo.com/thinkpad-t14-g5": {
        "price_usd": 1299,
        "specs": {
            "ram_gb": 32, "storage_gb": 1024, "storage_type": "SSD",
            "cpu": "AMD Ryzen 7 PRO 8840U", "battery_life_hours": 12,
            "screen_size_inches": 14, "weight_kg": 1.36,
            "backlit_keyboard": True, "fingerprint_reader": True,
        },
        "seller_rating": 4.7, "warranty_months": 36,
    },
    "https://hp.com/elitebook-640-g11": {
        "price_usd": 1099,
        "specs": {
            "ram_gb": 16, "storage_gb": 512, "storage_type": "SSD",
            "cpu": "Intel Core Ultra 5 125U", "battery_life_hours": 9,
            "screen_size_inches": 14, "weight_kg": 1.5,
            "backlit_keyboard": True, "fingerprint_reader": False,
        },
        "seller_rating": 4.3, "warranty_months": 12,
    },
    "https://asus.com/expertbook-b5": {
        "price_usd": 1049,
        "specs": {
            "ram_gb": 16, "storage_gb": 512, "storage_type": "SSD",
            "cpu": "Intel Core i5-1340P", "battery_life_hours": 8,
            "screen_size_inches": 14, "weight_kg": 1.38,
            "backlit_keyboard": True, "fingerprint_reader": True,
        },
        "seller_rating": 4.2, "warranty_months": 24,
    },
    "https://acer.com/travelmate-p4": {
        "price_usd": 899,
        "specs": {
            "ram_gb": 16, "storage_gb": 512, "storage_type": "SSD",
            "cpu": "Intel Core i5-1335U", "battery_life_hours": 9,
            "screen_size_inches": 14, "weight_kg": 1.4,
            "backlit_keyboard": False, "fingerprint_reader": True,
        },
        "seller_rating": 4.0, "warranty_months": 12,
    },
    "https://microsoft.com/surface-laptop-6": {
        "price_usd": 1399,
        "specs": {
            "ram_gb": 16, "storage_gb": 512, "storage_type": "SSD",
            "cpu": "Intel Core Ultra 7 165H", "battery_life_hours": 19,
            "screen_size_inches": 13.8, "weight_kg": 1.34,
            "backlit_keyboard": True, "fingerprint_reader": True,
        },
        "seller_rating": 4.6, "warranty_months": 12,
    },
    "https://bestbuy.com/dell-latitude-5350": {
        "price_usd": 799,
        "specs": {
            "ram_gb": 8, "storage_gb": 256, "storage_type": "SSD",
            "cpu": "Intel Core i5-1335U", "battery_life_hours": 7,
            "screen_size_inches": 13.3, "weight_kg": 1.4,
            "backlit_keyboard": False, "fingerprint_reader": False,
        },
        "seller_rating": 4.1, "warranty_months": 12,
    },
    "https://newegg.com/lenovo-v15-g4": {
        "price_usd": 649,
        "specs": {
            "ram_gb": 8, "storage_gb": 256, "storage_type": "SSD",
            "cpu": "AMD Ryzen 5 7430U", "battery_life_hours": 6,
            "screen_size_inches": 15.6, "weight_kg": 1.7,
            "backlit_keyboard": False, "fingerprint_reader": False,
        },
        "seller_rating": 3.8, "warranty_months": 12,
    },
}

# स्कैम/हैक/मिक्सर एड्रेस का डेटाबेस
# नोट: यह जानी-मानी एड्रेस का छोटा सैंपल है। असली टूल में 1000+ एड्रेस होंगे।

SCAM_DATABASE = {
    # हैक/स्कैम एड्रेस
    "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF": {
        "tag": "Bitfinex Hack 2016",
        "type": "hack",
        "amount_lost": "72,000 BTC",
        "reference": "https://www.washingtonpost.com/news/the-switch/wp/2016/08/03/bitfinex-bitcoin-exchange-gets-hacked-60-million-disappears/"
    },
    "3Cbq7aT1tY8kMxWLbitaG7yT6bPbKChq64": {
        "tag": "MtGox Hack",
        "type": "hack",
        "amount_lost": "850,000 BTC",
        "reference": "https://en.wikipedia.org/wiki/Mt._Gox"
    },
    "bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6": {
        "tag": "Colonial Pipeline Ransomware 2021",
        "type": "ransomware",
        "amount_lost": "75 BTC",
        "reference": "https://www.bbc.com/news/technology-57088336"
    },
    
    # मिक्सर/टम्बलर एड्रेस (प्राइवेसी टूल्स, लेकिन सस्पीशियस माने जाते हैं)
    "1ETQJ4cMoSYxGLQDTLq9j7MKyC2q2jC2Fd": {
        "tag": "Known Mixing Service",
        "type": "mixer",
        "risk": "medium"
    },
    
    # स्कैम एड्रेस (फ़िशिंग, पोंजी स्कीम)
    "1MDUoxL1bGvMxhuoDYx6i11ePytECAk9QK": {
        "tag": "Fake Exchange Scam",
        "type": "scam",
        "description": "Fake Binance phishing address"
    },
    
    # टेस्टनेट/रिग्रेट एड्रेस
    "2N1W7qo1SqykbWyF9hTZkFJsQFQCdXbBgcQ": {
        "tag": "Testnet Address (Ignore)",
        "type": "testnet",
        "risk": "none"
    }
}

# एड्रेस चेक फंक्शन
def check_scam_database(address: str) -> dict:
    address_lower = address.strip()
    
    # डायरेक्ट मैच
    if address_lower in SCAM_DATABASE:
        return {
            "found": True,
            "match_type": "exact",
            "details": SCAM_DATABASE[address_lower]
        }
    
    # पार्शियल मैच (पहले 10 करैक्टर)
    for scam_addr in SCAM_DATABASE:
        if address_lower.startswith(scam_addr[:10]):
            return {
                "found": True,
                "match_type": "partial",
                "details": SCAM_DATABASE[scam_addr],
                "note": "Partial address match detected"
            }
    
    # नो मैच
    return {
        "found": False,
        "match_type": "none",
        "details": {}
    }

# डेटाबेस अपडेट करने का फंक्शन (बाद में यूज करेंगे)
def update_scam_database(new_entries: dict):
    SCAM_DATABASE.update(new_entries)
    # यहाँ आप फाइल में सेव भी कर सकते हैं
    return len(SCAM_DATABASE)

# डेटाबेस स्टेटस
def get_database_stats():
    counts = {"hack": 0, "scam": 0, "ransomware": 0, "mixer": 0, "testnet": 0}
    for entry in SCAM_DATABASE.values():
        if entry["type"] in counts:
            counts[entry["type"]] += 1
    
    return {
        "total_entries": len(SCAM_DATABASE),
        "by_type": counts,
        "last_updated": "2024-01-15"
    }
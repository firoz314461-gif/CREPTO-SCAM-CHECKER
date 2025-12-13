from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import sqlite3
import json
import time
from typing import Dict, Optional
from scam_database import SCAM_DATABASE, check_scam_database

app = FastAPI(title="Crypto Address Safety Checker")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# डेटाबेस सेटअप (कैशिंग के लिए)
def init_db():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS address_cache 
                 (address TEXT PRIMARY KEY, data TEXT, timestamp INTEGER)''')
    conn.commit()
    conn.close()

# ब्लॉकचेन API से डेटा फ़ेच करें
def fetch_blockchain_data(address: str):
    # Blockchair API (फ्री, 30 रिक्वेस्ट/मिनट)
    try:
        # बिटकॉइन के लिए
        response = requests.get(
            f"https://api.blockchair.com/bitcoin/dashboards/address/{address}",
            headers={"User-Agent": "CryptoScanner/1.0"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and address in data['data']:
                addr_data = data['data'][address]['address']
                
                result = {
                    "balance": addr_data.get('balance', 0),
                    "transaction_count": addr_data.get('transaction_count', 0),
                    "first_seen": addr_data.get('first_seen', ''),
                    "last_seen": addr_data.get('last_seen', ''),
                    "total_received": addr_data.get('received', 0),
                    "total_sent": addr_data.get('spent', 0),
                    "source": "blockchair"
                }
                
                # कैश में सेव करें
                conn = sqlite3.connect('cache.db')
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO address_cache VALUES (?, ?, ?)",
                         (address, json.dumps(result), int(time.time())))
                conn.commit()
                conn.close()
                
                return result
    except Exception as e:
        print(f"API Error: {e}")
    
    # फॉलबैक API
    try:
        response = requests.get(
            f"https://blockchain.info/rawaddr/{address}?limit=5",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "balance": data.get('final_balance', 0),
                "transaction_count": data.get('n_tx', 0),
                "total_received": data.get('total_received', 0),
                "total_sent": data.get('total_sent', 0),
                "source": "blockchain.info"
            }
    except:
        pass
    
    return None

# स्कोर कैलकुलेशन
def calculate_risk_score(address: str, blockchain_data: Optional[Dict]) -> Dict:
    score = 0
    warnings = []
    risk_level = "LOW"
    
    # 1. स्कैम डेटाबेस में चेक
    scam_result = check_scam_database(address)
    if scam_result["found"]:
        score += 80
        warnings.append(f"⚠️ {scam_result['tag']}")
    
    # 2. ब्लॉकचेन डेटा एनालिसिस
    if blockchain_data:
        tx_count = blockchain_data.get('transaction_count', 0)
        total_received = blockchain_data.get('total_received', 0)
        
        # अगर एड्रेस नया है (कम ट्रांजैक्शन) लेकिन बड़ी रकम आई है
        if tx_count < 10 and total_received > 100000000:  # > 1 BTC
            score += 30
            warnings.append("🚨 New address with large transactions")
        
        # अगर बैलेंस ज़ीरो है लेकिन बहुत ट्रांजैक्शन हैं (मिक्सर)
        if blockchain_data.get('balance', 0) == 0 and tx_count > 100:
            score += 20
            warnings.append("⚠️ High transaction count with zero balance")
    
    # 3. एड्रेस पैटर्न चेक (ऑप्शनल)
    if address.startswith("bc1q") and len(address) == 42:
        # SegWit एड्रेस - कोई रिस्क नहीं
        pass
    elif len(address) < 26:
        score += 10
        warnings.append("⚠️ Invalid address format")
    
    # रिस्क लेवल डिसाइड करो
    if score >= 70:
        risk_level = "CRITICAL"
        color = "red"
    elif score >= 40:
        risk_level = "HIGH"
        color = "orange"
    elif score >= 20:
        risk_level = "MEDIUM"
        color = "yellow"
    else:
        risk_level = "LOW"
        color = "green"
    
    return {
        "score": min(score, 100),
        "risk_level": risk_level,
        "color": color,
        "warnings": warnings,
        "suggestions": [
            "Verify address from multiple sources",
            "Check transaction history carefully",
            "Use small test transaction first" if score > 30 else "Address appears safe"
        ]
    }

# API एंडपॉइंट्स
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/check")
async def check_address(address: str = Form(...)):
    # बेसिक वैलिडेशन
    if not address or len(address) < 26:
        return JSONResponse({
            "error": "Invalid address format",
            "valid": False
        })
    
    # स्कैम डेटाबेस चेक
    scam_check = check_scam_database(address)
    
    # ब्लॉकचेन डेटा
    blockchain_data = fetch_blockchain_data(address)
    
    # रिस्क स्कोर
    risk_analysis = calculate_risk_score(address, blockchain_data)
    
    # फाइनल रिजल्ट
    result = {
        "address": address,
        "valid": True,
        "scam_check": scam_check,
        "blockchain_data": blockchain_data,
        "risk_analysis": risk_analysis,
        "timestamp": time.time()
    }
    
    return JSONResponse(result)

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM address_cache")
    count = c.fetchone()[0]
    conn.close()
    
    return {
        "cached_addresses": count,
        "scam_database_size": len(SCAM_DATABASE),
        "status": "operational"
    }

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Odoo‑17 TradingView Clone ☁️

A custom TradingView-style charting add‑on for **Odoo 17**, built for an internship task at InstaCódigo.  
Designed for stock, crypto, forex, index, and commodity charting using 3 external APIs.

Developed using WSL

## 📂 Repository Structure

- `odoo-17/` — the core Odoo 17 source
- `custom-addons/tradingview_clone/` — all custom modules: models, views, controllers, assets, etc.
- `.gitignore`
- `odoo.conf.example` — sample config
- `secrets.py` (not in repo) — holds real API keys:
  TWELVEDATA_API_KEY = "your_key_here"
  FMP_API_KEY        = "your_key_here"
  FINNHUB_KEY        = "your_key_here"

  ## Setup & Run
  1. Clone repo: git clone https://github.com/MoaazEmam/Odoo_TradingView_Clone.git
  2. Navigate to directory: Odoo_TradingView_Clone
  3. (**Optional**) Create virtual environment: python3 -m venv venv
  4. (**Optional**) Activate virtual environment: source venv/bin/activate
  5. Install requirments: pip install -r odoo-17/requirments.txt
  6. Create odoo.conf and secrets.py files
  7. Run odoo: ./odoo-17/odoo-bin -c odoo.conf --addons-path=odoo-17/addons,custom-addons
  8. Access at http://localhost:8069
  9. Install the module:
     - Log in as admin (username:admin,password:admin by default)
     - Activate developer mode
         - Click on top left menu -> Settings -> Scroll all the way down
     -  Top left menu -> Apps -> Update apps list -> search for "Tradingview clone" -> Install
  10. Now you can access http://localhost:8069/market
 
  ## Known Limitations:
  - API Rate limits: free tiers of APIs are limited (TwelveData ~800 calls/day, Finnhub low
    burst limit). May throttle or error if overused.
  - Error handling is minimal: rate limit blocks or network issues may break the chart UI.
  - No retry/backoff logic or proper caching, so live data could fail under load.
  - No unit tests or CI pipeline set up yet.
  - Deployment assumes Unix-like environment; Windows support (native) may require adjustments.
 
  ## Final notes:
Prior to starting this task I had no previous knowledge of Odoo development, as a challenge to myself and to make use of the amazing opportunity of an internship at InstaCódigo I learned as much as possible about odoo and basically built this from scratch with 0 knowledge. So, while I am aware there are limitations and uncomplete areas such as UI, I had very limited time and alot to learn and I am glad I took this task on.

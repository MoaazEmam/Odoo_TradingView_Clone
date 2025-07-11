from odoo import models,fields,api
import yfinance as yf
import requests,logging
import time
from datetime import datetime
from ..secrets import TWELVEDATA_API_KEY
_logger=logging.getLogger(__name__)
td_call_count=0
class TradingViewOhlc(models.Model):
    _name='tradingview.ohlc'
    _description='Symbol candle data'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    timestamp = fields.Datetime()
    open = fields.Float()
    high = fields.Float()
    low = fields.Float()
    close = fields.Float()
    volume = fields.Float()
    
    
####################################    SYNC FUNCTIONS  ####################################
#NOTE:
#many errors appear as a result of the not all symbols being available on yfinance
    @staticmethod
    def td_to_yfinance(symbol,asset_type):
        asset_type=asset_type.lower().strip()
        
        exchange=None
        if ':' in symbol:
            symbol,exchange=symbol.split(':')
            
        #conversions for type stock
        if asset_type=='stock':
            #global exchange suffixes
            exchange_map={
                'BATS': '.BATS',   # CBOE BZX
                'XTSX': '.TO',     # Toronto Stock Exchange
                'XNSE': '.NS',     # National Stock Exchange (India)
                'XLON': '.L',      # London Stock Exchange
                'XHKG': '.HK',     # Hong Kong Stock Exchange
                'XJSE': '.JO',     # Johannesburg Stock Exchange
                'XSHG': '.SS',     # Shanghai Stock Exchange
                'XJPX': '.T',      # Japan Exchange Group (Tokyo)
                'XASX': '.AX',     # Australian Securities Exchange
                'XFRA': '.F',      # Frankfurt Stock Exchange
                'XEBS': '.BR',     # Euronext Brussels
                'XPAR': '.PA',     # Euronext Paris
                'XMIL': '.MI',     # Borsa Italiana (Milan)
                'BMEX': '.MX',     # Bolsa Mexicana de Valores
                'XBSE': '.BO',     # Bombay Stock Exchange
                'XSWX': '.SW',     # SIX Swiss Exchange
                'XKRX': '.KS',     # Korea Exchange
                'XTKS': '.T'      # Tokyo Stock Exchange
            }
            if exchange and exchange in exchange_map:
                return f"{symbol}{exchange_map[exchange]}"
            if symbol.isdigit() and len(symbol)==6:
                return f"{symbol}.SZ"
            return symbol
        #generally switch the / with a - for crypto
        elif asset_type=='crypto':
            if '/' in symbol:
                return symbol.replace('/','-')
            return None
        #forex base/qoute turns to baseqoute=X
        elif asset_type=='forex':
            if '/' in symbol:
                symbol=symbol.replace('/','-')
                return f"{symbol}=X"
        #just a mapping
        elif asset_type=='index':
            index_map={
                'SPX': '^GSPC',     # S&P 500
                'DJI': '^DJI',      # Dow Jones Industrial Average
                'NDX': '^NDX',      # NASDAQ 100
                'FTSE': '^FTSE',    # FTSE 100
                'RUT': '^RUT',      # Russell 2000
                'VIX': '^VIX',      # CBOE Volatility Index
                'DAX': '^GDAXI',    # German DAX
                'CAC': '^FCHI',     # CAC 40 (France)
                'N225': '^N225',    # Nikkei 225 (Japan)
                'HSI': '^HSI',      # Hang Seng Index (Hong Kong)
                'AS51': '^AXJO',    # ASX 200 (Australia)
                'SENSEX': '^BSESN', # BSE Sensex (India)
            }
            return index_map.get(symbol,None)
        elif asset_type=='commodity':
            if '/' in symbol:
                return f"{symbol.replace('/','')}=X"
            return f"{symbol}=F"


    @api.model
    def sync_ohlc(self):
        _logger.info("OHLC sync started")
        try:
            active_symbols=self.env['tradingview.symbol'].search([('active','=',True)])
            batch=[]
            for i,symbol in enumerate(active_symbols):
                yf_symbol=self.td_to_yfinance(symbol.symbol,symbol.type)
                
                if not yf_symbol:
                    #_logger.warning(f"No valid conversion from TD to YFinance for {symbol.symbol}...skipping")
                    continue
                ticker=yf.Ticker(yf_symbol)
                
                try:
                    if not ticker.info or 'symbol' not in ticker.info:
                    #    _logger.warning(f"Symbol {yf_symbol} not supported")
                        self.td_fallback(symbol)
                        continue
                except Exception as e:
                    _logger.error(f"Error validating symbol {yf_symbol}")
                    continue
                
                try:
                    data=ticker.history(period="1mo",interval="5d")
                    if data.empty:
                        #_logger.warning(f"No historical data for {yf_symbol}")
                        self.td_fallback(symbol)
                        continue
                except Exception as e:
                    _logger.error(f"Failed to fetch data for {yf_symbol}: {e}")
                    self.td_fallback(symbol)
                    continue
                for timestamp,row in data.iterrows():
                    existing_record = self.sudo().search([
                        ('symbol_id', '=', symbol.id),
                        ('timestamp', '=', timestamp.to_pydatetime().replace(tzinfo=None))])
                    clean_ts=timestamp.to_pydatetime().replace(tzinfo=None)
                    if not existing_record and any(item['symbol_id'] == symbol.id and item['timestamp'] == clean_ts for item in batch):
                        batch.append({
                            'symbol_id':symbol.id,
                            'timestamp':clean_ts,
                            'open':float(row['Open']) or 0,
                            'high':float(row['High']) or 0,
                            'low':float(row['Low']) or 0,
                            'close':float(row['Close']) or 0,
                            'volume':float(row['Volume']) or 0
                        })
                #commit every 50 records
                if i%50==0:
                    self.create(batch)
                    self.env.cr.commit()
                    batch=[]
                time.sleep(7.5)
            if batch:
                self.create(batch)
                self.env.cr.commit()
            _logger.info("OHLC sync finished")
        except Exception as e:
            _logger.error(f"Failed to sync ohlc data: {e}")
    def td_fallback(self,symbol):
        #_logger.info(f"yfinance failed, attempting twelvedata: {symbol.symbol}")
        global td_call_count
        if td_call_count >= 400:
            _logger.warning("TwelveData API call limit reached (400). Skipping.")
            return
        try:
            url=f"https://api.twelvedata.com/time_series?symbol={symbol.symbol}&interval=1day&apikey={TWELVEDATA_API_KEY}"
            response=requests.get(url)
            if response.status_code!=200:
                #_logger.warning(f"Failed to fetch OHLC for {symbol.symbol}")
                return
            if response.status_code==429 or (response.json().get("message") and "out" in response.json().get("message")):
                _logger.warning("Out of TD API credits, exiting")
                return
            data=response.json().get('values',[])
            for item in data:
                existing_record = self.sudo().search([
                        ('symbol_id', '=', symbol.id),
                        datetime.strptime(item.get("datetime"),"%Y-%m-%d %H:%M:%S")])
                if not existing_record:
                    self.create({
                        'symbol_id':symbol.id,
                        'timestamp':datetime.strptime(item.get("datetime"),"%Y-%m-%d %H:%M:%S"),
                        'open':float(item.get('open')) or 0,
                        'high':float(item.get('high')) or 0,
                        'low':float(item.get('low')) or 0,
                        'close':float(item.get('close')) or 0,
                        'volume':float(item.get('volume')) or 0
                    })
                self.env.cr.commit()
                td_call_count+=1
            #_logger.info("Fetched data from twelvedata")
        except Exception as e:
            _logger.error(f"Failed to sync ohlc data: {e}")
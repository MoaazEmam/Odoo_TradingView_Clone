from odoo import models,fields,api
import requests,logging
import yfinance as yf
import time
_logger=logging.getLogger(__name__)

#after alot of searching, ive decided to use an external source that scraps yahoo finance for all tickers
#and then use those tickers with yfinance to get all its data.
class TradingViewSymbol(models.Model):
    _name='tradingview.symbol'
    _description='Trading Symbol'
    name = fields.Char() # Full company/asset name
    symbol = fields.Char() # Trading symbol (e.g., BTCUSD, AAPL)
    slug = fields.Char() # URL-safe slug (e.g., btcusd)
    exchange = fields.Char() # Exchange name or code
    region = fields.Char() # Country or market region
    currency = fields.Char() # Trading currency (USD, EUR, BTC,etc.)
    sector = fields.Char() # Sector or asset category
    industry = fields.Char() # Industry classification (if applicable)
    isin = fields.Char() # International Securities Identification Number (optional)
    active = fields.Boolean(default=True)
    type = fields.Selection([
    ('stock', 'Stock'),
    ('crypto', 'Cryptocurrency'),
    ('forex', 'Forex'),
    ('commodity', 'Commodity'),
    ('index', 'Index'),
    ], default='stock')


####################################    SYNC FUNCTIONS  ####################################

    @staticmethod
    def decide_type(info):
        quote_type=info.get("quoteType","").lower()
        market=info.get("market","").lower()
        if quote_type=='cryptocurrency':
            return 'crypto'
        elif quote_type=='commodity' or quote_type=='index':
            return quote_type
        elif market in ['fx','forex']:
            return 'forex'
        else: 
            return 'stock'
        

    @api.model
    def sync_symbols_from_apis(self):
        _logger.info("Symbol sync started")
        start_time=time.time()
        error=""
        status="success"
        try:
            with open("custom-addons/tradingview_clone/yhallsym.txt", "r", encoding='UTF-8') as f:
                symbol_dict=eval(f.read())
            for i,(symbol,name) in enumerate(symbol_dict.items()):
                try:
                    ticker=yf.Ticker(symbol)
                    info=ticker.info
                except Exception as e:
                    _logger.error(f"Error fetching info for {symbol}: {e}")
                    error=f"Error fetching info for {symbol}: {e}"
                    status="failure"
                    if "Many" in e:
                        _logger.warning("API rate limit reached, backing off")
                        return
                    continue
                slug=str(symbol).lower().replace('/','')
                exchange=info.get('exchange')
                region=info.get('country','global')
                currency=info.get('currency')
                sector=info.get('sector')
                industry=info.get('industry','')
                values={
                    'name':name,
                    'symbol':symbol,
                    'slug':slug,
                    'exchange':exchange,
                    'region':region,
                    'currency':currency,
                    'sector':sector,
                    'industry':industry,
                    'isin':'',
                    'active':True,
                    'type':self.decide_type(info)
                }
                record=self.sudo().search([('symbol','=',symbol)],limit=1)
                try:
                    if record:
                        record.sudo().write(values)
                    else:
                        self.sudo().create(values)
                    if i%50==0:
                        self.env.cr.commit()
                except Exception as e:
                    _logger.error(f"Error saving symbol {symbol}: {e}")
                time.sleep(0.9)
            _logger.info(f"Done fetching data")
        except Exception as e:
            status="failure"
            error=str(e)
            _logger.error(f"Error syncing data, {error}")
        finally:
            duration= time.time()-start_time
            self.env['tradingview.sync_log'].create({
                'api_name': 'Symbol Sync',
                'last_run': fields.Datetime.now(),
                'status': status,
                'error_message': error,
                'duration_seconds': duration
            })

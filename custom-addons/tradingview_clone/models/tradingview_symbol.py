from odoo import models,fields,api
import requests,logging
import time
from ..secrets import TWELVEDATA_API_KEY,FMP_API_KEY
_logger=logging.getLogger(__name__)

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
    tech_supported=fields.Boolean(default=True)
    news_supported=fields.Boolean(default=True)
    forum_post_id=fields.Many2one('forum.post',string='Forum Thread')
    type = fields.Selection([
    ('stock', 'Stock'),
    ('crypto', 'Cryptocurrency'),
    ('forex', 'Forex'),
    ('commodity', 'Commodity'),
    ('index', 'Index'),
    ], default='stock')


####################################    SYNC FUNCTIONS  ####################################
#since the twelvedata api doesnt provide all the fields we need
#we will also use fmp
    @api.model
    def sync_symbols_from_apis(self):
        fmp_calls=0
        _logger.info("Symbol sync started")
        start_time=time.time()
        error=""
        status="success"
        try:
            stocks_url=f"https://api.twelvedata.com/stocks?apikey={TWELVEDATA_API_KEY}"
            crypto_url=f"https://api.twelvedata.com/cryptocurrencies?apikey={TWELVEDATA_API_KEY}"
            forex_url=f"https://api.twelvedata.com/forex_pairs?apikey={TWELVEDATA_API_KEY}"
            commodities_url=f"https://api.twelvedata.com/commodities?apikey={TWELVEDATA_API_KEY}"
            indices_url=f"https://api.twelvedata.com/etfs?apikey={TWELVEDATA_API_KEY}"
            try:
                stocks = requests.get(stocks_url).json().get("data", []) #fmp api only allows 250 calls per day
                crypto = requests.get(crypto_url).json().get("data", [])
                forex = requests.get(forex_url).json().get("data", [])
                commodities = requests.get(commodities_url).json().get("data", [])
                indices = requests.get(indices_url).json().get("data", [])
            except Exception as e:
                _logger.error(f"Error fetching from TwelveData: {e}")
                error="Error fetching from TwelveData: {e}"
                status="failure"
                return

            for s in stocks: s['asset_type']='stock'
            for cr in crypto: cr['asset_type']='crypto'
            for f in forex: f['asset_type']='forex'
            for co in commodities: co['asset_type']='commodity'
            for i in indices: i['asset_type']='index'

            twelved_symbols=stocks+crypto+forex+commodities+indices
            batch=[]
            for i,symbol in enumerate(twelved_symbols):
                symbol_code=symbol.get('symbol')
                if not symbol_code:
                    continue
                #fmp only provides data for stocks
                #other types may not need sector and industry info
                sector=''
                industry=''

                if symbol.get('asset_type') =='stock' and fmp_calls<=250:
                    fmp_info=self._fetch_info_fmp(symbol_code) or {}
                    sector=fmp_info.get('sector')
                    industry=fmp_info.get('industry','')
                    fmp_calls+=1
                name=symbol.get('name') or symbol.get('currency_base') or symbol_code
                slug=str(symbol_code).lower().replace('/','')
                exchange=symbol.get('exchange') or (symbol.get('available_exchanges')[0] if symbol.get('available_exchange') else '')
                region=symbol.get('country','global')
                currency=symbol.get('currency') or symbol.get('currency_quote') or (symbol_code.split('/')[1] if '/' in symbol_code else '')
                industry=industry or symbol.get('category','')
                values={
                    'name':name,
                    'symbol':symbol_code,
                    'slug':slug,
                    'exchange':exchange,
                    'region':region,
                    'currency':currency,
                    'sector':sector,
                    'industry':industry,
                    'isin':'',
                    'active':True,
                    'tech_supported':True,
                    'type':symbol.get('asset_type','stock')
                }
                record=self.sudo().search([('symbol','=',symbol_code)],limit=1)
                try:
                    if not record and not any(item['symbol'] == symbol_code for item in batch):
                        forum=self.env['forum.forum'].search([],limit=1)
                        post=self.env['forum.post'].create({
                            'forum_id':forum.id if forum else False,
                            'name':f"{symbol_code} Discussion",
                            'content':f"Discuss {name} ({symbol_code} here. News, future events, and more!)",
                            'tag_ids':[],
                            'state':'active',
                            'moderator_id':self.env.ref('base.user_admin').id 
                        })
                        values['forum_post_id']=post.id
                        batch.append(values)
                    else:
                        record.write(values)
                    if i%50==0:
                        self.create(batch)
                        self.env.cr.commit()
                        batch=[]
                except Exception as e:
                    _logger.error(f"Error saving symbol {symbol_code}: {e}")
            if batch:
                self.create(batch)
                self.env.cr.commit()
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


    def _fetch_info_fmp(self, symbol_code):
        url=f"https://financialmodelingprep.com/stable/profile?symbol={symbol_code}&apikey={FMP_API_KEY}"
        try:
            response=requests.get(url,timeout=10)
            if response.status_code==200:
                data=response.json()
                if data and isinstance(data,list):
                    item=data[0]
                    return{
                        'sector':item.get('sector'),
                        'industry':item.get('industry'),
                    }
        except Exception as e:
            _logger.warning(f"FMP fetch failed for {symbol_code}")
            return {}

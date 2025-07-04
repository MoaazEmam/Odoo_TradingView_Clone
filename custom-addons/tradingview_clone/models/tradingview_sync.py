import requests,logging
from odoo import models,api
from ..secrets import TWELVEDATA_API_KEY,FMP_API_KEY
_logger=logging.getLogger(__name__)

#since the twelvedata api doesnt provide all the fields we need
#we will also use fmp
class TradingViewSync(models.Model):
    _inherit = 'tradingview.symbol'

    @api.model
    def sync_symbols_from_apis(self):
        _logger.info("Symbol sync started")
        stocks_url=f"https://api.twelvedata.com/stocks?apikey={TWELVEDATA_API_KEY}"
        crypto_url=f"https://api.twelvedata.com/cryptocurrencies?apikey={TWELVEDATA_API_KEY}"
        forex_url=f"https://api.twelvedata.com/forex_pairs?apikey={TWELVEDATA_API_KEY}"
        commodities_url=f"https://api.twelvedata.com/commodities?apikey={TWELVEDATA_API_KEY}"
        indices_url=f"https://api.twelvedata.com/etfs?apikey={TWELVEDATA_API_KEY}"
        try:
            stocks = requests.get(stocks_url).json().get("data", [])[:250] #fmp api only allows 250 calls per day
            crypto = requests.get(crypto_url).json().get("data", [])
            forex = requests.get(forex_url).json().get("data", [])
            commodities = requests.get(commodities_url).json().get("data", [])
            indices = requests.get(indices_url).json().get("data", [])
        except Exception as e:
            _logger.error(f"Error fetching from TwelveData: {e}")
            return
        
        for s in stocks: s['asset_type']='stock'
        for cr in crypto: cr['asset_type']='crypto'
        for f in forex: f['asset_type']='forex'
        for co in commodities: co['asset_type']='commodity'
        for i in indices: i['asset_type']='index'
        
        twelved_symbols=stocks+crypto+forex+commodities+indices
        for symbol in twelved_symbols:
            symbol_code=symbol.get('symbol')
            if not symbol_code:
                continue
            #fmp only provides data for stocks
            #other types may not need sector and industry info
            sector=''
            industry=''
            
            if symbol.get('asset_type') =='stock':
                fmp_info=self._fetch_info_fmp(symbol_code) or {}
                sector=fmp_info.get('sector')
                industry=fmp_info.get('industry','')
            name=symbol.get('name') or symbol.get('currency_base') or symbol_code
            slug=str(symbol_code).lower().replace('/','')
            exchange=symbol.get('exchange') or (symbol.get('available_exchanges'[0]) if symbol.get('available_exchange') else '')
            region=symbol.get('country','global')
            currency=symbol.get('currency') or symbol.get('currency_qoute') or (symbol_code.split('/')[1] if '/' in symbol_code else '')
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
                'type':symbol.get('asset_type','stock')
            }
            record=self.search([('symbol','=',symbol_code)],limit=1)
            try:
                if record:
                    record.sudo().write(values)
                    _logger.info(f"Updated record {record.id} with values {values}")
                else:
                    newr=self.sudo().create(values)
                    _logger.info(f"Added record {newr.id} with values {values}")
            except Exception as e:
                _logger.error(f"Error saving symbol {symbol_code}: {e}")
        _logger.info(f"Done fetching data")

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

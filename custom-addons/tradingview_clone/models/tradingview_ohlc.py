from odoo import models,fields,api
import requests,logging
from datetime import datetime
from ..secrets import TWELVEDATA_API_KEY,FMP_API_KEY
_logger=logging.getLogger(__name__)

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
    
    @api.model
    def sync_ohlc(self):
        _logger.info("OHLC sync started")
        
        try:
            active_symbols=self.env['tradingview.symbol'].search([('active','=',True)])
            for i,symbol in enumerate(active_symbols):
                url=f"https://api.twelvedata.com/time_series?symbol={symbol.symbol}&interval=1min&apikey={TWELVEDATA_API_KEY}"
                response=requests.get(url)
                if response.status_code!=200:
                    _logger.warning(f"Failed to fetch OHLC for {symbol.symbol}")
                    continue
                    
                data=response.json().get('values',[])
                for item in data:
                    self.sudo().create({
                        'symbol_id':symbol.id,
                        'timestamp':datetime.strptime(item.get("datetime"),"%Y-%m-%d %H:%M:%S"),
                        'open':float(item.get('open')),
                        'high':float(item.get('high')),
                        'low':float(item.get('low')),
                        'close':float(item.get('close')),
                        'volume':float(item.get('volume'))
                    })
                if i%50==0:
                    self.env.cr.commit()
            _logger.info("OHLC sync finished")
        except Exception as e:
            _logger.error(f"Failed to sync ohlc data: {e}")
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

    @api.model
    def sync_ohlc(self):
        _logger.info("OHLC sync started")
        try:
            active_symbols=self.env['tradingview.symbol'].search([('active','=',True)])
            batch=[]
            for i,symbol in enumerate(active_symbols):
                try:
                    url=f"https://api.twelvedata.com/time_series?symbol={symbol.symbol}&interval=1day&apikey={TWELVEDATA_API_KEY}"
                    response=requests.get(url)
                    if response.status_code==429 or (response.json().get("message") and "out" in response.json().get("message")):
                        _logger.warning("Out of TD API credits, exiting")
                        return
                    if response.status_code!=200:
                        #_logger.warning(f"Failed to fetch OHLC for {symbol.symbol}")
                        return
                    data=response.json().get('values',[])
                    for item in data:
                        clear_ts=datetime.strptime(item.get("datetime"),"%Y-%m-%d")
                        existing_record = self.sudo().search([
                                ('symbol_id', '=', symbol.id),
                                ('timestamp','=',clear_ts)])
                        if not existing_record and not any(item['symbol_id']==symbol.id and item['timestamp'] == clear_ts  for item in batch):
                            batch.append({
                                'symbol_id':symbol.id,
                                'timestamp':clear_ts,
                                'open':float(item.get('open')) or 0,
                                'high':float(item.get('high')) or 0,
                                'low':float(item.get('low')) or 0,
                                'close':float(item.get('close')) or 0,
                                'volume':float(item.get('volume')) or 0
                            })
                    if i%50==0:
                        self.create(batch)
                        self.env.cr.commit()
                        batch=[]
                    if i==400:
                        _logger.warning("200 API credits used, existing")
                        break
                    time.sleep(7.5)
                except Exception as e:
                    _logger.error(f"Failed to sync ohlc data: {e}")
            if batch:
                self.create(batch)
                self.env.cr.commit()
            _logger.info("OHLC sync finished")
        except Exception as e:
            _logger.error(f"Failed to sync ohlc data: {e}")
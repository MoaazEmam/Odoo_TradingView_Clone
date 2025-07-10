from odoo import models,fields,api
import requests,logging
import datetime as datetime
import time
from ..secrets import TWELVEDATA_API_KEY,FMP_API_KEY
_logger=logging.getLogger(__name__)

class TradingViewTechnical(models.Model):
    _name='tradingview.technical'
    _description='Symbol technical indicators'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    indicator = fields.Char() # RSI, MACD, SMA, EMA, Bollinger Bands
    value = fields.Float()
    timestamp = fields.Datetime()
    
    
####################################    SYNC FUNCTIONS  ####################################

    @api.model
    def sync_technical(self):
        _logger.info("Sync technical starting")
        try:
            active_symbols=self.env['tradingview.symbol'].search([('active','=',True)])
            for i,symbol in enumerate(active_symbols):
                bbands_url=f"https://api.twelvedata.com/bbands?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                rsi_url=f"https://api.twelvedata.com/rsi?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                macd_url=f"https://api.twelvedata.com/macd?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                sma_url=f"https://api.twelvedata.com/sma?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                ema_url=f"https://api.twelvedata.com/ema?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                try:
                    bbands=requests.get(bbands_url).json().get("values",[])
                    rsi=requests.get(rsi_url).json().get("values",[])
                    macd=requests.get(macd_url).json().get("values",[])
                    sma=requests.get(sma_url).json().get("values",[])
                    ema=requests.get(ema_url).json()
                    if ema.get("code")==429 or (ema.get("message") and "out" in ema.get("message")):
                        _logger.warning("Out of TD API credits, exiting")
                        return
                    try:
                        ema=ema.get("values",[])
                        self.create({
                            'symbol_id':symbol.id,
                            'indicator':'Bollinger Bands',
                            'value':bbands[0].get("middle_band"),
                            'timestamp':datetime.strptime(bbands[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                        })
                        self.create({
                            'symbol_id':symbol.id,
                            'indicator':'RSI',
                            'value':rsi[0].get("rsi"),
                            'timestamp':datetime.strptime(rsi[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                        })
                        self.create({
                            'symbol_id':symbol.id,
                            'indicator':'MACD',
                            'value':macd[0].get("macd"),
                            'timestamp':datetime.strptime(macd[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                        })
                        self.create({
                            'symbol_id':symbol.id,
                            'indicator':'SMA',
                            'value':sma[0].get("sma"),
                            'timestamp':datetime.strptime(sma[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                        })
                        self.create({
                            'symbol_id':symbol.id,
                            'indicator':'EMA',
                            'value':ema[0].get("ema"),
                            'timestamp':datetime.strptime(ema[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                        })
                        time.sleep(0.5)
                    except Exception as e:
                        _logger.error(f"Failed to save technical indicators for {symbol.symbol}: {e}")
                    if i%10==0:
                        self.env.cr.commit()
                except Exception as e:
                    _logger.error(f"Failed to sync indicators for {symbol.symbol}: {e}")
                    continue
                self.env.cr.commit()
        except Exception as e:
            _logger.error(f"Failed to sync technical indicators: {e}")
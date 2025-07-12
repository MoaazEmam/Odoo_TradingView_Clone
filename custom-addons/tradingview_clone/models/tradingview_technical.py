from odoo import models,fields,api
import requests,logging
from datetime import datetime
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
            active_symbols=self.env['tradingview.symbol'].search([('active','=',True),('tech_supported','=',True)])
            batch=[]
            unsupported_symbols=[]
            for i,symbol in enumerate(active_symbols):
                if symbol.symbol in unsupported_symbols:
                    continue
                bbands_url=f"https://api.twelvedata.com/bbands?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                rsi_url=f"https://api.twelvedata.com/rsi?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                macd_url=f"https://api.twelvedata.com/macd?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                sma_url=f"https://api.twelvedata.com/sma?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                ema_url=f"https://api.twelvedata.com/ema?symbol={symbol.symbol}&interval=15min&apikey={TWELVEDATA_API_KEY}"
                try:
                    time.sleep(7.5)
                    bbands=requests.get(bbands_url).json()
                    if bbands.get("code")==429 or (bbands.get("message") and "out" in bbands.get("message")):
                        _logger.warning("Out of TD API credits, exiting")
                        return
                    if bbands.get("code")==404:
                        _logger.warning(f"{symbol.symbol}: {bbands.get("message")}")
                        symbol.write({'tech_supported':False})
                        self.env.cr.commit()
                        continue
                    bbands=bbands.get("values",[])
                    time.sleep(7.5)
                    rsi=requests.get(rsi_url).json().get("values",[])
                    time.sleep(7.5)
                    macd=requests.get(macd_url).json().get("values",[])
                    time.sleep(7.5)
                    sma=requests.get(sma_url).json().get("values",[])
                    time.sleep(7.5)
                    ema=requests.get(ema_url).json().get("values",[])
                    try:
                        for item in bbands:
                            batch.append({
                                'symbol_id':symbol.id,
                                'indicator':'Bollinger Bands',
                                'value':item.get("middle_band"),
                                'timestamp':datetime.strptime(bbands[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                            })
                        for item in rsi:
                            batch.append({
                                'symbol_id':symbol.id,
                                'indicator':'RSI',
                                'value':item.get("rsi"),
                                'timestamp':datetime.strptime(rsi[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                            })
                        for item in macd:
                            batch.append({
                                'symbol_id':symbol.id,
                                'indicator':'MACD',
                                'value':item.get("macd"),
                                'timestamp':datetime.strptime(macd[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                            })
                        for item in sma:
                            batch.append({
                                'symbol_id':symbol.id,
                                'indicator':'SMA',
                                'value':item.get("sma"),
                                'timestamp':datetime.strptime(sma[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                            })
                        for item in ema:
                            batch.append({
                                'symbol_id':symbol.id,
                                'indicator':'EMA',
                                'value':item.get("ema"),
                                'timestamp':datetime.strptime(ema[0].get("datetime"),"%Y-%m-%d %H:%M:%S")
                            })
                    except Exception as e:
                        _logger.error(f"Failed to save technical indicators for {symbol.symbol}: {e}")
                    if i%10==0:
                        self.create(batch)
                        self.env.cr.commit()
                        batch=[]
                    #if i==80:
                    #    break
                except Exception as e:
                    _logger.error(f"Failed to sync indicators for {symbol.symbol}: {e}")
                    continue
            if batch:
                self.create(batch)
                self.env.cr.commit()
        except Exception as e:
            _logger.error(f"Failed to sync technical indicators: {e}")
from odoo import models,fields

class TradingViewOhlc(models.Model):
    _name='tradingview.ohlc'
    _description='Symbol Candel data'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    timestamp = fields.Datetime()
    open = fields.Float()
    high = fields.Float()
    low = fields.Float()
    close = fields.Float()
    volume = fields.Float()

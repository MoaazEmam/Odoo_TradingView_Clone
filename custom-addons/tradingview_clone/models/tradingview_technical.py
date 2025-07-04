from odoo import models,fields

class TradingViewTechnical(models.Model):
    _name='tradingview.technical'
    _description='Symbol technical indicators'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    indicator = fields.Char()
    value = fields.Float()
    timestamp = fields.Datetime()
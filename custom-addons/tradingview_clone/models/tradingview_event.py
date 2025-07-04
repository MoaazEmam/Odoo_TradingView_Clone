from odoo import models,fields

class TradingViewEvent(models.Model):
    _name='tradingview.event'
    _description='Symbol events'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    title = fields.Char()
    event_type = fields.Selection([('earnings', 'Earnings'), ('split',
    'Split'), ('fork', 'Fork'), ('other', 'Other')])
    date = fields.Datetime()
    impact_level = fields.Selection([('low', 'Low'), ('medium',
    'Medium'), ('high', 'High')])
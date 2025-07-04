from odoo import models,fields

class TradingViewNews(models.Model):
    _name='tradingview.news'
    _description='Symbol news'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    title = fields.Char()
    summary = fields.Text()
    link = fields.Char()
    source = fields.Char()
    published_at = fields.Datetime()
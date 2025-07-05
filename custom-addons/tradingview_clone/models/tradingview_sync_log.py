from odoo import models,fields

class TradingViewSyncLog(models.Model):
    _name='tradingview.sync_log'
    _description='Symbol sync logs'
    
    api_name = fields.Char()
    last_run = fields.Datetime()
    status = fields.Selection([('success', 'Success'), ('failure',
    'Failure')])
    error_message = fields.Text()
    duration_seconds = fields.Float()
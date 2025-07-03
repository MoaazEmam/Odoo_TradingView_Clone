from odoo import models,fields

class TradingViewSymbol(models.Model):
    _name='tradingview.symbol'
    _description='Trading Symbol'
    name = fields.Char() # Full company/asset name
    symbol = fields.Char() # Trading symbol (e.g., BTCUSD, AAPL)
    slug = fields.Char() # URL-safe slug (e.g., btcusd)
    exchange = fields.Char() # Exchange name or code
    region = fields.Char() # Country or market region
    currency = fields.Char() # Trading currency (USD, EUR, BTC,etc.)
    sector = fields.Char() # Sector or asset category
    industry = fields.Char() # Industry classification (if applicable)
    isin = fields.Char() # International Securities Identification Number (optional)
    active = fields.Boolean(default=True)
    type = fields.Selection([
    ('stock', 'Stock'),
    ('crypto', 'Cryptocurrency'),
    ('forex', 'Forex'),
    ('commodity', 'Commodity'),
    ('index', 'Index'),
    ], default='stock')
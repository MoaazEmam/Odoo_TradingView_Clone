from odoo import http
from odoo.http import request

class TradingViewWebsite(http.Controller):
    @http.route('/market',type='http',auth='public',website=True,
                sitemap=True)
    def market_page(self,**kwargs):
        symbols=request.env['tradingview.symbol'].sudo().search([])
        return request.render('tradingview_clone.market_page',{
            'symbols':symbols
        })
    #here ill use slug instead of symbol since it is url safe
    @http.route('/market/<string:slug>',type='http',auth='public',website=True,
                sitemap=True)
    def symbol_detail(self,slug,**kwargs):
        symbol=request.env['tradingview.symbol'].sudo().search(['slug','=',slug],limit=1)
        if not symbol:
            return request.not_found()
        return request.render('tradingview_clone.symbol_detail',{
            'symbol':symbol
        })
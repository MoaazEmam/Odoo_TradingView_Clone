# -*- coding: utf-8 -*-
# from odoo import http


# class TradingviewClone(http.Controller):
#     @http.route('/tradingview_clone/tradingview_clone', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tradingview_clone/tradingview_clone/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tradingview_clone.listing', {
#             'root': '/tradingview_clone/tradingview_clone',
#             'objects': http.request.env['tradingview_clone.tradingview_clone'].search([]),
#         })

#     @http.route('/tradingview_clone/tradingview_clone/objects/<model("tradingview_clone.tradingview_clone"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tradingview_clone.object', {
#             'object': obj
#         })


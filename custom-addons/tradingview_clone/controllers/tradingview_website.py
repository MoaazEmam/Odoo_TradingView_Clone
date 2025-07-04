from odoo import http
from odoo.http import request
from collections import defaultdict
import math

class TradingViewWebsite(http.Controller):
    @http.route('/market',type='http',auth='public',website=True,
                sitemap=True)
    def market_page(self,**kwargs):
        symbols=request.env['tradingview.symbol'].sudo().search([])
        
        # Group symbols by type
        grouped = defaultdict(list)
        for symbol in symbols:
            grouped[symbol.type].append(symbol)
        
        # Pagination settings
        items_per_page = 5
        paginated_groups = {}
        
        for symbol_type, symbol_list in grouped.items():
            # Get current page for this type (default to 0)
            current_page = int(kwargs.get(f'{symbol_type}_page', 0))
            total_pages = math.ceil(len(symbol_list) / items_per_page)
            
            # Ensure current_page is within bounds
            current_page = max(0, min(current_page, total_pages - 1))
            
            # Get symbols for current page
            start_idx = current_page * items_per_page
            end_idx = start_idx + items_per_page
            page_symbols = symbol_list[start_idx:end_idx]
            
            paginated_groups[symbol_type] = {
                'symbols': page_symbols,
                'current_page': current_page,
                'total_pages': total_pages,
                'has_prev': current_page > 0,
                'has_next': current_page < total_pages - 1,
                'prev_page': current_page - 1,
                'next_page': current_page + 1,
                'total_count': len(symbol_list)
            }
        
        return request.render('tradingview_clone.market_page',{
            'symbols':symbols,
            'grouped_symbols': paginated_groups,
            'items_per_page': items_per_page
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
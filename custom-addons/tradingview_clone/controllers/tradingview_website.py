from odoo import http
from odoo.http import request
from collections import defaultdict
import math

class TradingViewWebsite(http.Controller):
    
    @http.route('/market/<string:symbol_slug>', type='http', auth="public", website=True)
    def market_symbol_page(self, symbol_slug):
        symbol = request.env['tradingview.symbol'].sudo().search([('slug', '=', symbol_slug)], limit=1)
        if not symbol:
            return request.not_found()
        return request.render('tradingview_clone.symbol_page', {
            'symbol': symbol,
        })

    @http.route('/market', type='http', auth='public', website=True, sitemap=True)
    def market_page(self, **kwargs):
        Symbol = request.env['tradingview.symbol'].sudo()

        # Gather filter values from query parameters
        search_term = kwargs.get('q', '').lower()
        region_filter = kwargs.get('region')
        sector_filter = kwargs.get('sector')
        exchange_filter = kwargs.get('exchange')
        type_filter = kwargs.get('type')

        # Build domain dynamically
        domain = [('active', '=', True)]
        if search_term:
            domain += ['|', ('name', 'ilike', search_term), ('symbol', 'ilike', search_term)]
        if region_filter:
            domain += [('region', '=', region_filter)]
        if sector_filter:
            domain += [('sector', '=', sector_filter)]
        if exchange_filter:
            domain += [('exchange', '=', exchange_filter)]
        if type_filter:
            domain += [('type', '=', type_filter)]

        all_symbols = Symbol.search(domain)

        # Pagination and grouping by type
        grouped = defaultdict(list)
        for symbol in all_symbols:
            grouped[symbol.type].append(symbol)

        items_per_page = 8
        paginated_groups = {}

        for symbol_type, symbol_list in grouped.items():
            current_page = int(kwargs.get(f'{symbol_type}_page', 0))
            total_pages = math.ceil(len(symbol_list) / items_per_page)
            current_page = max(0, min(current_page, total_pages - 1))

            start = current_page * items_per_page
            end = start + items_per_page

            paginated_groups[symbol_type] = {
                'symbols': symbol_list[start:end],
                'current_page': current_page,
                'total_pages': total_pages,
                'has_prev': current_page > 0,
                'has_next': current_page < total_pages - 1,
                'prev_page': current_page - 1,
                'next_page': current_page + 1,
                'total_count': len(symbol_list),
            }

        def get_unique(field):
            return sorted(set(rec[field] for rec in Symbol.search_read([(field, '!=', False)], [field])))

        filters = {
            'regions': get_unique('region'),
            'sectors': get_unique('sector'),
            'exchanges': get_unique('exchange'),
            'types': Symbol._fields['type'].selection,
        }

        return request.render('tradingview_clone.market_page', {
            'grouped_symbols': paginated_groups,
            'filters': filters,
            'applied_filters': {
                'region': region_filter,
                'sector': sector_filter,
                'exchange': exchange_filter,
                'type': type_filter,
                'q': search_term,
            }
        })

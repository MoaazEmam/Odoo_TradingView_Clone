from odoo import models,fields,api
import logging
from ..secrets import FINNHUB_KEY
from datetime import datetime,timedelta
import time
import finnhub
_logger=logging.getLogger(__name__)

class TradingViewNews(models.Model):
    _name='tradingview.news'
    _description='Symbol news'
    
    symbol_id = fields.Many2one('tradingview.symbol')
    title = fields.Char()
    summary = fields.Text()
    link = fields.Char()
    source = fields.Char()
    published_at = fields.Datetime()
    
    
####################################    SYNC FUNCTIONS  ####################################
    @api.model
    def sync_news(self):
        finnhub_client = finnhub.Client(api_key=f"{FINNHUB_KEY}")
        today=datetime.now()
        yesterday=today-timedelta(days=30)
        active_symbols=self.env['tradingview.symbol'].search([('active','=',True),('news_supported','=',True)])
        batch=[]
        for i,symbol in enumerate(active_symbols):
            try:
                print(f"Getting news for symbol {symbol.symbol}")
                news_dict=finnhub_client.company_news(symbol.symbol,yesterday.strftime('%Y-%m-%d'),today.strftime('%Y-%m-%d'))
                if news_dict==[]:
                    _logger.warning(f"{symbol.symbol} is not supported")
                    symbol.write({'news_supported':False})
                    self.env.cr.commit()
                    time.sleep(7.5)
                    continue
                print(f"Got news for symbol {symbol.symbol}: {news_dict}")
                for news in news_dict:
                    link=news.get('url')
                    existing_news = self.env['tradingview.news'].search([('link', '=', link)], limit=1)
                    if not existing_news and not any(item['link'] == link for item in batch):
                        try:
                            batch.append({
                                'symbol_id':symbol.id,
                                'title':news.get('headline'),
                                'summary':news.get('summary'),
                                'link':link,
                                'source':news.get('source'),
                                'published_at':datetime.fromtimestamp(news.get('datetime') / 1000)
                            })
                            print(len(batch))
                        except Exception as e:
                            _logger.error(f"Failed to save news for {symbol.symbol}: {e}")
            except Exception as e:
                if '429' in str(e):
                    _logger.error(f"No more finnhub API credits, exiting: {e}")
                    return
                else:
                    _logger.error(f"Error occured while fetching news for {symbol.symbol}: {e}")
            if i%50 ==0:
                self.create(batch)
                self.env.cr.commit()
                batch=[]
            time.sleep(5)
        if batch:
            self.create(batch)
            self.env.cr.commit()
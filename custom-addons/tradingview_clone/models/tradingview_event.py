from odoo import models,fields
import logging
from datetime import datetime,timedelta
import datefinder
import time
_logger=logging.getLogger(__name__)

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
    
    
####################################    SYNC FUNCTIONS  ####################################
#NOTE: I was not able to find a reliable AND free api to get data like earnings calender and splits 
###### so i decided to try and parse the news i already store to find events etc

    def sync_events(self):
        _logger.info("Event sync starting")
        event_keywords={
            'earnings':['earnings','earnings call','earnings report','Q1 results','Q2 results','Q3 results','Q4 results','eps'],
            'split':['split','stock split','share split','split date'],
            'fork':['fork','hard fork','soft fork','protocol upgrade']
        }
        now=datetime.now()
        latest_news=self.env['tradingview.news'].search([('published_at','>=',datetime.now()-timedelta(days=30))])
        batch=[]
        for i,news in enumerate(latest_news):
            text=f'{news.title or''}{news.summary or ''}'.lower()
            event_type=''
            #if any of the phrases in event_keywords is found in the text, consider it event
            for key,phrases in event_keywords.items():
                if any(phrase in text for phrase in phrases):
                    event_type=key
                    break
            impact=''
            if event_type=='':
                continue
            else:
                if event_type in ['earnings','fork']:
                    impact='high'
                else:
                    impact='medium'
            found_date=None
            dates=list(datefinder.find_dates(text))
            for date in dates:
                if date>now:
                    found_date=date
                    break
            
            if not found_date:
                continue
            
            event_title=news.title or f'{event_type.capitalize()} Event'
            existing=self.search([
                ('symbol_id','=',news.symbol_id),
                ('title','=',event_title),
                ('date','=',found_date)
            ],limit=1)
            if not existing and not any(item['title'] == event_title for item in batch):
                batch.append({
                    'symbol_id':news.symbol_id,
                    'title':event_title,
                    'event_type':event_type,
                    'date':found_date,
                    'impact_level':impact
                })
            if i%50==0:
                self.create(batch)
                self.env.cr.commit()
                batch=[]
            print(i)
        if batch:
            self.create(batch)
            self.env.cr.commit()
        _logger.info("Event sync finished")
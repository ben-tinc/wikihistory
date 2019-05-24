#!/usr/bin/env python3

from datetime import datetime
from urllib.parse import parse_qs, urlsplit
import re

import scrapy

# Ignore revisions older than 4 years.
MAX_DAYS_AGE = 1460


class HistorySpider(scrapy.Spider):
    name = "history"
    now = datetime.now()

    def start_requests(self):
        template = 'https://de.wikipedia.org/wiki/Kategorie:{}'
        # Default value, if there were no command line arguments.
        categories = getattr(self, 'cats', 'Geschichte_der_Malerei,Rechtsextremismus,Kernenergie,Mathematik')
        #categories = 'Altes_Ägypten'
        categories = categories.split(',')

        for cat in categories:
            url = template.format(cat)
            request = scrapy.Request(url=url, callback=self.parse_category)
            request.meta['category'] = cat
            yield request

    def parse_category(self, response):
        # history_base = [
        #     'https://de.wikipedia.org/w/index.php?title='
        #     &offset=<datetime>&limit=<Anzahl%20an%20%C3%84nderungen>&action=history'
        # baseurl = response.url
        urlpaths = response.css('div#mw-pages li a::attr(href)').extract()
        for path in urlpaths:
            pagename = path.split('/')[-1]
            history_url = ''.join([
                'https://de.wikipedia.org/w/index.php?title=',
                pagename,
                '&action=history'
            ])
            # print(history_url)
            request = scrapy.Request(url=history_url, callback=self.parse_history)
            request.meta['category'] = response.meta['category']
            request.meta['pagename'] = pagename
            request.meta['subcat'] = response.meta.get('subcat', None)
            yield request
        
        if response.meta.get('subcat', None) is None:
            subcats = response.css('div#mw-subcategories li a::attr(href)').extract()
            
            for path in subcats:
                url = 'https://de.wikipedia.org' + path
                pagename = path.split('/')[-1]
                request = scrapy.Request(url=url, callback=self.parse_category)
                request.meta['category'] = response.meta['category']
                request.meta['subcat'] = pagename
                yield request

   
    def parse_history(self, response):
        # Determine the datetime offset of this history page.
        offset = self._parse_offset(response.url)
        if offset and (self.now - offset).days > MAX_DAYS_AGE:
            return

        for item in response.css('ul#pagehistory li'):
            user = item.css('span.history-user bdi::text').extract_first()
            # can be both <span> and <a>
            date = item.css('.mw-changeslist-date::text').extract_first() 
            minor = item.css('abbr.minoredit').extract_first() != None
            history_size = item.css('span.history-size::text').extract_first()
            change_size = item.css('span.mw-plusminus-pos::text').extract_first()
            if change_size is None:
                change_size = item.css('span.mw-plusminus-neg::text').extract_first() or 0
            # In theory, there is a mediawiki marker for changes which revert
            # to previous versions, but these are often times not present.
            # So we need to use heuristics to find out if a given version is 
            # a revert.
            revert = self._check_if_revert(item)
            yield {
                'user': user,
                'date': date,
                'minor': minor,
                'history_size': history_size,
                'change_size': change_size,
                'revert': revert,
                'category': response.meta['category'],
                'subcat': response.meta.get('subcat', None),
                'pagename': response.meta['pagename'],
            }
        # After parsing all the revision items, look if there is another page 
        # in the page history.
        next_page = response.css('div#mw-content-text a.mw-nextlink').extract_first()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_history)          

    def _parse_offset(self, url):
        """Offset strings are of the form `yyyymmddhhmmss`."""
        queries = parse_qs(urlsplit(url).query)
        try:
            offset = self._parse_offset(queries['offset'])
            pattern = re.compile(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})')   
            (year, month, day, hours, minutes, seconds) = pattern.match(offset).groups()
            dt = datetime(int(year), int(month), int(day), int(hours), int(minutes), int(seconds))
        except:
            dt = None    
        return dt
    
    def _check_if_revert(self, item):
        """Heuristic to check if a given listitem is a revert of a previous
        edit.
        """
        revert = False
        if (
            item.css('.mw-tag-marker-mw-rollback').extract_first() is not None
            or item.css('.mw-tag-marker-mw-undo').extract_first() is not None):
            return True
        comment = item.css('span.comment::text').extract_first()
        if comment is not None:
            comment = comment.lower()
            revert = ('rückgängig' in comment or 'zurückgesetzt' in comment)
        return revert


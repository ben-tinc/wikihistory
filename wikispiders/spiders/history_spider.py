#!/usr/bin/env python3

import scrapy


class HistorySpider(scrapy.Spider):
    name = "history"
    # start_urls = [
    #     'https://de.wikipedia.org/wiki/Kategorie:Rechtsextremismus',
    # ]

    def start_requests(self, categories=['Rechtsextremismus']):
        for cat in categories:
            url = 'https://de.wikipedia.org/wiki/Kategorie:%s' % cat
            yield scrapy.Request(url=url, callback=self.parse_category)

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
            print(history_url)
            yield scrapy.Request(url=history_url, callback=self.parse_history)

   

    def parse_history(self, response):
        print(response.url)
        pass

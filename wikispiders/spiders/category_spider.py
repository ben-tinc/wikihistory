#!/usr/bin/env python3

import scrapy


class CategorySpider(scrapy.Spider):
    name = "categorypages"
    start_urls = [
        'https://de.wikipedia.org/wiki/Kategorie:Rechtsextremismus',
    ]

    # def start_requests(self, category='Rechtsextremismus'):
    #     url = 'https://de.wikipedia.org/wiki/Kategorie:%s' % category
    #     yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        """Should return a dict with relevant data."""
        print('#####################################')
        baseurl = response.url
        print(baseurl)
        urlpaths = response.css('div#mw-pages li a::attr(href)').extract()
        for path in urlpaths:
            print(path)
        print('#####################################')

# -*- coding: utf-8 -*-
import re
import scrapy

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join
from scrapy.shell import inspect_response

from w3lib.html import remove_tags

from ..items import ProductItem


class TigerChefProductLoader(ItemLoader):

    re_desc = re.compile(r'\t+')

    default_output_processor = TakeFirst()

    def desc_in(self, input):
        return self.re_desc.sub(' ', remove_tags(input[0]))


class TigerChefSpider(CrawlSpider):
    name = 'tigerchef'
    allowed_domains  = ['www.tigerchef.com']
    start_urls = ['https://www.tigerchef.com/sitemap.php']

    rules = [Rule(LinkExtractor(allow=r'\?entrant=', deny='\?form_values=')),
             Rule(LinkExtractor(allow=r'[\w-]+\.html', deny='\.php'), callback='parse_product')]

    def parse_product(self, response):
        info = response.css('div#product-info')
        if not info:
            return self.parse(response)

        loader = TigerChefProductLoader(item=ProductItem(), response=response)

        loader.nested_css('div#product-info')
        loader.add_css('title', 'h1.product-title::text')
        loader.add_css('price', 'span#the-price::attr(content)')
        #loader.add_css('quantity', 'span#priced_per::text')
        loader.add_css('desc', 'div.description-holder::text')

        loader.nested_css('div.specifications-holder')
        loader.add_css('brand', 'li[itemprop="name"]::text')
        loader.add_css('model', 'li[itemprop="sku"]::text')
        loader.add_xpath('quantity', './/li[text()="Sold As:"]/following-sibling::li/text()')
        loader.add_xpath('sku', './/li[text()="Tigerchef ID:"]/following-sibling::li/text()')

        loader.add_value('url', response.url)

        return loader.load_item()

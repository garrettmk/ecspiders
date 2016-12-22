# -*- coding: utf-8 -*-
import re
import scrapy

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join
from scrapy.shell import inspect_response

from ..items import ProductItem


class ZoroProductLoader(ItemLoader):

    default_output_processor = TakeFirst()


class ZoroSpider(CrawlSpider):
    name = 'zoro'
    allowed_domains = ['www.zoro.com']
    start_urls = ['https://www.zoro.com']

    rules = [Rule(LinkExtractor(allow=r'/i/'), callback='parse_product'),
             Rule(LinkExtractor(allow=[r'/[\w-]+$', r'/c/', r'page=']))]

    def parse_product(self, response):
        loader = ZoroProductLoader(item=ProductItem(), response=response)

        loader.nested_css('div.product-header')
        loader.add_css('title', 'span[itemprop="name"]::text')
        loader.add_css('brand', 'span[itemprop="brand"]::text')
        loader.add_css('sku', 'span[itemprop="sku"]::text')
        loader.add_css('model', 'span[itemprop="mpn"]::text')

        loader.nested_css('div#price-stock')
        loader.add_css('price', 'span[itemprop="price"]::text')
        loader.add_xpath('quantity', './/span[@itemprop="price"]/following-sibling::small/text()')

        loader.nested_css('div#prod-info')
        loader.add_css('desc', 'span[itemprop="description"]::text')

        loader.add_value('url', response.url)

        return loader.load_item()


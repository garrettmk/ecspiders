# -*- coding: utf-8 -*-
import re
import scrapy

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join, Compose
from scrapy.shell import inspect_response

from w3lib.html import remove_tags

from ..items import ProductItem


class KatomProductLoader(ItemLoader):

    default_output_processor = TakeFirst()

    re_sku = re.compile(r'KaTom #: ([^\s]+)', re.IGNORECASE)
    re_model = re.compile(r'MPN: ([^\s]+)', re.IGNORECASE)
    re_price = re.compile(r'(\d+[\d,]*\.\d+)')
    re_quantity = re.compile(r'/ (.*)')
    re_desc = re.compile(r'\t+')

    title_out = Join()

    def sku_in(self, input):
        match = self.re_sku.search(input[0])
        return match.group(1)

    def model_in(self, input):
        match = self.re_model.search(input[0])
        return match.group(1)

    def price_in(self, input):
        match = self.re_price.search(input[0])
        return match.group(1)

    def quantity_in(self, input):
        match = self.re_quantity.search(input[0])
        return match.group(1)

    def desc_in(self, input):
        return self.re_desc.sub(' ', remove_tags(input[0]))


class KatomSpider(CrawlSpider):
    name = "katom"
    allowed_domains = ["www.katom.com"]
    start_urls = ['https://www.katom.com/account/login']

    rules = [Rule(LinkExtractor(allow=r'\?page=')),
             Rule(LinkExtractor(allow=r'/cat/', deny=r'\?')),
             Rule(LinkExtractor(allow=r'\d+-\w+\.html'), callback='parse_product')]

    def parse_start_url(self, response):
        return scrapy.FormRequest(url='https://www.katom.com/account/login',
                                  formdata={'email': 'prwlrspider@gmail.com',
                                            'password': 'foofoo17'},
                                  callback=self.after_login)

    def after_login(self, response):
        if b'Error' in response.body:
            self.logger.error('Login failed.')
        else:
            self.logger.info('Login successful.')

        return scrapy.Request('https://www.katom.com')

    def parse_product(self, response):
        loader = KatomProductLoader(item=ProductItem(), response=response)

        try:
            loader.add_css('desc', 'section#overview')

            loader.nested_css('div.product-info')
            loader.add_css('title', 'h1[itemprop="name"]::text')
            loader.add_css('sku', 'span.code::text')
            loader.add_css('model', 'span.code::text')
            loader.add_css('price', 'strong.price::text')
            loader.add_css('quantity', 'strong.price span::text')

            loader.nested_css('section#overview')
            loader.add_css('brand', 'span[itemprop="brand"]::text')

            loader.add_value('url', response.url)

            return loader.load_item()
        except:
            self.logger.error('Error parsing product: %s' % response.url)


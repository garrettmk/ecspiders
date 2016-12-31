# -*- coding: utf-8 -*-
import re

from scrapy import Request
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
    rules = [Rule(LinkExtractor(restrict_css='li.level3'), callback='parse_category')]

    product_links = LinkExtractor(restrict_css='strong.category-title')

    def parse_category(self, response):
        """Return requests for product info pages, then a request for the next button."""
        for link in self.product_links.extract_links(response):
            yield Request(url=link.url, callback=self.parse_product)

        rel_link = response.css('div.pagination a[rel="next"]::attr(href)').extract_first()
        if rel_link:
            yield Request(url=response.urljoin(rel_link), callback=self.parse_category)

    def parse_product(self, response):
        """Extract product data from a product info page."""
        loader = TigerChefProductLoader(item=ProductItem(), response=response)

        loader.nested_css('div#product-info')
        loader.add_css('title', 'h1.product-title::text')
        loader.add_css('price', 'span#the-price::attr(content)')
        loader.add_css('price', 'span[itemprop="lowPrice"]::attr(content)')
        loader.add_css('desc', 'div.description-holder::text')

        # Try to extract the price if it says "add to cart to show price"
        script = response.css('div.qty-add-holder script').extract_first()
        if script:
            item_number = response.xpath('//li[text()="Item Number:"]/following-sibling::li/text()').extract_first()
            loader.add_value('price', re.search(r'\'%s\'.*\'(.*)\'' % item_number, script).group(1))

        loader.nested_css('div.specifications-holder')
        loader.add_css('brand', 'li[itemprop="name"]::text')
        loader.add_css('model', 'li[itemprop="sku"]::text')
        loader.add_xpath('quantity', './/li[text()="Sold As:"]/following-sibling::li/text()')
        loader.add_xpath('sku', './/li[text()="Tigerchef ID:"]/following-sibling::li/text()')

        return loader.load_item()

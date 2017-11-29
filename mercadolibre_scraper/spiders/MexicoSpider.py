import pkgutil

import scrapy
from datetime import datetime


class MLMexicoSpider(scrapy.Spider):
    name = "mercadolibre.com.mx"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        binary_string = pkgutil.get_data("mercadolibre_scraper", "resources/key_words.txt")
        self.key_words = binary_string.decode("utf-8").split("\n")

        self.details_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Accept-Language": "en",
            "Connection": "keep-alive"
        }

        self.today_date = str(datetime.now().date())

    def start_requests(self):
        for key_word in self.key_words:
            yield scrapy.Request(url="https://listado.mercadolibre.com.mx/" + key_word,
                                 callback=self.parse,
                                 meta={"key_word": key_word})

    def parse(self, response):
        lis = response.selector.xpath('//ol[@id="searchResults"]/li')
        for li in lis:
            data = {
                "id": li.xpath('./div/@id').extract_first(),
                "url": li.xpath('.//a/@href').extract_first(),
                "title": li.xpath('.//h2//span/text()').extract_first().strip(),
                "price": li.xpath('.//*[@class="price-fraction"]/text()').extract_first(),
                "key_word": response.meta.get("key_word"),
                "date": self.today_date
            }

            yield data

        next_url = response.selector.xpath('//li[@class="pagination__next"]/a/@href').extract_first()
        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse, meta=response.meta)

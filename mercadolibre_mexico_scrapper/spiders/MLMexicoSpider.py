import pkgutil

import scrapy


class MLMexicoSpider(scrapy.Spider):
    name = "mercadolibre.com.mx"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        # binary_string = pkgutil.get_data("mercadolibre", "resources/key_words.txt")
        # self.key_words = binary_string.decode("utf-8").split("\n")
        self.key_words = []
        with open("key_words.txt", "r") as f:
            for line in f:
                self.key_words.append(line[:-1])

        self.details_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Accept-Language": "en",
            "Connection": "keep-alive"
        }

    def start_requests(self):
        urls = ["https://listado.mercadolibre.com.mx/" + key_word for key_word in self.key_words]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        lis = response.selector.xpath('//ol[@id="searchResults"]/li')
        for li in lis:
            data = {
                "id": li.xpath('./div/@id').extract_first(),
                "url": li.xpath('.//a/@href').extract_first(),
                "title": li.xpath('.//h2/a/span/text()').extract_first(),
                "price": li.xpath('.//*[@class="price-fraction"]/text()').extract_first(),
            }

            yield data
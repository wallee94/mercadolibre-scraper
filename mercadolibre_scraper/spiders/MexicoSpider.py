import pkgutil

import re
import scrapy
from datetime import datetime
import requests


class MLMexicoSpider(scrapy.Spider):
    name = "mercadolibre.com.mx"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        binary_string = pkgutil.get_data("mercadolibre_scraper", "resources/key_words.txt")

        self.key_words = binary_string.decode("utf-8").split("\n")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Accept-Language": "en",
            "Connection": "keep-alive"
        }
        self.today_date = str(datetime.now().date())

        params = {
            "currencies": "USD,MXN",
            "format": "1"
        }
        acces_key = "701ab850ba9a3305ad7843cc055bd2c2"
        r = requests.get("http://www.apilayer.net/api/live?access_key=" + acces_key, params=params)
        json_response = r.json()
        self.usd_to_mxn = float(json_response.get("quotes", {}).get("USDMXN", "19.0"))

    def start_requests(self):
        for key_word in self.key_words:
            key_word = re.sub("\r+", "", key_word)
            urls = [
                "https://listado.mercadolibre.com.mx/" + key_word + "_ItemTypeID_N",
                "https://listado.mercadolibre.com.mx/usados/" + key_word
            ]
            for url in urls:
                is_new = "/usados/" not in url
                yield scrapy.Request(url=url,
                                     callback=self.parse,
                                     meta={"key_word": key_word, "page": 1, "last_position": 0, "is_new": is_new},
                                     headers=self.headers)

    def parse(self, response):
        lis = response.selector.xpath('//ol[@id="searchResults"]/li')
        for position, li in enumerate(lis):
            response.meta["last_position"] += 1
            data = {
                "id": li.xpath('./div/@id').extract_first(),
                "url": li.xpath('.//a/@href').extract_first(),
                "title": li.xpath('.//h2//span/text()').extract_first(),
                "price": self.clean_price(li.xpath('.//*[@class="price-fraction"]/text()').extract_first()),
                "key_word": response.meta.get("key_word"),
                "date": self.today_date,
                "position": response.meta.get("last_position"),
                "page": response.meta.get("page"),
                "is_new": response.meta.get("is_new")
            }

            if not data["title"]:
                return
            else:
                data["title"] = data["title"].strip()

            usd_symbol = li.xpath('.//*[@class="price-symbol"]/text()').extract_first()
            if usd_symbol is not None:
                if "U$S" == usd_symbol:
                    data["price"] = str(float(data["price"]) * self.usd_to_mxn)

            yield data

        next_url = response.selector.xpath('//li[@class="pagination__next"]/a/@href').extract_first()
        if next_url and response.meta["page"] < 10:
            response.meta["page"] += 1
            yield scrapy.Request(url=next_url, callback=self.parse, meta=response.meta, headers=self.headers)

    def clean_price(self, text):
        return re.sub(r"[^\w\.]", "", text)

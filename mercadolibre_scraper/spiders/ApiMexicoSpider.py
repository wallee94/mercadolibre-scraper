import pkgutil
import re
from datetime import datetime

import requests
import scrapy
import json


class MLMexicoSpider(scrapy.Spider):
    name = "api-mercadolibre.com.mx"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)

        response = requests.get("https://patopatoganso.com.mx/api/tracking/keywords/",
                                headers={"Authorization": "Token ac52865a0415790e775e2d2e41c86718ccb954d2"})
        if response.status_code == 200:
            self.key_words = response.json().get("keywords", [])
        else:
            binary_string = pkgutil.get_data("mercadolibre_scraper", "resources/key_words_api.txt")
            self.key_words = binary_string.decode("utf-8").split("\n")

        self.headers = {
            "User-Agent": "curl/7.51.0",
            "Accept": "*/*",
        }
        self.today_date = str(datetime.now().date())

        # get actual USD/MXN rate
        params = {
            "currencies": "USD,MXN",
            "format": "1"
        }
        access_key = "701ab850ba9a3305ad7843cc055bd2c2"
        r = requests.get("http://www.apilayer.net/api/live?access_key=" + access_key, params=params)
        json_response = r.json()
        self.usd_to_mxn = float(json_response.get("quotes", {}).get("USDMXN", "19.0"))

    def start_requests(self):
        api_url = "https://api.mercadolibre.com/sites/MLM/search?limit=100"
        for key_word in self.key_words:
            key_word_escaped = re.sub("\s+", "%20", key_word)
            url = api_url + "&q=" + key_word_escaped
            yield scrapy.Request(url=url, headers=self.headers, meta={"key_word": key_word, "base_url": url})

    def parse(self, response):
        response_json = json.loads(response.text)
        for result in response_json.get("results", []):
            data = self.parse_data(result, response)
            if data:
                yield data

        paging = response_json.get("paging")
        limit = paging.get("limit")
        total = paging.get("total")
        offset = paging.get("offset")
        if paging and 0 < limit < total - offset and offset < 1200:
            url = response.meta.get("base_url") + "&offset=" + str(paging.get("offset") + paging.get("limit"))
            yield scrapy.Request(url=url, headers=self.headers, meta=response.meta)

    def parse_data(self, result, response):
        data = {
            "id": result.get("id"),
            "title": result.get("title"),
            "url": result.get("permalink"),
            "date": self.today_date,
            "is_new": result.get("condition") == "new",
            "free_shipping": result.get("shipping", {}).get("free_shipping"),
            "accepts_mercadopago": result.get("accepts_mercadopago"),
            "sold_quantity": result.get("sold_quantity"),
            "available_quantity": result.get("available_quantity"),
            "address": result.get("address", {}).get("city_name") + ", " + result.get("address", {}).get("state_name"),
            "keyword": response.meta.get("key_word")
        }
        if result.get("currency_id") == "MXN":
            data["price"] = result.get("price")
        elif result.get("currency_id") == "USD":
            data["price"] = result.get("price")*self.usd_to_mxn
        else:
            return None

        return data

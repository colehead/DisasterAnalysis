# coding=utf-8

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

import re
import json
import sqlite3
import os

class NationSpider(BaseSpider):
    name = "nation"
    allowed_domains = ["csi.ac.cn"]
    base_url = "http://maps.googleapis.com/maps/api/geocode/json?sensor=true&latlng=%f,%f"
    
    def start_requests(self):
        spider_dir = os.path.dirname(os.path.realpath(__file__))
        settings = self.settings
        self.db_file = "%s/../%s" % (spider_dir, settings.get('DB_FILE'))

        sql = """
        select latitude, longtitude from quake q where not exists 
        (select * from nation n where n.longtitude = q.longtitude and n.latitude = q.latitude)
              """

        start_urls = []
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        for row in c.execute(sql):
            start_urls.append(self.base_url % (row[0], row[1]))

        conn.commit()
        conn.close()

        #yield Request(start_urls[2], self.parse)
        for url in start_urls:
            yield Request(url, self.parse)

    def parse(self, response):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        result = re.search(r"=([\d\.\-]+),([\d\.\-]+)", response.url)
        json_data =  json.loads(response.body)
        if len(json_data["results"]) > 0:
            address = json_data["results"][0]["address_components"]
            for comp in address:
                if len(comp["types"]) > 0 and comp["types"][0] == 'country':
                    nation = comp["short_name"]
                    print result.group(1), result.group(2), nation
                    c.execute("INSERT OR REPLACE INTO nation (latitude, longtitude, nation) VALUES (?,?,?)", 
                                [result.group(1), result.group(2), nation]
                    )
                    break
        conn.commit()


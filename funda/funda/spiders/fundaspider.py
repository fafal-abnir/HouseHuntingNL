import logging

import scrapy
import re
log = logging.getLogger()
def is_useful_dd_class(dd) -> bool:
    dd_class = dd.xpath("@class").extract_first()
    invalid_dd_class = ["object-kenmerken-group-list"]
    return not (dd_class in invalid_dd_class)


def extract_dd_value(dd) -> str:
    if dd.xpath("@class").extract_first() == "fd-flex--bp-m fd-flex-wrap fd-align-items-center":
        return dd.css("span::text").get()
    elif dd.xpath("@class").extract_first() == "fd-flex--bp-m fd-align-items-center":
        return dd.css("::text").get()
    elif dd.xpath("@class").extract_first() == "object-kenmerken-list__asking-price fd-flex fd-align-items-center":
        return dd.css("::text").get()
    if dd.css("span").xpath("@class").extract_first() is not None:
        # return "xxxx"
        if "energielabel" in dd.css("span").xpath("@class").extract_first():
            return dd.css("span::text").get()
    else:
        return dd.css("::text").get()

def extract_dt_value(dt) ->str:
    if dt.xpath(
            "@class").extract_first() == "object-kenmerken-group-header object-kenmerken-group-header-half":
        return dt.css("div::text").get()
    else:
        return dt.css("::text").get()

class FundaScrapper(scrapy.Spider):
    name = "funda"
    custom_settings = {'USER_AGENT': 1}
    # allowed_domains = ['funda.nl']
    # start_urls = ["https://www.funda.nl/en/huur/heel-nederland/"]
    # start_urls = ["https://www.funda.nl/en/koop/heel-nederland/"]
    # start_urls = [
    #     "https://www.funda.nl/en/huur/loon-op-zand/appartement-42804982-hoge-steenweg-37"]
    def start_requests(self):
        yield scrapy.Request(f"https://www.funda.nl/en/{self.mode}/heel-nederland/")
    def parse_list(self, response):
        for item in response.css('div.search-result__header-title-col'):
            a_tag = item.css('a[data-object-url-tracking="resultlist"]')
            yield response.follow(response.urljoin(a_tag.attrib['href']),
                                  callback=self.parse_house)

        # next_page = response.urljoin(
        #     response.css('a[rel="next"]').attrib['href'])
        # if next_page is not None:
        #     yield response.follow(next_page, callback=self.parse)

    def parse_house(self,response):
        dic = {}
        title = response.xpath('//title/text()').extract()[0]
        stats_div = response.css('div.object-statistics').get()
        if stats_div is not None:
            date_on_funda = re.search(r"([1-9]|1[012])/([1-9]|[12][0-9]|3[01])/(19|20)\d\d", stats_div)[0]
            dic["publish_date"] = date_on_funda
        if title is None:
            yield
        postal_code = re.search(r'\d{4} [A-Z]{2}', title).group(0)
        city = re.search(r'\d{4} [A-Z]{2} \w+',title).group(0).split()[2]
        # address = re.findall(r'te koop: (.*) \d{4}',title)[0]
        dic["title"] = title
        dic["postal_code"] = postal_code
        dic["city"] = city

        # dic["address"] = address
        dl_list = response.css("dl.object-kenmerken-list")
        for dl in dl_list:
            dd_list = dl.css("dd")
            valid_dd_list = list(filter(
                lambda dd: is_useful_dd_class(dd),
                dd_list))
            dt_list = dl.css("dt")
            for dt, dd in zip(dt_list, valid_dd_list):
                v = extract_dd_value(dd)
                if v is not None:
                    v = v.strip()
                dic[extract_dt_value(dt).strip()] = v

        yield dic

    # start_urls = ["https://www.funda.nl/en/huur/blaricum/appartement-42848057-prins-hendriklaan-54/"]

    def parse(self, response):
        for item in response.css('div.search-result__header-title-col'):
            a_tag = item.css('a[data-object-url-tracking="resultlist"]')
            yield response.follow(response.urljoin(a_tag.attrib['href']),callback=self.parse_house)
            # yield {
            #     'name': (a_tag.css(
            #         'h2.search-result__header-title.fd-m-none::text').get()).strip(),
            #     'link': response.urljoin(a_tag.attrib['href']),
            # }

        next_page = response.urljoin(response.css('a[rel="next"]').attrib['href'])
        if next_page is not None:
           yield response.follow(next_page, callback=self.parse)

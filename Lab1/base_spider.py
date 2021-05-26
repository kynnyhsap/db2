import pathlib
import scrapy
import re
import xml
from xml.etree import ElementTree
from scrapy.crawler import CrawlerProcess

BASE_PAGE_LINK = 'https://ua.igotoworld.com'
INTERNET_STORE_LINK = 'https://allo.ua'


class BaseSpider(scrapy.Spider):
    name = 'base_spider'
    start_urls = [BASE_PAGE_LINK]

    pages_to_parse = 20
    data_element = ElementTree.Element('data')

    FEEDS = {
        'data.xml': {
            'format': 'xml',
            'encoding': 'utf8',
            'indent': 4,
            # 'fields': ['page'],
        },
    }


    def parse(self, response):
        fragments = []

        # scraping images
        for img in response.xpath('//img'):
            img_url = img.xpath('@src').get()

            fragments.append({
                'tag': 'fragment',
                'attr': {
                    'type': 'image',
                },
                'text': img_url,
            })

        # scraping text
        for text in response.xpath('//text()'):
            string = text.get()
            string = string.strip()
            string = re.sub(r"(\\n|\\t)", '', string)  # remove tabs and new line escape characters

            if len(string) == 0:
                continue

            fragments.append({
                'tag': 'fragment',
                'attr': {
                    'type': 'text',
                },
                'text': string,
            })

        # creating xml
        page_element = ElementTree.Element('page', {'url': response._url})
        for fragment in fragments:
            fragment_element = ElementTree.Element(fragment['tag'], fragment['attr'])
            page_element.append(fragment_element)

        self.data_element.append(page_element)
        print(page_element.tostring())

        # jump to next page
        next_page = response.css('a::attr("href")').get()  # TODO: select with XPath
        if self.pages_to_parse > 0 and next_page is not None:
            self.pages_to_parse -= 1
            yield response.follow(next_page, self.parse)
        else:
            # print(self.data_element)
            ElementTree.ElementTree(self.data_element).write('data.xml')


if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })

    process.crawl(CrawlerProcess)
    process.start()

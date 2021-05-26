import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import xml.etree.cElementTree as ET
from xml.dom import minidom
import random
import re

MAX_PAGES = 20
BASE_PAGE_LINK = 'https://ua.igotoworld.com'


def build_xml(data, filename='data.xml'):
    root = ET.Element('root')
    data_element = ET.SubElement(root, 'data')

    for page in data:
        page_element = ET.SubElement(data_element, 'page', url=page['url'])

        for fragment in page['fragments']:
            fragment_element = ET.SubElement(page_element, 'fragment', type=fragment['type'])
            fragment_element.text = fragment['text']

    # tree = ET.ElementTree(root)
    # tree.write(filename)

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent='\t')
    with open(filename, "w") as f:
        f.write(xmlstr)


def is_tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


class Crawler:
    def __init__(self):
        self.pages_to_parse = MAX_PAGES
        self.pages = []

    def parse(self, url):
        if self.pages_to_parse == 0:
            return
        self.pages_to_parse -= 1

        # TODO: use XPath instead of bs4 find
        try:
            res = requests.get(url)
        except:
            return

        print('Parsing page', url)

        soup = BeautifulSoup(res.text, 'lxml')

        # create page
        page = {
            'url': url,
            'fragments': []
        }

        # find all images
        for img in soup.find_all('img'):
            src = img.get('src')
            page['fragments'].append({
                'type': 'image',
                'text': src,
            })

        # find all text data
        all_text_data = soup.find_all(text=True)
        all_visible_text_data = filter(is_tag_visible, all_text_data)
        for text in all_visible_text_data:
            text = text.strip()
            text = re.sub(r"(\\n|\\t)", '', text)  # remove tabs and new line escape characters

            if text == "":
                continue

            page['fragments'].append({
                'type': 'text',
                'text': text,
            })

        self.pages.append(page)

        # next_page_links = soup.find_all('a')[0].get('href')
        next_page_links = soup.find_all('a')
        next_page_links = list(filter(lambda link: link.get('href') != '#', next_page_links))
        random.shuffle(next_page_links)

        for next_page in next_page_links:
            self.parse(next_page.get('href'))


if __name__ == "__main__":
    crawler = Crawler()

    crawler.parse(BASE_PAGE_LINK)

    # print(crawler.pages)
    build_xml(crawler.pages)
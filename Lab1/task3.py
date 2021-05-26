import requests
from bs4 import BeautifulSoup
import xml.etree.cElementTree as ET
from xml.dom import minidom


ONLINE_STORE_LINK = 'https://allo.ua'


def build_xml(products, filename='products.xml'):
    root = ET.Element('root')
    # products_element = ET.SubElement(root, 'products')
    print(products)

    for product in products:
        product_element = ET.Element('product')

        description_element = ET.Element('description')
        description_element.text = product['description']
        product_element.append(description_element)

        image_element = ET.Element('image')
        image_element.text = product['image']
        product_element.append(image_element)

        price_element = ET.Element('price')
        price_element.text = product['price']
        product_element.append(price_element)

        root.append(product_element)

    # tree = ET.ElementTree(root)
    # tree.write(filename)

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent='\t')
    with open(filename, "w") as f:
        f.write(xml_str)


def parse(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')

    products_list = []
    products = soup.find_all('div', {'class': 'h-pc'})
    for product in products:
        price_div = product.find('div', {'class': 'v-price-box__cur'})
        if price_div is None:
            continue

        price = price_div.text
        image = product.find('img', {'class': 'h-pc__image'}).get('data-src')
        description = product.find('a', {'class': 'h-pc__title'}).text

        print(price, description, image)

        products_list.append({
            'description': description,
            'image': image,
            'price': price
        })

    return products_list


if __name__ == "__main__":
    build_xml(parse(ONLINE_STORE_LINK))

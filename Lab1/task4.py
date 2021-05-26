from lxml import etree

dom = etree.parse('products.xml')
xslt = etree.parse('products.xsl')

transform = etree.XSLT(xslt)

new_dom = transform(dom)
html_string = etree.tostring(new_dom, pretty_print=True).decode("utf-8")

with open('products.html', "w") as f:
    f.write(html_string)

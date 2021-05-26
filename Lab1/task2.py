import xml.etree.ElementTree as ET

root = ET.parse('data.xml').getroot()

images_counts = []
for page in root.findall('data/page'):
    images = page.findall('fragment[@type="image"]')

    total_images = len(images)
    images_counts.append(total_images)

average_images_count = round(sum(images_counts) / len(images_counts), 1)

print('Average images count', average_images_count)

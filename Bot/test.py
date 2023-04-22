import requests

img_data = requests.get('http://site.meishij.net/r/58/25/3568808/a3568808_142682562777944.jpg').content
with open('../data/images/image_name.jpg', 'wb') as handler:
    handler.write(img_data)
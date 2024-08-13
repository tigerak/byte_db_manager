import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
# modules
from app.config import *

def print_element_tree(element, indent=""):
    print(f"{indent}Tag: {element.tag}, Attributes: {element.attrib}")
    for child in element:
        print_element_tree(child, indent + "    ")

for rss_url in YTN_RSS:

    response = requests.get(rss_url)

    if response.status_code == 200:
        root = ET.fromstring(response.content)

        # channel 태그 내부의 item 태그들 탐색
        print(len(root.findall('channel')))
        for channel in root.findall('channel'):
            items = channel.findall('item')
            print(len(items))
            

    #     # 최대 가져올 item 태그의 개수 설정
    #     max_items = 2
    #     item_count = 0

    #     # channel 태그 내부의 item 태그들 탐색
    #     for channel in root.findall('channel'):
    #         for item in channel.findall('item'):
    #             # item 태그 정보를 출력 (또는 원하는 작업 수행)
    #             print(ET.tostring(item, encoding='unicode'))

    #             # item 개수 제한
    #             item_count += 1
    #             if item_count >= max_items:
    #                 break
    #         if item_count >= max_items:
    #             break
    # else:
    #     print(f"Failed to retrieve RSS feed: {response.status_code}")

    # print_element_tree(root)
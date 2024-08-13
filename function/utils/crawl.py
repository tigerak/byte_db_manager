import os
import json
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup as bs
import urllib3
from urllib3.util.ssl_ import create_urllib3_context
from datetime import datetime, timedelta
# modules
from function.db_manager import ChromaManager

def url_scrap(latest_date_str, ytn_url):
    
    ctx = create_urllib3_context()
    ctx.load_default_certs()
    ctx.options |= 0x4 # ssl.OP_LEGACY_SERVER_CONNECT
    
    total_today_content = {}
    total_content_num = 0
    for base_url in ytn_url:
        next_page = 1
        complete_switch = 1

        while complete_switch != -1:

            target_url = base_url + str(next_page)
        
            with urllib3.PoolManager(ssl_context=ctx) as http:
                req = http.request("GET", target_url)
            
            soup = bs(req.data, 'html.parser')

            time_list = soup.select('#container > div > div > div.section01 > section > div.list-type038 > ul > li > div > div.info-box01 > span.txt-time')
            title_list = soup.select('#container > div > div > div.section01 > section > div.list-type038 > ul > li > div > div.news-con > a > strong')
            url_list = soup.select('#container > div > div > div.section01 > section > div.list-type038 > ul > li > div > div.news-con > a')

            # today = str(datetime.today().strftime('%m-%d'))
            # yesterday = datetime.today() - timedelta(1)
            # total_article_path = r'/home/data_ai/Project/function/data/total_article.json'
            # 마지막 수집 날짜 조회
            # if os.path.exists(total_article_path):
            #     with open(total_article_path, 'r', encoding='utf-8') as f:
            #         total_article = json.load(f)
            #     article_dates = {data['article_date'] for data in total_article.values()}
            #     datetime_format = '%Y-%m-%d %H:%M'
            #     datetime_objects = [datetime.strptime(date_str, datetime_format) for date_str in article_dates]
            #     latest_datetime = max(datetime_objects)
            #     # 가장 최신의 datetime 객체를 다시 문자열로 변환
            #     latest_date_str = latest_datetime.strftime(datetime_format)
            #     # Db저장된 날짜는 '2024-07-16 17:35'이므로 연도 제거
            #     latest_date_str = latest_date_str.split('-', 1)[1]
            
            
            page_content_num = len(time_list)

            for idx in range(page_content_num):
                time = time_list[idx].get_text()
                url = url_list[idx].get('href')
                title = title_list[idx].get_text()
                
                if time >= latest_date_str:
                    total_today_content[total_content_num] = {'time': '', 'title':'', 'url': ''}
                    total_today_content[total_content_num]['time'] = time
                    total_today_content[total_content_num]['url'] = url
                    total_today_content[total_content_num]['title'] = title
                    total_content_num += 1
                elif time < latest_date_str:
                    complete_switch = -1
                    break
                sleep(0.02)

            if complete_switch == 1:
                next_page = next_page + 1
            elif complete_switch == -1:
                next_page = -1
            print(next_page)

    return total_today_content
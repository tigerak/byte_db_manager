import os
import re
import json
from time import sleep
from tqdm import tqdm
import hashlib
import requests
# torch
import torch
# modules
from function.utils.crawl import url_scrap
from function.utils.scrap import Scraping
from function.longformer import Longformer
from app.config import MODEL_API_ADDRESS

class ytn_manager():
    def ytn_crawling(self, chromadb, using_summary=False):

        scrap = Scraping()
        longformer = Longformer()

        try:
            latest_date_str, latest_set_num = chromadb.get_most_recent_date_and_setnum()
            if latest_date_str == 'None':
                latest_date_str = '07-15 06:00'# '07-15 06:00'
                latest_set_num = 0
            print(f"마지막 날짜 : {latest_date_str}, 마지막 번호 : {latest_set_num}")
        except:
            print(f"날짜를 가져오는데 문제가 생김 :[")
            print(latest_date_str, latest_set_num)

        # 최신 기사 수집
        total_today_content = url_scrap(latest_date_str)
        # 시간의 오름차순으로 정렬
        content_list = list(total_today_content.values())
        sorted_content_list = sorted(content_list, key=lambda item: item['time'])
        # 
        for content in tqdm(sorted_content_list):
            input_url = content['url']
            media, title, article, article_date = scrap.scraping(input_url=input_url)

            check_sign = self._remove_unfulfilled_article(title, article, input_url)
            # DB에 저장 및 json 만들기
            if check_sign:
                # 요약문 사용 유무 선택
                if not using_summary:
                    tenser_embedding = longformer.inference(article)
                    summary_title = ''
                    summary = ''
                    summary_reason = ''
                    
                elif using_summary:
                    data = {
                            'titleDiv': title,
                            'dateDiv': article_date,
                            'articleDiv': article
                        }
                    response = requests.post(MODEL_API_ADDRESS, data=data)
                    response = response.json()

                    summary_title = response['summary_title']
                    summary = response['summary']
                    summary_reason = response['summary_reason']
                    main = response['main']
                    sub = response['sub']
                    major_class = response['major_class']
                    medium_class = response['medium_class']

                    tenser_embedding = longformer.inference(summary)

                embedding = torch.squeeze(tenser_embedding).tolist()  # 2차원 텐서를 리스트로 변경해서 chromadb에 저장.
                search_date = article_date.split(' ')[0].strip()
                respons = chromadb.search(embedding=embedding,
                                          search_date=search_date)
                set_list = []
                for k, data in enumerate(respons):
                    if data['distances'] < 20:
                        print(f"{k}번 - 유사도 : {round(data['distances'], 3)}")
                        print(f"URI : {data['metadata']['url'].strip()}")
                        print(f"기사 제목 : {data['metadata']['title']}")
                        print(f"요약문 : {data['metadata']['summary']}")
                        print(f"송고 시간 : {data['metadata']['article_date'].strip()}")
                        print(f"세트 번호 : {data['metadata']['set_num']}") # 세트 번호는 int
                        print(f"DB ID : {data['ids']}\n")
                        set_list.append(data['metadata']['set_num'])
                        
                # latest_set_num 사용 및 갱신
                if len(set_list) != 0:
                    set_num = max(set_list)
                    print(f"세트 번호 리스트에 다른 종류? {set_list}")
                elif len(set_list) == 0:
                    set_num = latest_set_num + 1
                    latest_set_num = set_num
                
                # DB에 저장
                chromadb.add_or_update(embedding, media, input_url,
                                       title, article, article_date, 
                                       summary_title, summary, summary_reason, 
                                       main, sub, major_class, medium_class,
                                       set_num)
                
            sleep(0.2)

        print(f"데이터가 DB에 저장되었습니다.{chromadb.get_most_recent_date_and_setnum()}")


    def _remove_unfulfilled_article(self, title, article, input_url):
        sign = False

        localname_pattern = re.compile(r'^\[.*소식\]')
        stock_pattern = re.compile(r'^국고채 금리 장중.*3년물.*')
        exchange_pattern = re.compile(r'^외국환시세\(.*\)')

        if title.startswith('[게시판]'):
            print('게시판 : ', title, input_url)
        elif title.startswith('[연합뉴스 이 시각 헤드라인]'):
            print('헤드라인 : ', title, input_url)
        elif title.startswith('[외환]'):
            print('외환 : ', title, input_url)
        elif title.startswith('[인사]'):
            print('인사 : ', title, input_url)
        elif title.startswith('[속보]'):
            print('속보 : ', title, input_url)
        elif title.startswith('[1보]'):
            print('1보 : ', title, input_url)
        elif localname_pattern.match(title):
            print('지역명소식 : ', title, input_url)
        elif stock_pattern.match(title):
            print('국고채 : ', title, input_url)
        elif exchange_pattern.match(title):
            print('외국환 : ', title, input_url)

        elif article.startswith('▲'):
            print('삼각형 : ', title, input_url)
        elif len(article.split('다.')) < 3:
            print('두문장: ', title, input_url)

        else:
            sign = True

        return sign

    def _make_id(self, article):
        
        article_id = hashlib.sha256(article.encode('utf-8')).hexdigest()
        
        return article_id
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
from config import *
from gpt_data.main import MakePrompt
from gpt_data.utils.gpt_api import GPT

class ytn_manager():
    def ytn_crawling(self, chromadb, using_summary=False):

        scrap = Scraping()
        longformer = Longformer()

        try:
            latest_date_str, latest_set_num, most_recent_index, article_date_dt_raw = \
                                                chromadb.get_most_recent_items()
            if latest_date_str == 'None':
                latest_date_str = '08-01 06:00'# '07-15 06:00'
                latest_set_num = 0
                most_recent_index = 0
            print(f"마지막 날짜 : {latest_date_str}, 마지막 세트 : {latest_set_num}, 마지막 번호{most_recent_index}")
        except:
            print(f"날짜를 가져오는데 문제가 생김 :[")
        tmp_date = article_date_dt_raw.split(' ')[0]  
        print(f"임시 마지막 날짜: {tmp_date}")

        # 웹 기사 수집
        ytn_url = [r'https://www.yna.co.kr/industry/all/',
                   r'https://www.yna.co.kr/market-plus/all/']
        total_today_content = url_scrap(latest_date_str, ytn_url)

        # 시간의 오름차순으로 정렬
        content_list = list(total_today_content.values())
        sorted_content_list = sorted(content_list, key=lambda item: item['time'])
        
        # 
        for _, content in tqdm(enumerate(sorted_content_list), 
                               total=len(sorted_content_list)):
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
                    main = ''
                    sub = ''
                    major_class = ''
                    medium_class = ''
                
                # 전부 요약문 사용함.
                elif using_summary:
                    data = {
                            'titleDiv': title,
                            'dateDiv': article_date,
                            'articleDiv': article
                        }
                    error_count=0
                    try:
                        result = requests.post(BROKER_API_ADDRESS, data=data)
                        result = result.json()
                        print(result)
                    except:
                        while error_count < 2:
                            error_count += 1
                            sleep(15)
                            print("한 번 더 !!")
                            result = requests.post(BROKER_API_ADDRESS, data=data)
                            result = result.json()

                    task_id = result['task_id']
                    print(task_id)
                    sleep(0.2)
                    response = {'status' : ''}
                    while response['status'] != 'success':
                        response = requests.post(JOB_API_ADDRESS + task_id)
                        response = response.json()
                        print(response['message'])
                        sleep(5)
                    
                    # JSON으로 직렬화한 걸 다시 json으로
                    result_str = response['result']
                    result_dict = json.loads(result_str) # str -> json
                    print(result_dict)

                    # 사회 및 경제 5개 외 필터
                    major_class = result_dict['major_class']
                    medium_classes = result_dict['medium_class'].split(',')
                    valid_medium_classes = ['주식', '금리', '물가', '환율', '부동산']
                    # "사회"인 항목은 버림
                    if major_class == "사회":
                        print("사회 삭제")
                        continue
                    # "경제"인 항목 중에서 주어진 리스트에 포함되지 않는 항목은 버림
                    if major_class == "경제":
                        if not any(mc in medium_classes for mc in valid_medium_classes):
                            print("경제 5개 외 삭제")
                            continue
                    
                    summary_title = result_dict['summary_title']
                    summary = result_dict['summary']
                    summary_reason = result_dict['summary_reason']
                    main = result_dict['main']
                    sub = result_dict['sub']
                    major_class = result_dict['major_class']
                    medium_class = result_dict['medium_class']

                    tenser_embedding = longformer.inference(summary)

                # 2차원 텐서를 리스트로 변경해서 chromadb에 입력.
                embedding = torch.squeeze(tenser_embedding).tolist()
                search_date = article_date.split(' ')[0].strip()
                search_result = chromadb.search(embedding=embedding,
                                          search_date=search_date)
                threshold = 0.18
                set_list = []
                for k, data in enumerate(search_result):
                    if data['distance'] < threshold:
                        print(f"{k}번 - 유사도 : {round(data['distance'], 3)}")
                        print(f"URI : {data['metadata']['url'].strip()}")
                        print(f"기사 제목 : {data['metadata']['title']}")
                        print(f"요약문 : {data['metadata']['summary']}")
                        print(f"송고 시간 : {data['metadata']['article_date'].strip()}")
                        print(f"세트 번호 : {data['metadata']['set_num']}") 
                        print(f"DB ID : {data['id']}\n")
                        similarity = f"{data['metadata']['index']}->{data['metadata']['set_num']}->{data['distance']}"
                        set_list.append(similarity)
                        
                # 매일 Set Num 0으로 초기화
                if tmp_date != search_date:
                    latest_set_num = 0
                    tmp_date = search_date
                # latest_set_num 사용 및 갱신 -> 가장 유사도 높은 set_num으로 !
                if len(set_list) != 0:
                    set_num = -1
                    tmp_similarity = 20.
                    for i, set in enumerate(set_list):
                        set = set.split('->')
                        if float(set[2]) < tmp_similarity:
                            tmp_similarity = float(set[2])
                            set_num = int(set[1])
                    print(f"세트 번호 리스트에 다른 종류? {set_list}")
                elif len(set_list) == 0:
                    set_num = latest_set_num + 1
                    latest_set_num = set_num

                # set_list -> str로 바꿔서 저장. 
                set_list = ', '.join(set_list)

                most_recent_index += 1
                
                # DB에 저장
                chromadb.add_or_update(index=most_recent_index, 
                                       embedding=embedding, 
                                       media=media, 
                                       url=input_url,
                                       title=title, 
                                       article=article, 
                                       article_date=article_date, 
                                       summary_title=summary_title, 
                                       summary=summary, 
                                       summary_reason=summary_reason, 
                                       main=main, 
                                       sub=sub, 
                                       major_class=major_class, 
                                       medium_class=medium_class,
                                       set_num=set_num, 
                                       set_list=set_list)
                
                # 날짜 + set_mum 일치 항목 검색
                set_num_document = chromadb.get_by_setnum_date(set_num=set_num,
                                                            search_date=search_date)
                tmp_part_list = []
                matching_ids = []
                for i, doc in enumerate(set_num_document):
                    # Summary 추가
                    content = doc['metadata']['summary']
                    tmp_part = f"{i+1}번 기사:\n{content}\n"
                    tmp_part_list.append(tmp_part)
                    # id 추가
                    matching_ids.append(doc['id'])
                part_prompt = ''.join(tmp_part_list)
                # Prompt 생성
                mp = MakePrompt()
                prompt = mp._base_prompt(part_prompt)
                # GPT4o - Keyword 및 한 줄 설명 생성 
                gpt = GPT()
                keyword, description = gpt.api_make_keyword(set_num_prompt=prompt)
                print(f"- 키워드 : {keyword} - 설명 : {description}")
                # Keyword 업데이트
                chromadb.update_keyword(matching_ids=matching_ids,
                                            keyword=keyword,
                                            description=description)
                
            sleep(0.2)

        print(f"데이터가 DB에 저장되었습니다.{chromadb.get_most_recent_items()}")

        # 


    # 기사 제목에서 필요 없는 기사들 1차 필터링
    def _remove_unfulfilled_article(self, title, article, input_url):
        sign = False

        localname_pattern = re.compile(r'^\[.*소식\]')
        pick_pattern = re.compile(r'^\[픽! .+\]')
        stock_pattern = re.compile(r'^국고채 금리.*연 \d+%$')
        exchange_pattern = re.compile(r'^외국환시세\(\d+월\d+일·.*')
        kos_pattern = re.compile(r'^\[코스피·코스닥 전 거래일\(\d+일\) 주요공시\]')
        
        if title.startswith('[게시판]'):#
            print('게시판 : ', title, input_url)
        elif title.startswith('[외환]'):#
            print('외환 : ', title, input_url)
        elif title.startswith('[인사]'):#
            print('인사 : ', title, input_url)
        elif title.startswith('[부고]'):#
            print('부고 : ', title, input_url)
        elif title.startswith('[속보]'):#
            print('속보 : ', title, input_url)
        elif title.startswith('[1보]'):#
            print('1보 : ', title, input_url)
        elif title.startswith('[코스피]'):#
            print('코스피 : ', title, input_url)
        elif title.startswith('[코스닥]'):#
            print('코스닥 : ', title, input_url)
        elif title.startswith('[표]'): #
            print('표 : ', title, input_url)
        elif title.startswith('[동정]'): #
            print('동정 : ', title, input_url)
        elif title.startswith('[르포]'): #
            print('르포 : ', title, input_url)
        elif title.startswith('[사이테크+]'): #
            print('사이테크+ : ', title, input_url)
        elif stock_pattern.match(title):
            print('국고채 : ', title, input_url)
        elif exchange_pattern.match(title):
            print('외국환 : ', title, input_url)
        elif kos_pattern.match(title):
            print('코스피코스닥 : ', title, input_url)
        elif pick_pattern.match(title):
            print('픽! : ', title, input_url)

        elif title.startswith('[연합뉴스 이 시각 헤드라인]'):
            print('헤드라인 : ', title, input_url)
        elif localname_pattern.match(title):
            print('지역명소식 : ', title, input_url)
        

        elif article.startswith('▲'):
            print('삼각형 : ', title, input_url)
        elif len(article.split('다.')) <= 3:
            print('두문장: ', title, input_url)

        else:
            sign = True

        return sign

    def _make_id(self, article):
        
        article_id = hashlib.sha256(article.encode('utf-8')).hexdigest()
        
        return article_id
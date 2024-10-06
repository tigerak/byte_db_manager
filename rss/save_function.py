import json
from time import sleep
import requests
# Torch
import torch
# modules
from config import *
from function.news_manager import ytn_manager
from function.db_manager import ChromaManager
from function.longformer import Longformer
from gpt_data.main import MakePrompt
from gpt_data.utils.gpt_api import GPT


class Save_function():
    def __init__(self):
        collection_name = 'ytn_data'
        self.chromadb = ChromaManager(collection_name)
        self.ytn = ytn_manager()
        self.longformer = Longformer()
        self.make_prompt = MakePrompt()
        self.gpt = GPT()

        try:
            (self.latest_date_str, 
             self.latest_set_num, 
             self.most_recent_index, 
             self.most_recent_date_raw) = self.chromadb.get_most_recent_items()
            if self.latest_date_str == 'None':
                self.latest_date_str = '08-01 06:00'# '07-15 06:00'
                self.latest_set_num = 0
                self.most_recent_index = 0
            print(f"마지막 날짜 : {self.latest_date_str}, 마지막 세트 : {self.latest_set_num}, 마지막 번호{self.most_recent_index}")
        except:
            print(f"날짜를 가져오는데 문제가 생김 :[")
        self.tmp_date = self.most_recent_date_raw.split(' ')[0]  # '%Y-%m-%d %H:%M'
        print(f"임시 마지막 날짜: {self.tmp_date}")

        # 마지막 송고시간에 해당하는 모든 제목 가져오기
        search_time = self.most_recent_date_raw.rsplit(':', 1)[0]
        # 마지막 시간 기사 제목들 가져오기.
        self.recent_title_list = self.chromadb.get_most_recent_titles(search_date=self.tmp_date, 
                                                                      search_time=search_time)
        print(f"마지막 시간 : {search_time}")
        print(f"마지막 제목들 : {self.recent_title_list}")


    def prepare_article(self, different_data):
        
        for item in different_data:
            check_sign = False
            # 기사 제목에서 필요 없는 기사들 1차 필터링
            check_sign = self.ytn._remove_unfulfilled_article(
                                                        title=item['title'],
                                                        article=item['article'],
                                                        input_url=item['input_url']
                                                        )
            # check_sign == False가 기본으로 잘 잡혀있는지 확인 할 것
            if check_sign:
                
                try: 
                    ### 임시 필터 - 같은 제목 기사 존재 확인 ###
                    search_date = item['article_date'].split(' ')[0]
                    search_title = item['title']
                    same_title_result = self.chromadb.search_same_title(
                                                            search_date=search_date,
                                                            search_title=search_title
                                                            )
                    if len(same_title_result) > 0:
                        
                        ### 임시 필터 추가 - 본문도 같은 경우 무시 ###
                        article_id = self.chromadb._make_id(article=item['article'])
                        if article_id == same_title_result[0]['id']:
                            print(f"같은 제목, 같은 내용의 기사가 {len(same_title_result)}개 있음.\n옛 기사 제목 : {same_title_result[0]['title']}\n새 기사 제목 : {search_title}")
                            continue
                        else :
                            print(f"같은 제목이지만 내용이 다름 -> 요약 시작")
                except:
                    print("같은 이름 작업 중 문제가 생겼습니다 !!")
                    
                # 요약 모델 API로 보내는 형식
                api_data = {
                        'titleDiv': item['title'],
                        'dateDiv': item['article_date'],
                        'articleDiv': item['article']
                    }
                # 브로커 서버로 전송
                result = self.send_broker(article_date=item['article_date'],
                                          input_url=item['input_url'],
                                          api_data=api_data)
                # 대/중 분류로 필터링
                if result["message"] == '사회':
                    continue
                elif result["message"] == "경제 5개 외":
                    continue
                else:
                    # 키워드 생성
                    self.keyword_update(set_num=result['set_num'], 
                                        search_date=result['search_date'])
            else:
                continue
            
            sleep(0.2)
    
    # 브로커 서버로 전송
    def send_broker(self, article_date, input_url, api_data):
        # yy-mm-dd 만 추출
        search_date = article_date.split(' ')[0].strip()
        
        # 브로커 서버의 @bp.route('/model_broker', methods=['POST']) 로 전송
        result = requests.post(BROKER_API_ADDRESS, data=api_data)
        result = result.json()
        # print(result)
        
        # task_id 받아오기
        task_id = result['task_id']
        # print(task_id)
        sleep(0.2)
        # 브로커 서버의 @bp.route('/job_result/<job_id>', methods=['POST']) 로 전송
        response = {'status' : ''}
        while response['status'] != 'success':
            response = requests.post(JOB_API_ADDRESS + task_id)
            response = response.json()
            # print(response['message'])
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
            return {"message": "사회"}
        # "경제"인 항목 중에서 주어진 리스트에 포함되지 않는 항목은 버림
        if major_class == "경제":
            if not any(mc in medium_classes for mc in valid_medium_classes):
                print("경제 5개 외 삭제")
                return {"message": "경제 5개 외"}
        
        ### Summary Title이 기존과 똑같으면 GPT4로 보내서 새 제목 받아오기 ###
        summary_title = result_dict['summary_title']
        summary = result_dict['summary']
        same_summary_title = self.chromadb.search_same_summary_title(
                                                    search_date=search_date,
                                                    summary_title=summary_title
                                                    )
        if len(same_summary_title) > 0:
            summary_title = self.new_summary_title(summary)
            print(f"같은 요약문 제목 발견 :\n기존 요약문 제목 : {result_dict['summary_title']}\n수정 요약문 제목 : {summary_title}")

        summary_reason = result_dict['summary_reason']
        main = result_dict['main']
        sub = result_dict['sub']
        major_class = result_dict['major_class']
        medium_class = result_dict['medium_class']

        # 2차원 텐서를 리스트로 변경해서 chromadb에 입력.
        tenser_embedding = self.longformer.inference(summary)
        embedding = torch.squeeze(tenser_embedding).tolist()

        # 유사도 검색
        search_result = self.chromadb.search(embedding=embedding,
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

        # latest_set_num 사용 및 갱신 -> 가장 유사도 높은 set_num으로 !
        # search_date가 tmp_date보다 작으면 search_date의 마지막 set_num 가져오기.
        # search_date가 tmp_date와 같으면 그대로 진행
        # search_date가 tmp_date보다 크면 lastest_set_num = 0 (미래 기사가 나올 수 없기 때문)
        # 매일 Set Num 0으로 초기화
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
            if self.tmp_date < search_date:
                self.latest_set_num = 0
                self.tmp_date = search_date
                set_num = self.latest_set_num + 1
                self.latest_set_num = set_num
            elif self.tmp_date > search_date:
                tmp_last_set_num = self.chromadb.get_tmp_last_setnum(search_date)
                set_num = tmp_last_set_num + 1
            elif self.tmp_date == search_date:
                set_num = self.latest_set_num + 1
                self.latest_set_num = set_num        
        
        # set_list -> str로 바꿔서 저장. 
        set_list = ', '.join(set_list)

        self.most_recent_index += 1
        
        # DB에 저장
        self.chromadb.add_or_update(index=self.most_recent_index, 
                                    embedding=embedding, 
                                    media='연합뉴스', 
                                    url=input_url,
                                    title=api_data['titleDiv'], 
                                    article=api_data['articleDiv'], 
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
        return {"message": "저장 완료",
                "set_num": set_num,
                "search_date": search_date}
            
    # 같은 군집에 새 기사 등록 시, 같은 세트 넘버의 모든 기사에 대한 키워드 갱신.
    def keyword_update(self, set_num, search_date):
        # 날짜 + set_mum 일치 항목 검색.
        set_num_document = self.chromadb.get_by_setnum_date(set_num=set_num,
                                                    search_date=search_date)
        tmp_part_list = []
        matching_ids = []
        for i, doc in enumerate(set_num_document):
            print(f"유사 기사 제목들 : {doc['metadata']['summary_title']}")
            # Summary 추가
            content = doc['metadata']['summary']
            tmp_part = f"{i+1}번 요약문:\n{content}\n"
            tmp_part_list.append(tmp_part)
            # id 추가
            matching_ids.append(doc['id'])
        part_prompt = ''.join(tmp_part_list)
        # Prompt 생성
        prompt = self.make_prompt._base_prompt(part_prompt)
        # GPT4o - Keyword 및 한 줄 설명 생성 
        keyword, description = self.gpt.api_make_keyword(set_num_prompt=prompt)
        print(f"- 키워드 : {keyword} - 설명 : {description}")
        # Keyword 업데이트
        self.chromadb.update_keyword(matching_ids=matching_ids,
                                     keyword=keyword,
                                     description=description)
        
    # 동일한 요약문 제목 존재 시 GPT4에서 새 제목 얻어오는 함수.
    def new_summary_title(self, summary):
        prompt = self.make_prompt._new_summary_title_prompt(summary=summary)
        # print(f"푸롬푸트 : {prompt}")
        result = self.gpt.api_make_new_summary_title(prompt=prompt)
        return result
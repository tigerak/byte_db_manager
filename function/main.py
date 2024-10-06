import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)

from time import time
# torch
import torch
# modules
from function.news_manager import ytn_manager
from function.db_manager import ChromaManager
from function.longformer import Longformer
from gpt_data.main import MakePrompt
from gpt_data.utils.gpt_api import GPT


class ytn_data():
    def __init__(self):
        collection_name = 'ytn_data'
        self.collection_name = collection_name
        self.ytn = ytn_manager()
        self.chromadb = ChromaManager(collection_name)


    def new(self):
        # 데이터 전부 삭제
        # self.chromadb.delete_collection(method='delete_all_data') # delete_all_data, delete_collection
        # self.chromadb = ChromaManager(self.collection_name) # delete_collection용


        self.ytn.ytn_crawling(chromadb=self.chromadb, using_summary=True)


    def renewal_similarity(self):
        from tqdm import tqdm
        from time import sleep
        import json
        
        longformer = Longformer()

        # ############################## 인덱스 갱신 ##############################
        # print("index 갱신")
        # all_documents = self.chromadb.export_all()
        # sorted_documents = sorted(all_documents, key=lambda x: x['metadata']['article_date'])

        # for new_index, document in tqdm(enumerate(sorted_documents), total=len(sorted_documents)):
        #     document['metadata']['index'] = new_index + 1  # 1부터 시작하는 새로운 index 부여
        #     # 업데이트된 index를 DB에 저장

        #     tenser_embedding = longformer.inference(document['metadata']['summary'])
        #     embedding = torch.squeeze(tenser_embedding).tolist()

        #     collection = self.chromadb.temp()
        #     collection.upsert(
        #         ids=[document['id']],
        #         embeddings=[embedding], 
        #         documents=[document['document']],
        #         metadatas=[document['metadata']]
        #     )
        # print("인덱스가 날짜 순으로 다시 부여되었습니다.")
        # print("index 갱신 완료")
        # ######################################################################
        
        file_path = r"./ytn_backup.json"
        # ############################## 모든 데이터 저장 ##############################
        # all_documents = self.chromadb.export_all()
        # sorted_documents = sorted(all_documents, key=lambda x: x['metadata']['article_date'])
        # print("모든 데이터 시간 오름차순 정렬정렬")
        
        # with open(file_path, 'w', encoding='utf-8') as f:
        #     json.dump(sorted_documents, f, ensure_ascii=False, indent=4)
        # print(f"데이터가 {file_path}에 저장되었습니다.")
        # ######################################################################
        
        # ############################## 대분류 중분류 필터 ##############################
        # with open(file_path, 'r', encoding='utf-8') as f:
        #     sorted_documents = json.load(f)

        # # 필터링 조건 설정
        # valid_medium_classes = ['주식', '금리', '물가', '환율', '부동산']

        # # 필터링된 데이터를 저장할 리스트
        # filtered_data = []

        # # 데이터 필터링
        # for item in sorted_documents:
        #     major_class = item['metadata']['major_class']
        #     medium_classes = item['metadata']['medium_class'].split(',')

        #     # "사회"인 항목은 버림
        #     if major_class == "사회":
        #         continue

        #     # "경제"인 항목 중에서 주어진 리스트에 포함되지 않는 항목은 버림
        #     if major_class == "경제":
        #         if not any(mc in medium_classes for mc in valid_medium_classes):
        #             continue

        #     # 나머지 항목은 필터링된 데이터에 추가
        #     filtered_data.append(item)

        # with open(file_path, 'w', encoding='utf-8') as f:
        #     json.dump(filtered_data, f, ensure_ascii=False, indent=4)
        # print(f"데이터가 {file_path}에 저장되었습니다.")
        # ######################################################################

        # ############################## 데이터 전부 삭제 ##############################
        # # delete_all_data, delete_collection
        # self.chromadb.delete_collection(method='delete_all_data') 
        # # self.chromadb = ChromaManager(self.collection_name)
        # ######################################################################

        threshold = 0.18
        tmp_date = ''
        latest_set_num = 0
        ############################## 임계치 갱신 ##############################
        with open(file_path, 'r', encoding='utf-8') as f:
            sorted_documents = json.load(f)
        
        for document in tqdm(sorted_documents):
            search_date = document['metadata']['article_date'].split(' ')[0]  # 날짜만 가져옴
            
            # 요약문 임베딩 
            tenser_embedding = longformer.inference(document['metadata']['summary'])
            embedding = torch.squeeze(tenser_embedding).tolist()
            
            response = self.chromadb.search(embedding=embedding, 
                                            search_date=search_date)
            
            set_list = []
            for k, data in enumerate(response):
                if (data['distance'] < threshold) and (data['distance'] != 0.) :
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
                if tmp_date < search_date:
                    latest_set_num = 0
                    tmp_date = search_date
                    set_num = latest_set_num + 1
                    latest_set_num = set_num
                elif tmp_date > search_date:
                    tmp_last_set_num = self.chromadb.get_tmp_last_setnum(search_date)
                    set_num = tmp_last_set_num + 1
                elif tmp_date == search_date:
                    set_num = latest_set_num + 1
                    latest_set_num = set_num

            # set_list -> str로 바꿔서 저장. 
            set_list = ', '.join(set_list)

            
            # DB에 저장
            self.chromadb.add_or_update(index=document['metadata']['index'], 
                                       embedding=embedding, 
                                       media=document['metadata']['media'], 
                                       url=document['metadata']['url'],
                                       title=document['metadata']['title'], 
                                       article=document['document'], 
                                       article_date=document['metadata']['article_date'], 
                                       summary_title=document['metadata']['summary_title'], 
                                       summary=document['metadata']['summary'], 
                                       summary_reason=document['metadata']['summary_reason'], 
                                       keyword=document['metadata']['keyword'],
                                       description=document['metadata'].get('description', ''),
                                       main=document['metadata']['main'], 
                                       sub=document['metadata']['sub'], 
                                       major_class=document['metadata']['major_class'], 
                                       medium_class=document['metadata']['medium_class'],
                                       set_num=set_num, 
                                       set_list=set_list)
            sleep(0.1)
            ######################################################################

            ############################## 키워드 추가 코드 ##############################
            # 날짜 + set_mum 일치 항목 검색
            set_num_document = self.chromadb.get_by_setnum_date(set_num=set_num,
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
            self.chromadb.update_keyword(matching_ids=matching_ids,
                                         keyword=keyword,
                                         description=description)
            ######################################################################

        
        
    def api_test(self):
        # 경제 뉴스
        top_tag = '경제 뉴스'
        middle_tag = '주식'
        search_date = '2024-08-07'

        response = self.chromadb.get_by_medium_date(top_tag, middle_tag, search_date)
        print(response)

        # # 기업 키워드
        # from datetime import datetime

        # main_tag = '삼성전자'
        # search_date = '2024-08-07'

        # response = self.chromadb.get_by_main_date(main_tag=main_tag,
        #                                         search_date=search_date)
        # grouped_results = []

        # for item in response:
        #     id = item.get('id')
        #     keyword = item.get('keyword')
        #     summary_title = item.get('summary_title')
        #     article_date = item.get('article_date')
            
        #     # 기존에 같은 keyword가 있는지 찾기
        #     existing_keyword = next((group for group in grouped_results if group['keyword'] == keyword), None)
            
        #     if existing_keyword:
        #         existing_keyword['items'].append({
        #             'id': id,
        #             'summary_title': summary_title,
        #             'article_date': article_date
        #         })
        #     else:
        #         grouped_results.append({
        #             'keyword': keyword,
        #             'items': [{
        #                 'id': id,
        #                 'summary_title': summary_title,
        #                 'article_date': article_date
        #             }]
        #         })

        # # 각 키워드 내에서 summary_title을 최신 시간 기준으로 정렬
        # for group in grouped_results:
        #     group['items'] = sorted(group['items'], key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

        # # 키워드를, 그 키워드의 최신 summary_title의 시간 기준으로 정렬
        # grouped_list_sorted = sorted(grouped_results, key=lambda x: datetime.strptime(x['items'][0]['article_date'], '%Y-%m-%d %H:%M'), reverse=True)
        # print(grouped_list_sorted)
        
        # print(grouped_dict_sorted)

        # search_ids = []
        # for keyword, value in grouped_dict_sorted.items():
        #     for v in value:
        #         search_ids.append(v['id'])
        # print(search_ids)
        
        # result = self.chromadb.get_by_ids(search_ids)
        # print(result)



if __name__ == '__main__':

    # ad = article_data()
    # ad.new()
    # all_documents = ad.show_all()
    # print(all_documents)
    # get_lastes_article()
    # ad.test()
    
    # sd = summary_data()
    # sd.new()
    # sd.renewal_similarity()
    # sd.test()
    # all_documents = sd.show_all()
    # print(all_documents)

    # topTag = '경제 뉴스'
    # middleTag = '물가'
    # searchDate = '2024-08-01'
    # sd.api_test()

    yd = ytn_data()
    # yd.new()
    yd.renewal_similarity()
    # yd.api_test()
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

class article_data():
    def __init__(self):
        self.collection_name = 'article_data'

        self.ytn = ytn_manager()
        self.chromadb = ChromaManager(self.collection_name)

    def new(self):
        
        # # 데이터 전부 삭제
        # self.chromadb.delete_collection(method='delete_all_data') # delete_all_data, delete_collection
        # # self.chromadb = ChromaManager(self.collection_name) # delete_collection용


        self.ytn.ytn_crawling(chromadb=self.chromadb)


    def show_all(self):
        all_documents = self.chromadb.export_all()
        return all_documents
        

    def test(self):
        longformer = Longformer()
        qurey = """
다음 주(7월 22∼26일)에는 우리나라 경제의 2분기 성장률이 드러나고, 인구 관련 최신 지표가 공개된다. 김병환 금융위원장 후보에 대한 인사청문회도 열린다. 한국은행은 25일 '2분기 실질 국내총생산(GDP·속보)'을 발표한다. 앞서 1분기 우리나라 실질 GDP의 경우 순수출(수출-수입)과 건설투자, 민간소비 회복에 힘입어 1.3%(직전분기 대비) 성장했다. 시장의 전망치를 웃도는 '깜짝 성장'으로, 이를 기반으로 한은은 올해 성장률 눈높이를 기존 2.1%에서 2.5%로 올려잡았다. 하지만 1분기 성장률이 기대 이상으로 높았던 '기저효과'와 아직 뚜렷하지 않은 소비 회복 등을 고려할 때, 2분기 성장률은 1분기보다 크게 낮아질 것으로 예상된다. 실제로 상당수 경제 전문기관이나 금융사 등은 2분기 성장률이 0% 안팎에 머물 것으로 보고 있다. 통계청은 24일 '5월 인구 동향' 통계를 내놓는다. 전 세계 최악 수준으로 추락한 저출산 추세 속에서 지난 4월의 '반짝 증가'가 이어졌을지 주목된다. 4월 출생아 수는 1만9천49명으로 작년 같은 달보다 521명(2.8%) 늘면서 1년 7개월 만에 처음으로 플러스를 기록한 바 있다. 다만 월별 출생아는 여전히 2만명을 밑도는 수준으로, 추세 반전을 언급하기는 성급하다는 평가다. 최상목 부총리 겸 기획재정부 장관은 23일 경제관계장관회의를 열고 시니어 레지던스 활성화 방안, 공공기관 대국민 체감형 서비스 개선방안 등을 발표한다. 이어 브라질 리우데자네이루에서 열리는 '주요 20개국(G20) 재무장관 회의'에 참석한다. 다음 주에는 금융당국 수장이 바뀔 전망이다. 국회 정무위원회는 22일 김병환 금융위원장 후보자에 대한 인사청문회를 실시한다. 윤석열 대통령은 김 후보자에 대한 인사 청문 보고서가 채택되면, 김 후보자를 금융위원장에 임명한다. 금융위원회와 금융감독원은 이후 25일 국회 정무위에 업무보고를 할 예정이다. 우리투자증권은 10년 만에 부활할 것으로 관측된다. 금융위원회는 24일 정례회의에서 우리금융그룹이 제출한 우리종합금융과 한국포스증권의 합병을 인가할 계획이다. 우리금융은 2014년 6월 우리투자증권(현 NH투자증권)을 매각한 바 있다.
"""
        search_date = r"2024-08-01"
        tenser_embedding = longformer.inference(qurey)
        embedding = torch.squeeze(tenser_embedding).tolist()
        respons = self.chromadb.search(embedding=embedding,
                                       search_date=search_date)
        
        for k, data in enumerate(respons):
            if data['distances'] < 20:
                print(f"{k}번 - 유사도 : {round(data['distances'], 3)}")
                print(f"URI : {data['metadata']['url'].strip()}")
                print(f"기사 제목 : {data['metadata']['title']}")
                print(f"요약문 : {data['metadata']['summary']}")
                # if m['article_date'].startswith('수'):
                #     m['article_date'] = m['article_date'].split('정')[0]
                #     print(f"송고 시간 : {m['article_date'][1:].strip()}")
                # else:
                #     print(f"송고 시간 : {m['article_date'].strip()}")
                print(f"송고 시간 : {data['metadata']['article_date'].strip()}")
                print(f"세트 번호 : {data['metadata']['set_num']}") # 세트 번호는 int
                print(f"DB ID : {data['ids']}\n")



class summary_data():
    def __init__(self):
        collection_name = 'summary_data'
        self.collection_name = collection_name
        self.ytn = ytn_manager()
        self.chromadb = ChromaManager(collection_name)


    def new(self):
        # # 데이터 전부 삭제
        # self.chromadb.delete_collection(method='delete_all_data') # delete_all_data, delete_collection
        # # self.chromadb = ChromaManager(self.collection_name) # delete_collection용


        self.ytn.ytn_crawling(chromadb=self.chromadb, using_summary=True)

    def renewal_similarity(self):
        from tqdm import tqdm
        from time import sleep
        import json
        
        longformer = Longformer()

        ############################## 인덱스 갱신 ##############################
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
        #         embeddings=embedding, 
        #         documents=[document['document']],
        #         metadatas=[document['metadata']]
        #     )
        # print("인덱스가 날짜 순으로 다시 부여되었습니다.")
        # print("index 갱신 완료")
        ######################################################################
        
        file_path = r"./sum_test.json"
        ############################## 모든 데이터 저장 ##############################
        all_documents = self.chromadb.export_all()
        sorted_documents = sorted(all_documents, key=lambda x: x['metadata']['article_date'])
        print("모든 데이터 시간 오름차순 정렬정렬")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_documents, f, ensure_ascii=False, indent=4)
        print(f"데이터가 {file_path}에 저장되었습니다.")
        ######################################################################

        ############################## 데이터 전부 삭제 ##############################
        # # delete_all_data, delete_collection
        # self.chromadb.delete_collection(method='delete_collection') 
        # # self.chromadb = ChromaManager(self.collection_name)
        ######################################################################

        threshold = 18.0
        ############################## 임계치 갱신 ##############################
        # with open(file_path, 'r', encoding='utf-8') as f:
        #     sorted_documents = json.load(f)
        
        # latest_set_num = 0
        # for document in tqdm(sorted_documents):
        #     search_date = document['metadata']['article_date'].split(' ')[0]  # 날짜만 가져옴
            
        #     tenser_embedding = longformer.inference(document['metadata']['summary'])
        #     embedding = torch.squeeze(tenser_embedding).tolist()
        #     print(len(embedding))
        #     response = self.chromadb.search(embedding=embedding, search_date=search_date)
            
        #     set_list = []
        #     for k, data in enumerate(response):
        #         if (data['distance'] < threshold) and (data['distance'] != 0.) :
        #             print(f"{k}번 - 유사도 : {round(data['distance'], 3)}")
        #             print(f"URI : {data['metadata']['url'].strip()}")
        #             print(f"기사 제목 : {data['metadata']['title']}")
        #             print(f"요약문 : {data['metadata']['summary']}")
        #             print(f"송고 시간 : {data['metadata']['article_date'].strip()}")
        #             print(f"세트 번호 : {data['metadata']['set_num']}") 
        #             print(f"DB ID : {data['id']}\n")
        #             similarity = f"{data['metadata']['index']}->{data['metadata']['set_num']}->{data['distance']}"
        #             set_list.append(similarity)
                    
        #     # latest_set_num 사용 및 갱신 -> 가장 유사도 높은 set_num으로 !
        #     if len(set_list) != 0:
        #         set_num = -1
        #         tmp_similarity = 20.
        #         for i, set in enumerate(set_list):
        #             set = set.split('->')
        #             if float(set[2]) < tmp_similarity:
        #                 tmp_similarity = float(set[2])
        #                 set_num = int(set[1])
        #         print(f"세트 번호 리스트에 다른 종류? {set_list}")
        #     elif len(set_list) == 0:
        #         set_num = latest_set_num + 1
        #         latest_set_num = set_num

        #     # set_list -> str로 바꿔서 저장. 
        #     set_list = ', '.join(set_list)

        #     tenser_embedding = longformer.inference(document['metadata']['summary'])
        #     embedding = torch.squeeze(tenser_embedding).tolist()
            
        #     # DB에 저장
        #     self.chromadb.add_or_update(index=document['metadata']['index'], 
        #                                embedding=embedding, 
        #                                media=document['metadata']['media'], 
        #                                url=document['metadata']['url'],
        #                                title=document['metadata']['title'], 
        #                                article=document['document'], 
        #                                article_date=document['metadata']['article_date'], 
        #                                summary_title=document['metadata']['summary_title'], 
        #                                summary=document['metadata']['summary'], 
        #                                summary_reason=document['metadata']['summary_reason'], 
        #                                main=document['metadata']['main'], 
        #                                sub=document['metadata']['sub'], 
        #                                major_class=document['metadata']['major_class'], 
        #                                medium_class=document['metadata']['medium_class'],
        #                                set_num=set_num, 
        #                                set_list=set_list)
        #     sleep(0.1)
        ######################################################################

    def show_all(self):
        self.chromadb.export_all()
        

    def test(self):
        longformer = Longformer()
        qurey = """
충북 제천시는 2025 국제한방천연물산업엑스포의 성공 개최를 위해 국외 자매도시인 중국 쓰촨(四川)성 펑저우(彭州)시에서 홍보활동을 벌였다고 3일 밝혔다.  김창규 시장을 단장으로 한 방문단은 지난달 31일부터 이날까지 펑저우시 관계자 및 지역 기업들과 공식 면담을 갖고 엑스포 참여 방안에 대해 논의를 진행했다.  방문단은 또 신녹색약업공사 등 중의약 기업들을 방문해 천연물 산업의 협력과 발전 방안에 대해서도 논의했다. 김 시장은 "국외 자매도시와의 교류 협력을 통해 내년 엑스포의 성공개최 기반을 착실히 다져나갈 것"이라고 말했다.  이 엑스포는 내년 9월 20일부터 10월 19일까지
"""
        search_date = r"2024-08-03"
        # model_api_address = 'http://61.43.54.32:8181/api'
        # MODEL_API_ADDRESS = model_api_address
        # response = requests.post(MODEL_API_ADDRESS, data=qurey)    
        # print(response.json())

        # summary = response.json() ##

        tenser_embedding = longformer.inference(qurey)
        embedding = torch.squeeze(tenser_embedding).tolist()
        respons = self.chromadb.search(embedding, search_date)
        
        for k, data in enumerate(respons):
            if data['distance'] < 20:
                print(f"{k}번 - 유사도 : {round(data['distance'], 3)}")
                print(f"URI : {data['metadata']['url'].strip()}")
                print(f"기사 제목 : {data['metadata']['title']}")
                print(f"요약문 : {data['metadata']['summary']}")
                # if m['article_date'].startswith('수'):
                #     m['article_date'] = m['article_date'].split('정')[0]
                #     print(f"송고 시간 : {m['article_date'][1:].strip()}")
                # else:
                #     print(f"송고 시간 : {m['article_date'].strip()}")
                print(f"송고 시간 : {data['metadata']['article_date'].strip()}")
                print(f"세트 번호 : {data['metadata']['set_num']}") # 세트 번호는 int
                print(f"DB ID : {data['id']}\n")

    def api_test(self):
        from datetime import datetime
        st = time()
        topTag = '경제 뉴스'
        middleTag = '부동산'
        searchDate = '2024-08-01'
        response = self.chromadb.search_by_tags_and_date(topTag=topTag, 
                                                         middleTag=middleTag, 
                                                         searchDate=searchDate)
        print(response)
        et = time()
        print(et-st)

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
        
        file_path = r"./ytn_test.json"
        # ############################## 모든 데이터 저장 ##############################
        # all_documents = self.chromadb.export_all()
        # sorted_documents = sorted(all_documents, key=lambda x: x['metadata']['article_date'])
        # print("모든 데이터 시간 오름차순 정렬정렬")
        
        # with open(file_path, 'w', encoding='utf-8') as f:
        #     json.dump(sorted_documents, f, ensure_ascii=False, indent=4)
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
            
            tenser_embedding = longformer.inference(document['metadata']['summary'])
            embedding = torch.squeeze(tenser_embedding).tolist()
            
            response = self.chromadb.search(embedding=embedding, search_date=search_date)
            
            # 매일 Set Num 0으로 초기화
            if tmp_date != search_date:
                latest_set_num = 0
                tmp_date = search_date
                
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
                set_num = latest_set_num + 1
                latest_set_num = set_num

            # set_list -> str로 바꿔서 저장. 
            set_list = ', '.join(set_list)

            # Embedding 생성
            tenser_embedding = longformer.inference(document['metadata']['summary'])
            embedding = torch.squeeze(tenser_embedding).tolist()
            
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
                                       main=document['metadata']['main'], 
                                       sub=document['metadata']['sub'], 
                                       major_class=document['metadata']['major_class'], 
                                       medium_class=document['metadata']['medium_class'],
                                       set_num=set_num, 
                                       set_list=set_list)
            sleep(0.1)

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
        from datetime import datetime
        main_tag = '삼성전자'
        search_date = '2024-08-07'

        response = self.chromadb.get_by_main_date(main_tag=main_tag,
                                                search_date=search_date)
        # final_results에서 keyword를 기준으로 데이터를 묶음
        grouped_results = {}

        for item in response:
            id = item.get('id')
            keyword = item.get('keyword')
            summary_title = item.get('summary_title')
            article_date = item.get('article_date')
            
            if keyword in grouped_results:
                grouped_results[keyword].append({
                    'id': id,
                    'summary_title': summary_title,
                    'article_date': article_date
                })
            else:
                grouped_results[keyword] = [{
                    'id': id,
                    'summary_title': summary_title,
                    'article_date': article_date
                }]

        # 각 키워드 내에서 summary_title을 최신 시간 기준으로 정렬
        for keyword in grouped_results:
            grouped_results[keyword] = sorted(grouped_results[keyword], key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

        # 키워드를, 그 키워드의 최신 summary_title의 시간 기준으로 정렬
        grouped_list_sorted = sorted(grouped_results.items(), key=lambda x: datetime.strptime(x[1][0]['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

        # 다시 딕셔너리로 변환
        grouped_dict_sorted = {k: v for k, v in grouped_list_sorted}

        print(grouped_dict_sorted)

        search_ids = []
        for keyword, value in grouped_dict_sorted.items():
            for v in value:
                search_ids.append(v['id'])
        print(search_ids)
        
        result = self.chromadb.get_by_ids(search_ids)
        print(result)



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
    # yd.renewal_similarity()
    yd.api_test()
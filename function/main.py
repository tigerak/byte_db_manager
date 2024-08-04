import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)
# torch
import torch
# modules
from function.news_manager import ytn_manager
from function.db_manager import ChromaManager
from function.longformer import Longformer


class article_data():
    def __init__(self):
        self.collection_name = 'article_data'

        self.ytn = ytn_manager()
        self.chromadb = ChromaManager(self.collection_name)

    def new(self):
        
        # 데이터 전부 삭제
        self.chromadb.delete_collection(method='delete_all_data') # delete_all_data, delete_collection
        # self.chromadb = ChromaManager(self.collection_name) # delete_collection용


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

        self.ytn = ytn_manager()
        self.chromadb = ChromaManager(collection_name)


    def new(self):
        
        # # 데이터 전부 삭제
        # self.chromadb.delete_collection(method='delete_all_data')

        self.ytn.ytn_crawling(chromadb=self.chromadb, using_summary=True)


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


if __name__ == '__main__':

    # ad = article_data()
    # ad.new()
    # all_documents = ad.show_all()
    # print(all_documents)
    # get_lastes_article()
    # ad.test()
    
    sd = summary_data()
    sd.new()
    # sd.test()
    # all_documents = sd.show_all()
    # print(all_documents)
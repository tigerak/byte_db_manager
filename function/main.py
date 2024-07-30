import sys
# torch
import torch
# modules
from function.news_manager import ytn_manager
from function.db_manager import ChromaManager
from function.longformer import Longformer
from app.config import BASE_DIR
sys.path.append(BASE_DIR)
print(sys.path)


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
    서울을 중심으로 수도권 주택 시장이 들썩이는 가운데 국토교통부가 장기 평균과 비교해 서울 아파트 공급이 부족한 상황은 아니라는 진단을 연일 내놓고 있다. 국토부는 17일 보도설명자료를 통해 "서울 아파트 입주 물량은 10년 평균 대비부족하지 않으며, 올해보다 내년에 더욱 늘어날 전망"이라고 밝혔다. 서울 아파트는 입주 물량이 올해 3만8천가구, 내년 4만8천가구로 예상돼 아파트 준공 물량 10년 평균인 3만8천가구에 비해 부족하지 않다는 설명이다. 국토부는 주택 공급 지표 중 준공과 착공이 늘어나고 있다는 점을 앞세우고 있다. 올해 1∼5월 전국 주택 준공 실적은 18만3천638가구로 작년 같은 기간보다 16.5% 증가하고, 착공은 10만6천537가구로 31.4% 늘었다는 것이다. 그러면서 "공급 여건 개선을 위한 정책 효과가 꾸준히 나타나고 있는 상황"이라고 밝혔다. 국토부는 전날에도 보도설명자료를 통해 "올해 1∼5월 누계 서울 아파트 준공 실적은 1만1천900가구로 전년 동기(5천600가구) 대비 2배 이상 증가했다"고 설명했다. 1∼5월 서울 아파트 착공 실적(9천221가구) 역시 부동산 프로젝트파이낸싱(PF) 대출 보증 공급 등의 영향으로 작년 동기보다 13% 증가해 공급 실적이 개선되고 있다고 했다. 다만 지난해 공급이 장기 평균과 비교해 상당히 축소돼 있었기에 기저효과가 있다는 점은 고려해야 한다. 김규철 국토부 주택토지실장은 이날 국회 국토교통위원회 전체회의에서 "서울의 경우 (입주 물량이) 충분한 것으로 파악하고 있다"며 "하반기에 추가적인 공급이 이뤄질 수 있도록 지원을 강화하겠다"고 밝혔다. 서울 아파트 공급이 부족하지 않다는 판단은 "(집값이) 추세적으로 상승 전환하는 것은 아니라고 확신한다"는 박상우 국토부 장관의 발언과 궤를 함께하는 것으로 볼 수 있다. 그러나 정부는 그간 '주택 공급 실적'의 기준으로 착공·준공이 아닌 인허가를 사용해왔다. 국토부의 보도설명자료에는 인허가에 대한 내용은 빠져있다. 윤석열 정부가 목표치로 삼은 '임기 내 주택공급 270만가구'도 인허가 기준이다. 이 계획에 따라 국토부는 올해 공급 계획 물량을 54만가구(수도권 30만가구)로 잡고 있다. 일반적으로 주택은 인허가 이후 3∼5년, 착공 이후 2∼3년 후에 준공돼 입주가 이뤄진다. 착공·준공과 달리 인허가는 계속해서 부진한 상태다. 올해 1∼5월 인허가 물량은 12만5천974가구로 작년 같은 기간보다 24.1% 줄었다. 연간 목표 물량을 달성하려면 연말까지 40만가구 이상 인허가가 이뤄져야 한다. 지난해 주택 인허가는 42만9천가구로 연간 목표치(54만가구)에 20%가량 못 미쳤다. 이에 따라 2∼3년 후 신축 공급이 줄어들 것이라는 시장 전망은 '지금 집을 사야 한다'는 실수요자들의 심리를 자극하고 있다. 정부는 규제 완화를 통한 주택 공급 확대를 추진하며 지난해 '9·26 공급대책'에 이어 올해 '1·10 부동산 대책'을 내놓았으나 공사비 급등과 건설경기 침체 등으로 약발이 제대로 먹히지 않는 상황이다. 특히 빌라 등 비(非)아파트 인허가는 1∼5월 1만5천313가구로 작년 같은 기간보다 35.8% 감소해 아파트 인허가(-22.1%)보다 감소 폭이 두드러진다. 착공의 경우 1∼5월 아파트 착공이 50.4% 증가하는 동안 비아파트는 26.7% 감소했다. 1∼5월 준공도 아파트가 29.5% 증가했으나 비아파트는 39.2% 줄었다. 일각에서는 공급 부족 우려와 관련한 정부 대응 수위가 낮은 것 아니냐는 지적도 나온다. 국토부는 지난해 8월 이후 1년 가까이 주택공급혁신위원회를 소집하지 않았다. 이 위원회는 윤석열 정부의 270만가구 공급 공약의 구체적 계획을 마련하기 위해 구성됐으며 주택·건설업계 전문가들이 위원으로 포함돼 있다. 주택시장 불안 우려가 커지자 정부는 오는 18일 최상목 경제부총리 겸 기획재정부 장관 주재로 부동산 관계장관회의를 열어 대응 방안을 논의한다. 국토부는 3기 신도시와 신규 택지를 통한 공급을 앞당기는 방안 등 공급 활성화 방안을 준비하고 있다. 이르면 이달 중 대책을 발표할 것으로 보인다. 국토부는 서울 일부 지역을 중심으로 한 집값, 전셋값 상승세는 분명하다면서 추세적 상승으로 전환할 가능성이 있는지 시장 전문가들과 협의하며 상황을 진단하고 있다고 밝혔다. 김규철 실장은 "추세적 전환 가능성 있다고 보는 전문가가 있는 반면, 유효 수요가 제한적일 수밖에 없고 전반적으로 경기 침체가 진행 중인 상황이라 유동성 요인으로 매매가격이 상승하고 있다는 전문가도 많다"면서 "정부가 가계부채 관리 기조를 강하게 가져가는 상황에서 (집값이) 지속해서 오르기 어렵다는 의견을 제시하는 분들이 있어 상황을 예의주시하면서 대응하고 있다"고 말했다.
    """
        search_date = r"2024-07-21"
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
다음 주(7월 22∼26일)에는 우리나라 경제의 2분기 성장률이 드러나고, 인구 관련 최신 지표가 공개된다. 김병환 금융위원장 후보에 대한 인사청문회도 열린다. 한국은행은 25일 '2분기 실질 국내총생산(GDP·속보)'을 발표한다. 앞서 1분기 우리나라 실질 GDP의 경우 순수출(수출-수입)과 건설투자, 민간소비 회복에 힘입어 1.3%(직전분기 대비) 성장했다. 시장의 전망치를 웃도는 '깜짝 성장'으로, 이를 기반으로 한은은 올해 성장률 눈높이를 기존 2.1%에서 2.5%로 올려잡았다. 하지만 1분기 성장률이 기대 이상으로 높았던 '기저효과'와 아직 뚜렷하지 않은 소비 회복 등을 고려할 때, 2분기 성장률은 1분기보다 크게 낮아질 것으로 예상된다. 실제로 상당수 경제 전문기관이나 금융사 등은 2분기 성장률이 0% 안팎에 머물 것으로 보고 있다. 통계청은 24일 '5월 인구 동향' 통계를 내놓는다. 전 세계 최악 수준으로 추락한 저출산 추세 속에서 지난 4월의 '반짝 증가'가 이어졌을지 주목된다. 4월 출생아 수는 1만9천49명으로 작년 같은 달보다 521명(2.8%) 늘면서 1년 7개월 만에 처음으로 플러스를 기록한 바 있다. 다만 월별 출생아는 여전히 2만명을 밑도는 수준으로, 추세 반전을 언급하기는 성급하다는 평가다. 최상목 부총리 겸 기획재정부 장관은 23일 경제관계장관회의를 열고 시니어 레지던스 활성화 방안, 공공기관 대국민 체감형 서비스 개선방안 등을 발표한다. 이어 브라질 리우데자네이루에서 열리는 '주요 20개국(G20) 재무장관 회의'에 참석한다. 다음 주에는 금융당국 수장이 바뀔 전망이다. 국회 정무위원회는 22일 김병환 금융위원장 후보자에 대한 인사청문회를 실시한다. 윤석열 대통령은 김 후보자에 대한 인사 청문 보고서가 채택되면, 김 후보자를 금융위원장에 임명한다. 금융위원회와 금융감독원은 이후 25일 국회 정무위에 업무보고를 할 예정이다. 우리투자증권은 10년 만에 부활할 것으로 관측된다. 금융위원회는 24일 정례회의에서 우리금융그룹이 제출한 우리종합금융과 한국포스증권의 합병을 인가할 계획이다. 우리금융은 2014년 6월 우리투자증권(현 NH투자증권)을 매각한 바 있다.
"""

        # model_api_address = 'http://61.43.54.32:8181/api'
        # MODEL_API_ADDRESS = model_api_address
        # response = requests.post(MODEL_API_ADDRESS, data=qurey)    
        # print(response.json())

        # summary = response.json() ##

        tenser_embedding = longformer.inference(qurey)
        embedding = torch.squeeze(tenser_embedding).tolist()
        respons = self.chromadb.search(embedding)
        
        for k, (d, m, i) in enumerate(zip(respons['distances'][0], 
                                        respons['metadatas'][0], 
                                        respons['ids'][0])):
            
            if d > 20:
                print(f"{k}번 - 유사도 : {round(d, 3)}")
                print(f"URI : {m['url'].strip()}")
                print(f"기사 제목 : {m['title']}")
                print(f"요약문 : {m['summary']}")
                # if m['article_date'].startswith('수'):
                #     m['article_date'] = m['article_date'].split('정')[0]
                #     print(f"송고 시간 : {m['article_date'][1:].strip()}")
                # else:
                #     print(f"송고 시간 : {m['article_date'].strip()}")
                print(f"송고 시간 : {m['article_date'].strip()}")
                print(f"세트 번호 : {m['set_num']}") # 세트 번호는 int
                print(f"DB ID : {i}\n")


if __name__ == '__main__':

    ad = article_data()
    ad.new()
    # all_documents = ad.show_all()
    # print(all_documents)
    # get_lastes_article()
    # ad.test()
    
    # sd = summary_data()
    # sd.new()
    # sd.test()
    # all_documents = sd.show_all()
    # print(all_documents)
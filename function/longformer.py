# import os
# # CUDA 호출을 동기적으로 실행하여 디버깅을 용이하게 함
# os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

# # 디바이스 측 어설션을 위한 환경 변수 설정
# os.environ["TORCH_USE_CUDA_DSA"] = "1"
import copy

import math

import torch
from transformers.models.longformer.modeling_longformer import LongformerSelfAttention
from transformers import AutoTokenizer, AutoModel, RobertaModel
# modules
from function.models.model_cfg import model_choice


class RobertaLongSelfAttention(LongformerSelfAttention):
    def forward(
        self,
        hidden_states,
        attention_mask=None,
        head_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        output_attentions=False
    ):
        
        return super().forward(
            hidden_states,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
        )

class RobertaLongForMaskedLM(AutoModel):
    def __init__(self, config):
        super().__init__(config)
        
        for i, layer in enumerate(self.encoder.layer):
            # replace the `modeling_bert.BertSelfAttention` object with `LongformerSelfAttention`
            layer.attention.self = RobertaLongSelfAttention(config, layer_id=i)

            layer.attention.self.query_global = copy.deepcopy(layer.attention.self.query)
            layer.attention.self.key_global = copy.deepcopy(layer.attention.self.key)
            layer.attention.self.value_global = copy.deepcopy(layer.attention.self.value)
    
            
class Longformer():
    def __init__(self):
        self.CFG = model_choice['bert_base_4096']

        self.model = RobertaLongForMaskedLM.from_pretrained(self.CFG['MODEL_SAVE_DIR'])
        self.tokenizer = AutoTokenizer.from_pretrained(self.CFG['MODEL_SAVE_DIR'])
        
    def inference(self, article):
        # 입력 시퀀스 길이를 계산 (예시)
        input_length = len(self.tokenizer.encode(article))
        # 512의 배수로 설정할 max_length 계산
        max_length = math.ceil(input_length / 512) * 512
        inputs = self.tokenizer(article, 
                        return_tensors='pt',
                        padding='max_length',  # 패딩 활성화
                        max_length=max_length,  # 최대 길이 설정
                        truncation=True
                        )
        # print(f"INPUT IDS SIZE : {inputs['input_ids'].size()}")
        if self.CFG['DEVICE'] == 'gpu':
            model = self.model.to('cuda')
            inputs = inputs.to('cuda')
        with torch.no_grad():
            outputs = model(**inputs, return_dict=False)
            
        # print(len(outputs)) # 토큰차원, 문서차원
        # print(outputs[0].size()) # 토큰 차원
        # print(outputs[1].size()) # 문서 차원
        
        return outputs[1] 
    
    def test_func(self):
        return self.model, self.tokenizer
        
# if __name__ == '__main__':
#     article = ["""
# 환경부가 20일 올해 전기차 보조금 업무처리 지침을 확정하자 국내 자동차 업계는 중국산 리튬인산철(LFP) 배터리 탑재 여부에 따라 희비가 엇갈렸다. 이번 지침이 에너지 밀도와 재활용성이 낮은 LFP 배터리를 겨냥한 만큼 해당 배터리를 탑재한 전기 승용차를 출시한 업체들은 줄어든 보조금에 난감한 표정을 지었다. 특히 가격이 저렴한 LFP 배터리를 사용할 수밖에 없는 중소 전기상용차 제작·수입·판매업체들은 폐업까지 갈 수 있다며 망연자실한 모습이었다. 다만 글로벌 전기차 시장에서 번져가고 있는 자국 우선주의와 탈탄소 흐름에 대응한 불가피한 결정이라는 목소리도 있었다. ◇ 국산차·대다수 수입차 "영향 크지 않아"…테슬라 등 타격 이날 환경부가 발표한 차종별 보조금 액수에 따르면 올해 전기 승용차가 받을 수 있는 최대 국비 보조금은 작년보다 30만원가량 감소했다. 다만 국비 보조금을 최대한 받을 수 있는 차종 대부분이 국내 완성차업체인 현대차와 기아 브랜드라는 점에서 '국내 기업에 유리한 전기차 보조금 지침'이라는 해석이 나왔다. 현대차·기아는 주력 전기차 라인업인 아이오닉5·6와 EV6가 보조금을 100% 수령할 수 있는 상한인 5천500만원 이내로 가격이 설정됐고, 니켈·코발트·망간(NCM) 배터리가 탑재돼 배터리에 따른 불이익을 받지 않는다. 이에 따라 올해에도 아이오닉6 롱레인지 2WD 18·20인치 모델과 AWD 18인치 모델 구입 시 국비 보조금 최대치인 690만원을 받을 수 있다. 메르세데스-벤츠, BMW, 아우디, 볼보, 렉서스 등 주류 수입차 업계도 비슷한 입장이다. 이들 브랜드의 주요 전기차 가격은 보조금 상한선인 8천500만원을 넘기는 경우가 많아 보조금이 판매에 미치는 영향이 상대적으로 적다. 보조금 50% 수령 대상인 차종들도 대부분 NCM 기반 삼원계 배터리를 사용해 LFP 배터리 탑재에 따른 불이익을 받지 않는다. 다만 보조금 100% 수령 기준인 5천500만원에 맞춰 차량 가격을 인하했거나 LFP 배터리를 탑재한 일부 수입 차종은 큰 타격을 받을 전망이다. '중국산 테슬라'로 불리는 모델Y 후륜구동 모델이 대표적이다. 이 모델의 가격은 최근 200만원 인하됐지만, 올해 보조금은 작년(514만원)보다 62% 감소한 195만원으로 책정됐다. 함께 5천500만원 이하로 가격이 하향 조정된 폭스바겐 ID.4와 폴스타2 구입 시에는 지난해보다 적긴 하지만 각각 492만원, 439만원의 보조금을 받는다. 수입 전기차 중 보조금 액수가 400만원을 넘긴 것은 이 두 차종이 유일하다. KG모빌리티(KGM)의 토레스 EVX에 대해서도 작년 대비 30%가량 감소한 443만∼457만원의 보조금이 정해졌다. BYD(비야디)의 LFP 배터리를 장착한 이 차종은 가성비가 가장 큰 장점이라 KGM은 고객 지원 방안을 마련하는 동시에 환경부에 구체적인 보조금 책정 요소를 문의할 예정이다. ◇ 전기버스 보조금 최대 4천300만원 줄어 이번 보조금 지침이 중국산 수입 증가로 국산과 수입산 판매량이 역전된 전기버스 시장을 겨냥했다는 해석도 나온다. 국토교통부 자동차 통계에 따르면 지난해 국내에서 등록된 국산과 수입 전기버스는 각각 1천293대(45.8%), 1천528대(54.2%)로 집계됐다. 수입 전기버스 등록 대수가 국산을 넘어선 것은 지난해가 처음으로, 여기에는 LFP 배터리가 탑재된 중국산 전기버스 수입 증가가 큰 역할을 했다. 하지만 이번 지침이 적용될 경우 LFP 배터리가 탑재된 중국산 전기버스에 대한 보조금은 작년 대비 최대 4천300만원가량 줄어든다. 중국산 LFP 배터리가 탑재된 전기화물차도 타격이 불가피하다. BYD를 포함한 중국산 화물차들은 작년 대비 최대 800만원까지 보조금이 줄어든 반면, 현대차 포터 포터II 일렉트릭, 기아 봉고EV는 국비 보조금 최대치(1천50만원)가 적용돼 '국산차 밀어주기'라는 말이 나온다. 이에 따라 비용 문제로 LFP 배터리를 탑재할 수밖에 없는 중소 전기차 제작·수입·판매업체들도 반발하고 있다. 보조금이 줄면서 최대 강점이 가격경쟁력이 타격을 받아 폐업까지 갈 수 있다는 것이 이들의 주장이다. 중소 전기차 업체 관계자는 "이번 개편이 전기차, 특히 전기상용차 보급이나 인프라 구축을 더 늦출 가능성이 있다"고 말했다. ◇ "환경·국산 전기차 고려한 결정" 목소리도 다만 배터리의 효율과 재활용성에 기반해 친환경적인 차가 더 많은 지원을 받을 수 있도록 하겠다는 환경부의 방침을 지지하는 목소리도 있다. LFP 배터리는 사용 후 꺼낼 금속이 사실상 리튬뿐이라 경제성이 떨어지고, 재활용이 힘들어 환경에도 악영향을 미친다. 아울러 전기차 보조금 지급 등과 관련해 자국 우선주의가 전 세계적으로 확산하는 상황에서 국내 자동차산업 보호를 위해서는 '적절한 대응책'이라는 분석도 나온다. 현재 미국은 인플레이션 감축법(IRA)에 따라 일정 조건 아래 북미에서 생산된 전기차에만 보조금을 지급하고, 프랑스는 전기차 생산, 수송 등에서 발생한 탄소 배출량을 측정해 보조금을 차등 지급하는 방식으로 전기차 수입을 규제하고 있다. 업계 관계자는 "이번 전기차 보조금 개편안은 환경개선과 배터리 기술개발, 소비자 편익 확충을 유도할 수 있어 긍정적 측면이 분명히 있다"고 밝혔다.
# ""","""
# 미국 연방준비제도(Fed·연준)의 오는 19∼20일 연방공개시장위원회(FOMC) 회의에 전 세계 중앙은행의 이목이 집중되고 있다. 이번 FOMC에서 기준금리 추가 인상 여부가 결정될 예정인 가운데 일본 등 다른 주요 경제권도 이번 주에 기준금리를 결정할 계획이기 때문이다. 앞서 유럽중앙은행(ECB)은 지난 14일 시장의 예상을 깨고 기준금리를 연 4.5%로 0.25%포인트 올린 상태다. 다수 전문가는 미 연준이 이번 회의에서는 기준금리를 동결하겠지만 연말 이전에 한 번 더 금리를 올릴 가능성이 있다는데 무게를 두는 분위기다. 연준이 인플레이션(물가 상승)과의 전쟁이 아직 끝나지 않았다는 메시지를 강조할 경우 각국의 연쇄 금리 인상 등 긴축 유지 기조는 당분간 계속될 가능성이 있다. ◇ 유가 강세 등 여전한 물가 우려 미국의 기준 금리는 지난 1년 넘게 꾸준히 오른 끝에 현재 22년 만에 가장 높은 수준인 연 5.25∼5.50%로 인상된 상태다. 이에 금융시장은 연준의 이달 금리 동결 가능성을 거의 확신해왔고 골드만삭스는 연준의 긴축통화정책이 종료된 것으로 분석하기도 했다. 하지만 최근 이런 전망에 다소 변화가 생겼다. 국제유가가 연내 배럴당 100달러에 이를 것이라는 전망이 나오며 유가가 들썩이는 등 여전히 물가가 출렁이면서다. 변동성이 큰 에너지·식품을 제외한 미국의 8월 근원 소비자물가지수(CPI)도 전달보다 0.3% 올랐다. 전년 동월 대비 4.3% 올랐으며 연준 목표치인 2%를 여전히 크게 웃도는 수치다. 이런 가운데 ECB는 지난 14일 기준금리를 연 4.5%로, 수신금리와 한계대출금리는 각각 연 4.0%와 연 4.75%로 0.25%포인트씩 올렸다. ECB는 작년 7월부터 10회 연속으로 금리를 인상했다. ECB는 물가 상승률 전망치를 올해 5.6%, 내년 3.2%로 지난번 전망치보다 각각 0.2%포인트씩 올렸다. 여기에는 에너지 가격 상승이 반영됐다. ◇ 고민에 빠진 연준 이에 연준이 연내에 추가로 금리를 인상할 가능성이 커졌다는 분석이 나온다. 다만, 소비지출 위축과 고용시장 냉각 등 인플레이션 둔화 촉진 요인이 여럿 있기 때문에 이번 통화정책 회의에서는 금리가 동결될 것이라는 전망이 여전히 우세한 상황이다. 블룸버그는 최근 "예상보다 뜨거운 물가 상승은 연준이 이달 금리 동결 이후 11월이나 12월에 다시 금리를 올릴 옵션을 열어두고 있다"고 평가했다. CNN방송도 연내 추가 금리 인상 가능성이 여전히 남아있다고 분석했다. 일각에서는 11월에도 연준이 금리를 올리지 않을 수 있다는 분석도 나온다. 로이터통신은 17일 골드만삭스의 보고서를 인용, 연준이 10월 31일∼11월 1일 회의에서도 기준금리를 올릴 가능성이 작다고 전망했다. 골드만삭스는 11월에는 과열됐던 노동시장이 다시 균형을 잡고 인플레이션에 대한 더 좋은 소식이 있을 수 있어 FOMC가 올해 마지막 기준금리 인상을 포기할 수 있다고 말했다. 이와 관련해 연준이 금리 정책과 관련해 딜레마에 빠졌다는 분석도 나온다. 지나친 금리 인상은 수요뿐만 아니라 공급에도 타격을 줘 오히려 가격 상승 압력으로 작용할 수 있다는 점에서다. 루즈벨트연구소의 마이크 콘크잘 거시경제 분석팀장은 이날 블룸버그통신에 "과도한 긴축 통화정책은 주택 같은 특정 경제 분야에 역효과를 낳을 수 있다"고 지적했다. 그는 "앞으로 몇 년 동안 인플레이션 목표를 2%로 지속 가능하게 되돌리기 위해서는 급격하게 성장을 억제하는 것보다는 절제된 성장 허용을 고려해야 한다는 점이 연준에는 정책적 역설인 상황"이라고 덧붙였다. ◇ 일본·중국 금리는 동결 전망 이런 상황 속에 이번 주는 전 세계 통화 정책 결정에서 매우 중요한 기간이 될 전망이다. 블룸버그통신은 미 연준을 시작으로 22일 일본은행까지 주요 20개국(G20)의 절반에 달하는 국가가 기준금리 결정 회의를 개최할 예정이라고 보도했다. 통신은 고금리를 유지하려는 미국의 압박에 각국이 적응하는 가운데, 이번 통화정책 결정은 올해 남은 기간의 금리 동향 분위기를 조성할 수 있다고 설명했다. 우선 일본의 마이너스 금리 기조 유지 여부에 관심이 쏠린다. 일본은 현재 주요국 가운데 유일하게 단기금리를 -0.1%로 운영하며 대규모 금융완화 정책을 추진하고 있다. 일본은행은 지난 7월 금융정책결정회의에서도 국채를 무제한 매입하는 10년물 국채 금리의 상한 기준을 종전 0.5%에서 사실상 1.0% 수준으로 올렸지만 단기금리는 동결했다. 하지만 우에다 가즈오 일본은행 총재는 최근 임금 상승을 동반한 지속적인 물가 상승을 확신할 수 있는 단계가 되면 마이너스 금리 해제도 여러 선택지 중 하나가 될 수 있다고 말하기도 했다. 이와 관련해 이코노미스트들은 블룸버그 설문조사에서 일본은행의 이번 회의에서는 아무런 변화가 없을 것으로 내다봤다. 다만, 일본은행의 정책입안자들은 연준의 금리 결정이 엔화를 포함한 지역 자산에 미칠 수 있는 영향을 면밀하게 살펴볼 것이라고 블룸버그통신은 보도했다. 경기 침체 우려가 짙어지고 있는 중국도 이번 주에는 대출 금리 변동이 없을 것으로 전망됐다. 중국 당국은 앞서 지난 15일 자로 6개월 만에 지급준비율을 0.25%포인트 인하했다. 앞서 중국인민은행은 작년 4월과 12월, 올해 3월 지준율을 0.25%포인트씩 낮춘 바 있다. 지난달 15일에는 대형 부동산 개발업체 등의 금융 리스크 증대 우려 속에 정책금리인 1년물 중기유동성지원창구(MLF) 금리와 7일물 역레포 금리를 각각 0.15%p(2.65→2.5%)와 0.1%p(1.9→1.8%)로 전격 인하한 상태다. ◇ 영국 스웨덴 등 유럽 각국 줄줄이 인상 가능성 유럽 지역에서는 금리 인상이 줄을 이을 것으로 보인다. 전문가 대부분은 영국 중앙은행인 잉글랜드은행(BOE)이 21일 기준금리를 0.25%포인트 인상할 것으로 예상한다. BOE는 지금까지 14차례 연속 공격적으로 금리 인상을 해 왔으며 이번이 마지막 인상이 될 것으로 전망된다. 앤드루 베일리 BOE 총재는 이달 초 "금리가 아마도 주기의 정점에 가까워진 것 같다"고 말했다. 같은 날 스위스국립은행(SNB)도 인플레이션 억제를 위해 추가 금리 인상을 단행할 수 있다고 블룸버그통신은 전망했다. 이번에 금리가 인상되더라도 역시 이번 긴축 사이클의 마지막이 될 것으로 분석됐다. 노르웨이와 스웨덴도 통화 정책을 긴축 상태로 더 유지할 가능성이 있는 것으로 전망됐다. 블룸버그통신 설문조사에 따르면 튀르키예 중앙은행은 기준금리를 약 5% 더 인상해 약 30%로 끌어올릴 것으로 예상됐다. 아울러 인플레이션 압박에 시달리는 이집트도 금리 인상 대열에 가세할 것으로 보인다. 반면, 브라질은 지난달에 이어 2회 연속으로 기준 금리를 0.5%포인트 인하, 12.75%로 낮출 것으로 보인다고 블룸버그통신은 전했다. 브라질의 월 물가상승률은 지난 6월 3.16% 이후 7월(3.99%), 8월(4.61%) 다소 나빠졌지만 작년 초 12%보다는 크게 낮아진 상태다.
# """
#         ]
        
#     lf = Longformer()
#     outputs = lf.inference(article=article)
#     print(outputs.size())
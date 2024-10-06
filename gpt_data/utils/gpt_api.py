
import re
import json
from tqdm import tqdm

from langchain_openai import ChatOpenAI
# from langchain.chains.llm import LLMChain
# from langchain.prompts import PromptTemplate
# from langchain.prompts import StringPromptTemplate
# from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# modules
from config import OPENAI_API_KEY


class GPT():
    # GPT4 모델 선택 및 기타 설정
    def __init__(self):
        
        model_name = 'gpt-4o-2024-05-13'
        self.chat_model = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                                     model=model_name,
                                     temperature=0.0)
        
    # GPT4에 직접 세트 넘버 마다의 결과 조회하는 코드.
    def query_gpt(self, json_path, set_num):
        # Data Preprocessing
        with open(json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        for n in json_data[set_num-1:set_num]:
            prompt = PromptTemplate.from_template(n)
            output_parser = StrOutputParser()
            sequence = prompt | self.chat_model | output_parser
            result = sequence.invoke({})
            # # Test Print
            print(f'{result}')
            break
        
        return result

    # function/main.py에서 직접 데이터 저장 후 KeyWord 추가하는 코드.
    def make_keyword_data(self, prompt_path, save_path):
        with open(prompt_path, 'r', encoding='utf-8') as file:
            prepare_prompt_list = json.load(file)

        keyword_data_list = []
        for prepare_prompt in tqdm(prepare_prompt_list, total=len(prepare_prompt_list)):
            prompt = PromptTemplate.from_template(prepare_prompt)
            output_parser = StrOutputParser()
            sequence = prompt | self.chat_model | output_parser
            result = sequence.invoke({})

            tmp_data = {
                'prompt': prepare_prompt,
                'response': result
            }
            keyword_data_list.append(tmp_data)

            print(result)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(keyword_data_list, f, ensure_ascii=False, indent=4)

        print(f"Prompt list가 {save_path}에 저장되었습니다.")

        return keyword_data_list
    
    # 같은 군집 추가 시 키워드 및 한 줄 설명 갱신
    def api_make_keyword(self, set_num_prompt):
        result = self.gpt_run(set_num_prompt)

        result = result.split('### 짧은 제목 :')[1]
        result = result.split('### 한 문장 설명 :')
        keyword = result[0].strip()
        description = result[1].strip()
        return keyword, description
    
    # 같은 요약문 제목 있을 경우 새 요약문 제목 생성
    def api_make_new_summary_title(self, prompt):
        result = self.gpt_run(prompt)
        # result = result.split('### 요약문 제목 :')
        # print(f"뉴 섬머리 타이플 : {result}")
        result = result.strip()
        return result
    
    # GPT4 실행
    def gpt_run(self, prepared_prompt):
        prompt = PromptTemplate.from_template(prepared_prompt)
        output_parser = StrOutputParser()
        sequence = prompt | self.chat_model | output_parser
        result = sequence.invoke({})
        return result
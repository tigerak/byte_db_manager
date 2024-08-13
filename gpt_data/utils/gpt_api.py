
import re
import json
from tqdm import tqdm

from langchain_openai import ChatOpenAI
# from langchain.chains.llm import LLMChain
# from langchain.prompts import PromptTemplate
from langchain.prompts import StringPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# modules
from app.config import OPENAI_API_KEY


class GPT():
    def __init__(self):
        
        model_name = 'gpt-4o-2024-05-13'
        self.chat_model = ChatOpenAI(openai_api_key=OPENAI_API_KEY,
                                     model=model_name,
                                     temperature=0.0)
        
         
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
    
    def api_make_keyword(self, set_num_prompt):
        prompt = PromptTemplate.from_template(set_num_prompt)
        output_parser = StrOutputParser()
        sequence = prompt | self.chat_model | output_parser
        result = sequence.invoke({})

        result = result.split('### 짧은 제목 :')[1]
        result = result.split('### 한 문장 설명 :')
        keyword = result[0].strip()
        description = result[1].strip()
        return keyword, description
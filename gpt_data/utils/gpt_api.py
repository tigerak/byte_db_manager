
import re
import json

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

import json
import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)
print(sys.path)
# moduels
from function.db_manager import ChromaManager
from gpt_data.utils.gpt_api import GPT


class MakePrompt():
    ############################## function/main.py 관련 ##############################
    def __init__(self):
        self.export_from_db_path = r'/home/data_ai/Project/gpt_data/data/export_from_db.json'
        self.prepared_prompt_path = r'/home/data_ai/Project/gpt_data/data/prepared_prompt.json'
        self.keyword_data_path = r'/home/data_ai/Project/gpt_data/data/keyword_data.json'
        
    # 군집별로 Prompt 제작하여 저장
    def set_prompt(self):
        # ChromaDB로부터 모든 데이터 불러와 군집화 후 저장 후 불러오기
        self._export_group()

        with open(self.export_from_db_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        # 군집별 Prompt 제작
        query_list = []
        for set_num, article_list in json_data.items():
            tmp_part_list = []
            for i, article in enumerate(article_list):
                tmp_part = f"{i+1}번 기사:\n{article}\n"
                tmp_part_list.append(tmp_part)
            part_prompt = ''.join(tmp_part_list)
            prompt = self._base_prompt(part_prompt)

            query_list.append(prompt)
        # 저장
        with open(self.prepared_prompt_path, 'w', encoding='utf-8') as f:
            json.dump(query_list, f, ensure_ascii=False, indent=4)
        print(f"Prompt list가 {self.prepared_prompt_path}에 저장되었습니다.")

    # ChromaDB로부터 모든 데이터 불러와 군집화 후 저장 
    def _export_group(self):
        ch = ChromaManager('summary_data')
        all_documents = ch.export_all()
        # 모든 데이터 계층 평활화
        for doc in all_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))
        # set_num 값으로 정렬
        sorted_values = sorted(all_documents, key=lambda x: x['set_num'])
        # set_num 별로 저장
        group_data = {}
        for data in sorted_values:
            if data['set_num'] not in group_data.keys():
                group_data[data['set_num']] = []
            group_data[data['set_num']].append(data['summary'])
        # 저장
        with open(self.export_from_db_path, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=4)
        print(f"DB 추출 데이터가 {self.export_from_db_path}에 저장되었습니다.")


    # function/main.py에서 직접 데이터 저장 후 KeyWord 추가하는 코드.
    def make_data_from_gpt(self):
        gpt = GPT()
        keyword_data_list = gpt.make_keyword_data(prompt_path=self.prepared_prompt_path,
                                                  save_path=self.keyword_data_path)
        
    ######################################################################
    
        
    ############################## Prompt ##############################
    # 키워드 및 한 줄 설명 생성 Prompt.
    def _base_prompt(self, part_prompt):
        prompt = f"""{part_prompt}
위 요약문들의 공통적인 내용을 가장 잘 설명할 수 있는 하나의 짧은 제목을 만드세요. 제목은 5단어 이하여야 합니다.
그리고 그 짧은 제목을 한 문장으로 설명하세요.

### 짧은 제목 :
### 한 문장 설명 :
"""
        return prompt
    
    # 같은 요약문 제목 존재 시 새 요약문 제목 만드는 Prompt.
    def _new_summary_title_prompt(self, summary):
        prompt = f"""{summary}
위 요약문의 내용을 가장 잘 설명할 수 있는 30자 이하의 요약문 제목을 만드세요. 
요약문 제목은 '주체 + 쉼표(,) + 명사구'의 형태를 원칙으로 합니다.

### 요약문 제목 :
"""
        return prompt
        
    ######################################################################


if __name__ == '__main__':
    mp = MakePrompt()
    mp.set_prompt() # 일단 저장함
    mp.make_data_from_gpt()

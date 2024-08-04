import json
import sys
BASE_DIR = '/home/data_ai/Project'
sys.path.append(BASE_DIR)
print(sys.path)
# moduels
from function.db_manager import ChromaManager
from gpt_data.utils.gpt_api import GPT

class MakePrompt():
    def __init__(self):
        self.export_from_db_path = r'/home/data_ai/Project/gpt_data/data/export_from_db.json'
        self.prepared_prompt_path = r'/home/data_ai/Project/gpt_data/data/prepared_prompt.json'
        
    # 군집별로 Prompt 제작하여 저장
    def set_prompt(self):
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
        

    def _base_prompt(self, part_prompt):
        prompt = f"""{part_prompt}
위 기사들의 공통점을 찾아 3단어 내외의 키워드를 만드세요.
그리고 그 키워드를 한 문장을 설명하세요.

### 키워드 :
### 한 문장 설명 :
"""
        return prompt
        
    # ChromaDB로부터 모든 데이터 불러와 군집화 후 저장 
    def _export_group(self):
        ch = ChromaManager('article_data')
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
            group_data[data['set_num']].append(data['document'])
        # 저장
        with open(self.export_from_db_path, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=4)
        print(f"DB 추출 데이터가 {self.export_from_db_path}에 저장되었습니다.")


if __name__ == '__main__':
    # mp = MakePrompt()
    # mp.set_prompt() # 일단 저장함

    gpt = GPT()
    json_path = r'/home/data_ai/Project/gpt_data/data/prepared_prompt.json'
    set_num = 781
    gpt.query_gpt(json_path, set_num)
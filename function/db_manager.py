import os
import hashlib
import json
from datetime import datetime
from time import sleep
from scipy.spatial.distance import cosine
# ChromaDB
import chromadb
from chromadb.config import Settings
# Modules
from config import *


class ChromaManager():
    def __init__(self, collection_name):
        # ChromaDB Client 설정
        self.chroma_client = chromadb.HttpClient(
                                        host="chromadb", 
                                        port=8000, 
                                        settings=Settings(
                                                    allow_reset=True, 
                                                    anonymized_telemetry=False,
                                                    )
                                        )
        # 일자별로 인덱스 설정
        self.date_index_path = f"{FUNCTION_DATA_DIR}{collection_name}_index.json"
        self.date_index = self._load_date_index()  # 파일에서 인덱스 로드

        # ChromaDB Collection을 가져오거나 생성함
        print(f"컬렉션 목록: {self.chroma_client.list_collections()}")
        self.collection_name = collection_name
        if collection_name not in self.chroma_client.list_collections():
            try:
                self.article_collection = \
                    self.chroma_client.get_or_create_collection(name=collection_name,
                                                                metadata={"hnsw:space": "cosine"})
                                                                #           "hnsw:M": 128,
                                                                #           "hnsw:ef": 200},
                                                                # dimensions=768)
                print(f"열린 컬렉션 : {collection_name}")
            except Exception as e:
                pass
        # self.longformer = Longformer()
    
    # 일자별 인덱스 불러오기
    def _load_date_index(self):
        if os.path.exists(self.date_index_path):
            with open(self.date_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
        
    # 일자별 인덱스 저장
    def _save_date_index(self):
        for k, v in self.date_index.items():
            self.date_index[k] = list(set(v))
        with open(self.date_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.date_index, f, ensure_ascii=False, indent=4)

    # id는 기사 본문을 이용함.
    def _make_id(self, article):
        
        article_id = hashlib.sha256(article.encode('utf-8')).hexdigest()
        
        return article_id
    
    # 데이터 저장 혹은 업데이트
    def add_or_update(self, index, embedding, media, url, 
                      title, article, article_date, 
                      summary_title, summary, summary_reason, 
                      main, sub, major_class, medium_class,
                      set_num, set_list,
                      keyword='', description=''):
            id = self._make_id(article=article)
            # 날짜 인덱스 업데이트
            index_date = article_date.split(' ')[0].strip()
            self.date_index.setdefault(index_date, []).append(id) 
            self._save_date_index()  # 인덱스를 파일에 저장
            # 데이터 추가 (upsert는 추가 및 업데이트. 추가만 하려면 add)
            self.article_collection.upsert(
                                ids=[id],
                                embeddings=[embedding],
                                documents=[article],
                                metadatas=[{'index': index,
                                            'title': title,
                                            'url': url,
                                            'media' : media,
                                            'article_date' : article_date,
                                            'summary_title': summary_title,
                                            'summary': summary,
                                            'summary_reason': summary_reason,
                                            'keyword': keyword,
                                            'description': description,
                                            'major_class': major_class,
                                            'medium_class': medium_class,
                                            'main': main,
                                            'sub': sub,
                                            'set_num': set_num,
                                            'set_list': set_list}]
                                )
            self.date_index = self._load_date_index() # 전역 변수 업데이트
            print(f"저장 완료 : {title}")
            # result = self.article_collection.get(ids=[id],
            #                                     include=['embeddings', 'documents', 'metadatas'])
            # print(result)
          

    # Keyword 업데이트 ! (데이터 업데이트 시 embeddings 필수)
    def update_keyword(self, matching_ids, keyword, description):
        try:
            result = self.article_collection.get(ids=matching_ids,
                                                 include=['embeddings', 'metadatas'])
            # 각 문서에 대해 keyword 업데이트
            updated_metadatas = []
            existing_embeddings = result['embeddings']

            for i in range(len(matching_ids)):
                metadata = result['metadatas'][i]
                metadata['keyword'] = keyword  # keyword 필드를 업데이트
                metadata['description'] = description  # description 필드를 업데이트
                updated_metadatas.append(metadata)
            
            # 업데이트된 데이터를 DB에 반영
            self.article_collection.upsert(
                ids=matching_ids,
                embeddings=existing_embeddings,
                metadatas=updated_metadatas
            )
            
            print(f"{len(matching_ids)}개의 문서에 키워드가 업데이트 되었습니다.")

        except Exception as e:
            print(f"Error updating keywords for matching IDs: {str(e)}")


    ############################## MVP API ##############################
    # MVP API - 경제 뉴스
    def get_by_medium_date(self, top_tag, middle_tag, search_date):
        if top_tag == '경제 뉴스':
            top_tag = '경제'
        middle_tag = str(middle_tag)

        # 선택 날짜의 모든 데이터 불러옴.
        response = self._get_search_date(search_date)

        # 중분류가 일치하는 데이터 가져오기
        filtered_data = []
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]
            medium_tags = [tag.strip() for tag in metadata['medium_class'].split(',')]
            # 중분류 필터를 통해 필요한 태그만 남김 (데이터에서 지우면 안 됨)
            for country in MEDIUM_TAG_FILTER:
                if country in medium_tags: 
                    medium_tags.remove(country)
            metadata['medium_class'] = ','.join(medium_tags)
            # 중분류와 대분류가 모두 일치하는 것만 선택
            if middle_tag in metadata['medium_class'] and top_tag == metadata['major_class']:
                filtered_data.append({
                            'id': response['ids'][i],
                            'document': response['documents'][i],
                            'metadata': metadata
                        })
        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        # metadatas 하위 key들을 한단계 올림.
        sorted_data = self._get_sorted_data(filtered_data)
        # 최종적으로 summary_title, summary, medium_class, main, article_date, url 만 반환
        final_results = self._final_results_form(sorted_data)

        return final_results

    # MVP API - 기업 키워드
    def get_by_main_date(self, main_tag, search_date):
        # 선택 날짜의 모든 데이터 불러옴.
        response = self._get_search_date(search_date)

        # Main Match DB에서 상품명 및 기업아명 가져오기
        with open(MAIN_TAG_MATCH_DB, 'r', encoding='utf-8') as file:
            main_match_db = json.load(file)
        try:
            matched_main_list = main_match_db[main_tag]
        except:
            matched_main_list = []

        # 조건에 맞는 데이터를 필터링
        filtered_data = []
        seen_ids = set()  # 이미 추가된 id를 추적하는 집합
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]
            # 상품명 및 기업아명 순환하며 필터링
            for main in matched_main_list:
                if main in metadata['main']: # ex) 삼성전자 in 삼성전자서비스
                    if response['ids'][i] in seen_ids:
                        continue
                    filtered_data.append({
                        'id': response['ids'][i],
                        'document': response['documents'][i],
                        'metadata': metadata
                    })
                    seen_ids.add(response['ids'][i])

        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        # metadatas 하위 key들을 한단계 올림.
        sorted_data = self._get_sorted_data(filtered_data)

        # 최종적으로 keyword, summary_title 만 반환
        main_results = []
        for item in sorted_data:
            main_results.append({
                'id': item.get('id'),
                'keyword': item.get('keyword'),
                'summary_title': item.get('summary_title'),
                'article_date': item.get('article_date')
            })
        
        return main_results
    
    
    # MVP API - 키워드 선택시 요약문 리스트 반환
    def get_by_ids(self, search_ids):
        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=search_ids)
        
        filtered_data = []
        for i in range(len(response['documents'])):
            metadata = response['metadatas'][i]
            medium_tags = [tag.strip() for tag in metadata['medium_class'].split(',')]
            # 중분류 필터를 통해 필요한 태그만 남김 (데이터에서 지우면 안 됨)
            for country in MEDIUM_TAG_FILTER:
                if country in medium_tags: 
                    medium_tags.remove(country)
            response['metadatas'][i]['medium_class'] = ','.join(medium_tags)

            filtered_data.append({
                        'id': response['ids'][i],
                        'document': response['documents'][i],
                        'metadata': metadata
                    })
        
        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        sorted_data = self._get_sorted_data(filtered_data)
        # 최종적으로 summary_title, summary, medium_class, main, article_date, url 만 반환
        final_results = self._final_results_form(sorted_data)
        
        return final_results
    ######################################################################

    ############################## Utils ##############################
    # 최종적으로 summary_title, summary, medium_class, main, article_date, url 만 반환
    def _final_results_form(self, sorted_data):
        final_results = []
        for item in sorted_data:
            final_results.append({
                'summary_title': item.get('summary_title'),
                'summary': item.get('summary'),
                'medium_class': item.get('medium_class'),
                'main': item.get('main'),
                'article_date': item.get('article_date'),
                'url': item.get('url')
            })
        return final_results
    
    # 일자별로 모든 데이터 가져오기
    def _get_search_date(self, search_date):
        self.date_index = self._load_date_index()  # 파일에서 인덱스 로드
        if search_date not in self.date_index:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            self.date_index[search_date] = []
        matching_ids = self.date_index[search_date]
        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=matching_ids,
                                               include=['documents',
                                                        'embeddings', 
                                                        'metadatas'])
        return response
    
    # 시간 순으로 정렬
    def _get_sorted_data(self, filtered_data):
        # metadata 키들을 상위 계층으로 이동하고 metadata는 제거
        for item in filtered_data:
            metadata = item.pop('metadata')
            item.update(metadata)

        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        sorted_data = sorted(filtered_data, key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)
        return sorted_data
    
    # 코사인 계산 함수
    def _calculate_distance(self, embedding1, embedding2):
        # 두 임베딩 간의 코사인 거리를 계산하는 함수
        return cosine(embedding1, embedding2)
    
    ######################################################################
    

    ############################## 관리 페이지 ##############################
    # MVP 관리 페이지 - 저장 버튼
    def update_specific_metadata_fields(self, id, search_date=None, 
                                        summary_title=None, summary=None, 
                                        keyword=None, set_num=None, 
                                        major_class=None, medium_class=None, 
                                        main=None, sub=None):
        # 기존 키워드 추출
        origin_document = self.article_collection.get(ids=[id])
        origin_keyword = origin_document['metadatas'][0]['keyword']
        # 일자별로 모든 데이터 가져오기
        response = self._get_search_date(search_date)
        
        try:
            for i in range(len(response['ids'])):
                existing_id = response['ids'][i]
                existing_embedding = response['embeddings'][i]
                existing_metadata = response["metadatas"][i]

                if origin_keyword == existing_metadata['keyword']:
                    if id == existing_id:
                        # Update only the provided fields
                        if summary_title is not None:
                            existing_metadata["summary_title"] = summary_title
                        if summary is not None:
                            existing_metadata["summary"] = summary
                        if keyword is not None:
                            existing_metadata["keyword"] = keyword
                        if set_num is not None:
                            existing_metadata["set_num"] = int(set_num)
                        if major_class is not None:
                            existing_metadata["major_class"] = major_class
                        if medium_class is not None:
                            existing_metadata["medium_class"] = medium_class
                        if main is not None:
                            existing_metadata["main"] = main
                        if sub is not None:
                            existing_metadata["sub"] = sub
                    elif id != existing_id:
                        if keyword is not None:
                            existing_metadata["keyword"] = keyword

                    # Perform upsert with the updated metadata
                    self.article_collection.upsert(
                        ids=[existing_id],
                        embeddings=[existing_embedding],
                        metadatas=[existing_metadata]
                    )
                    print(f"Metadata updated for ID: {existing_id}")
        except Exception as e:
            print(f"Error updating keywords for matching IDs: {str(e)}")

    
    # 날짜 + 메인 | 중분류 입력 버튼
    def get_by_main_and_date(self, 
                             main_tag='', 
                             medium_class='', 
                             search_date=''):
        # 일자별로 모든 데이터 가져오기
        response = self._get_search_date(search_date)

        # Main Match DB 가져오기 
        with open(MAIN_TAG_MATCH_DB, 'r', encoding='utf-8') as file:
            main_match_db = json.load(file)
        try:
            matched_main_list = main_match_db[main_tag]
        except:
            matched_main_list = []

        # 조건에 맞는 데이터를 필터링
        filtered_data = []
        seen_ids = set()  # 이미 추가된 id를 추적하는 집합
        for i in range(len(response['documents'])):
            metadata = response['metadatas'][i]
            # main_tags = [tag.strip() for tag in metadata['main'].split(',')]  # main 필드를 콤마로 분할하고 strip() 적용
            medium_classes = [category.strip() for category in metadata['medium_class'].split(',')] 

            for main in matched_main_list:
                if main in metadata['main']:
                    if response['ids'][i] in seen_ids:
                        continue
                    filtered_data.append({
                        'id': response['ids'][i],
                        'document': response['documents'][i],
                        'metadata': metadata
                    })
                    seen_ids.add(response['ids'][i])

            if medium_class in medium_classes:
                if response['ids'][i] in seen_ids:
                    continue
                filtered_data.append({
                    'id': response['ids'][i],
                    'document': response['documents'][i],
                    'metadata': metadata
                })
                seen_ids.add(response['ids'][i])
        # print(len(filtered_data))
        return filtered_data
    
    
    ############################## Save Function ##############################
    ### Get ###
    # 가장 최근 데이터의 송고시간, 세트 넘버, 기사 인덱스 가져오기.
    def get_most_recent_items(self):
        last_date = max(self.date_index.keys())
        matching_ids = self.date_index[last_date]
        response = self.article_collection.get(ids=matching_ids)

        most_recent_date = None
        most_recent_date_raw = None
        most_recent_set_num = 0
        most_recent_index = 0

        # Iterate through fetched documents to find the most recent one
        for i in range(len(response['documents'])):
            article_date = response['metadatas'][i]['article_date']
            article_date_dt_raw = datetime.strptime(article_date, '%Y-%m-%d %H:%M')  # Adjust format if needed
            article_date_dt = article_date_dt_raw.strftime('%m-%d %H:%M')

            if most_recent_date is None or article_date_dt > most_recent_date:
                most_recent_date = article_date_dt
                most_recent_date_raw = article_date_dt_raw

            article_set_num = int(response['metadatas'][i]['set_num'])
            if article_set_num > most_recent_set_num:
                most_recent_set_num = article_set_num

            article_index = int(response['metadatas'][i]['index'])
            if article_index > most_recent_index:
                most_recent_index = article_index

        return str(most_recent_date), most_recent_set_num, \
                most_recent_index, str(most_recent_date_raw)
    
    
    # 날짜 + 세트 넘버 일치 항목 검색
    def get_by_setnum_date(self, set_num, search_date):
        response = self._get_search_date(search_date)

        # 조건에 맞는 데이터를 필터링
        filtered_data = []
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]

            if set_num == metadata['set_num']:
                filtered_data.append({
                    'id': response['ids'][i],
                    'document': response['documents'][i],
                    'metadata': metadata
                })

        return filtered_data
    
    # 가장 최근 저장 기사 제목 가져오기.
    def get_most_recent_titles(self, search_date, search_time):
        response = self._get_search_date(search_date)

        recent_title_list = []
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]
            if search_time == metadata['article_date']: 
                recent_title_list.append(metadata['title'])
        return recent_title_list
    

    ### Search ### 
    def search(self, embedding, search_date):
        self.date_index = self._load_date_index()  # 파일에서 인덱스 로드
        if search_date not in self.date_index:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return []
        matching_ids = self.date_index[search_date]
        
        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=matching_ids,
                                               include=['embeddings', 'metadatas'])

        # 데이터가 없을 경우 빈 리스트 반환
        if not response or not response['ids']:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return []

        # 필터링된 데이터에서 임베딩을 비교하여 검색 결과 구성
        filtered_results = []
        for i, id in enumerate(response['ids']):
            db_embedding = response['embeddings'][i]
            distance = cosine(embedding, db_embedding)  # 코사인 거리 계산
            filtered_results.append({
                'id': response['ids'][i],
                'embedding': response['embeddings'][i],
                'distance': distance,
                'metadata': response['metadatas'][i]
            })

        # 검색 결과를 거리순으로 정렬
        filtered_results = sorted(filtered_results, key=lambda x: x['distance'])

        # 필요에 따라 상위 n_results 개수만큼 반환
        n_results = 20
        return filtered_results[:n_results]
    
        
    # 동일 기사 제목 및 기사 본문 일 경우 무시 기능
    def search_same_title(self, search_date, search_title):
        response = self._get_search_date(search_date)

        filtered_data = []
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]

            if search_title == metadata['title']:
                filtered_data.append({
                            'id': response['ids'][i],
                            'document': response['documents'][i],
                            'metadata': metadata
                        })
        sorted_data = self._get_sorted_data(filtered_data)
        return sorted_data
    
    # 동일 요약문 제목일 경우 GPT4로 제목 새로 지으러 보내기
    def search_same_summary_title(self, search_date, summary_title):
        response = self._get_search_date(search_date)
        
        filtered_data = []
        for i in range(len(response['ids'])):
            metadata = response['metadatas'][i]

            if summary_title == metadata['summary_title']:
                filtered_data.append({
                            'id': response['ids'][i],
                            'document': response['documents'][i],
                            'metadata': metadata
                        })
        sorted_data = self._get_sorted_data(filtered_data)
        return sorted_data


    ### Get ###
    # ID로 데이터 검색
    def get_data(self, db_id):
        response = self.article_collection.get(ids=[db_id])
        if response['ids']:
            data = {
                'id': response['ids'][0],
                'document': response['documents'][0],
                'metadata': response['metadatas'][0]
            }
            return data
        else:
            print("해당 ID에 대한 데이터를 찾을 수 없습니다.")
            return None
        
    # 날짜로 데이터 검색
    def get_data_from_date(self, search_date):
        if search_date in self.date_index:
            matching_ids = self.date_index[search_date]
            response = self.article_collection.get(ids=matching_ids)
            return [{
                'id': response['ids'][i],
                'document': response['documents'][i],
                'metadata': response['metadatas'][i]
            } for i in range(len(response['ids']))]
        else:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return None
        
    
    # 임시로 지난 날짜의 최종 set_num 가져오기
    def get_tmp_last_setnum(self, search_date):
        matching_ids = self.date_index[search_date]
        response = self.article_collection.get(ids=matching_ids)

        tmp_last_set_num = 0

        # Iterate through fetched documents to find the most recent one
        for i in range(len(response['documents'])):

            article_set_num = int(response['metadatas'][i]['set_num'])
            if article_set_num > tmp_last_set_num:
                tmp_last_set_num = article_set_num

        return tmp_last_set_num
        
    # collection 내의 모든 데이터 추출
    def export_all(self):
        # Initialize an empty list to store all documents
        all_documents = []
        start = 0
        batch_size = 1000  # Adjust the batch size as needed

        while True:
            # Fetch documents in batches
            response = self.article_collection.get(
                limit=batch_size,
                offset=start
            )
            
            if not response['documents']:
                break

            # Append fetched documents to the list
            for i in range(len(response['documents'])):
                entry = {
                    'id': response['ids'][i],
                    'document': response['documents'][i],
                    'metadata': response['metadatas'][i] 
                }
                all_documents.append(entry)

            # Update the starting point for the next batch
            start += batch_size

        # # Convert to JSON format
        # json_data = json.dumps(all_documents, indent=4, ensure_ascii=False)

        
        # # Print or save JSON data
        # with open('/home/data_ai/Project/function/data/exported_data.json', 'w', encoding='utf-8') as f:
        #     f.write(json_data)
        
        # print("Data exported to exported_data.json")

        return all_documents
    


    # collection 삭제
    def delete_collection(self, method='delete_all_data'):
        try:
            if method == 'delete_collection': # 컬렉션 삭제
                self.chroma_client.delete_collection(name=self.collection_name)
                print("컬렉션 삭제 완료")
            elif method == 'delete_all_data': # 데이터 모두 삭제
                all_ids = self.article_collection.get()['ids']
                self.article_collection.delete(ids=all_ids)
                print("데이터 삭제 완료")
            else :
                print("method를 명확히 지정하십시오.")
        except Exception as e:
            print(f"삭제 중 문제 발생 : {e}")

    # collection 내의 데이터만 전부 삭제.
    def delete_data(self, del_id):
        try:
            self.article_collection.delete(ids=del_id)
            print(f"Successfully deleted data with id: {del_id}")
        except Exception as e:
            print(f"Error deleting data: {e}")


    def save_to_json(self, file_path):
        try:
            data = self.article_collection.get()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"데이터가 {file_path}에 저장되었습니다.")
        except Exception as e:
            print(f"데이터 저장 중 오류가 발생했습니다: {e}")

    def load_from_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ids = data['ids']
            embeddings = data['embeddings']
            documents = data['documents']
            metadatas = data['metadatas']
            self.article_collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
            print(f"{file_path}로부터 데이터가 불러와졌습니다.")
        except Exception as e:
            print(f"데이터 불러오기 중 오류가 발생했습니다: {e}")

    ######################################################################
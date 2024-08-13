import os
import hashlib
import json
from datetime import datetime

import requests

# chroma_url = 'http://chromadb:8000/api_endpoint'  

# response = requests.get(chroma_url)
# print(response.json())

import chromadb
from chromadb.config import Settings


class ChromaManager():
    def __init__(self, collection_name):
        self.chroma_client = chromadb.HttpClient(
                                        host="chromadb", 
                                        port=8000, 
                                        settings=Settings(
                                                    allow_reset=True, 
                                                    anonymized_telemetry=False,
                                                    )
                                        )
        self.date_index_path = f"/home/data_ai/Project/function/data/{collection_name}_index.json"
        self.date_index = self._load_date_index()  # 파일에서 인덱스 로드

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
        
    def _load_date_index(self):
        if os.path.exists(self.date_index_path):
            with open(self.date_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}

    def _save_date_index(self):
        for k, v in self.date_index.items():
            self.date_index[k] = list(set(v))
        with open(self.date_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.date_index, f, ensure_ascii=False, indent=4)
    
    def add_or_update(self, index, embedding, media, url, 
                      title, article, article_date, 
                      summary_title, summary, summary_reason, 
                      main, sub, major_class, medium_class,
                      set_num, set_list):
            id = self._make_id(article=article)
            # 날짜 인덱스 업데이트
            index_date = article_date.split(' ')[0].strip()
            self.date_index.setdefault(index_date, []).append(id) 
            self._save_date_index()  # 인덱스를 파일에 저장
            # 데이터 추가 (upsert는 업데이트. 추가만 하려면 add)
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
                                            'keyword': '',
                                            'description': '',
                                            'major_class': major_class,
                                            'medium_class': medium_class,
                                            'main': main,
                                            'sub': sub,
                                            'set_num': set_num,
                                            'set_list': set_list}]
                                )
            print(f"저장 완료 : {title}")
            # result = self.article_collection.get(ids=[id],
            #                                     include=['embeddings', 'documents', 'metadatas'])
            # print(result)
            
    # 관리 페이지 저장 버튼
    def update_specific_metadata_fields(self, id, summary_title=None, summary=None, 
                                        major_class=None, medium_class=None, 
                                        main=None, sub=None):
        try:
            result = self.article_collection.get(ids=[id],
                                                 include=['embeddings', 'metadatas'])
            existing_embeddings = result['embeddings'][0]
            existing_metadata = result["metadatas"][0]


            # Update only the provided fields
            if summary_title is not None:
                existing_metadata["summary_title"] = summary_title
            if summary is not None:
                existing_metadata["summary"] = summary
            if major_class is not None:
                existing_metadata["major_class"] = major_class
            if medium_class is not None:
                existing_metadata["medium_class"] = medium_class
            if main is not None:
                existing_metadata["main"] = main
            if sub is not None:
                existing_metadata["sub"] = sub

            # Perform upsert with the updated metadata
            self.article_collection.upsert(
                ids=[id],
                embeddings=[existing_embeddings],
                metadatas=[existing_metadata]
            )
            print(f"Metadata updated for ID: {id}")

        except Exception as e:
            print(f"Error updating metadata for ID: {id}: {str(e)}")

    # Keyword 업데이트 !
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
                metadata['description'] = description  # keyword 필드를 업데이트
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

    # MVP API - 경제 뉴스
    def get_by_medium_date(self, topTag, middleTag, searchDate):
        if topTag == '경제 뉴스':
            topTag = '경제'
        middleTag = str(middleTag)

        all_results = []

        start = 0
        batch_size = 1000  # 한 번에 가져올 문서 수, 필요에 따라 조정 가능

        while True:
            # 모든 데이터를 batch 단위로 가져오기
            response = self.article_collection.get(
                limit=batch_size,
                offset=start
            )

            # 더 이상 가져올 데이터가 없으면 종료
            if not response['documents']:
                break

            # 가져온 데이터 중에서 조건에 맞는 것 필터링
            for i in range(len(response['documents'])):
                metadata = response['metadatas'][i]
                db_date = metadata['article_date'].split(' ')[0]  # 시간 부분 제거, 날짜만 추출
                medium_classes = metadata['medium_class'].split(',')  # 콤마로 구분된 medium_class 분할

                if db_date == searchDate and middleTag in medium_classes and metadata['major_class'] == topTag:
                    all_results.append({
                        'id': response['ids'][i],
                        'document': response['documents'][i],
                        'metadata': metadata
                    })

            # 다음 batch를 가져오기 위해 offset 업데이트
            start += batch_size

        # metadata 키들을 상위 계층으로 이동하고 metadata는 제거
        for item in all_results:
            metadata = item.pop('metadata')
            item.update(metadata)

        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        sorted_data = sorted(all_results, key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

        # 최종적으로 summary_title, summary, medium_class, main, article_date, url 만 반환
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
    
    # MVP API - 기업 키워드
    def get_by_main_date(self, main_tag, search_date):
        # search_date와 일치하는 ID 목록 가져오기
        if search_date not in self.date_index:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return []
        matching_ids = self.date_index[search_date]

        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=matching_ids)

        # Main DB에서 상품명 및 기업아명 가져오기
        main_match_db_path = r'/home/data_ai/Project/function/data/main_match_db.json'
        with open(main_match_db_path, 'r', encoding='utf-8') as file:
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

        # metadata 키들을 상위 계층으로 이동하고 metadata는 제거
        for item in filtered_data:
            metadata = item.pop('metadata')
            item.update(metadata)

        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        sorted_data = sorted(filtered_data, key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

        # 최종적으로 keyword, summary_title 만 반환
        final_results = []
        for item in sorted_data:
            final_results.append({
                'id': item.get('id'),
                'keyword': item.get('keyword'),
                'summary_title': item.get('summary_title'),
                'article_date': item.get('article_date')
            })
        
        return final_results
    
    # MVP API - 키워드 선택시 요약문 리스트 반환
    def get_by_ids(self, search_ids):
        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=search_ids)
        
        filtered_data = []
        for i in range(len(response['documents'])):
            metadata = response['metadatas'][i]
            filtered_data.append({
                        'id': response['ids'][i],
                        'document': response['documents'][i],
                        'metadata': metadata
                    })
        # metadata 키들을 상위 계층으로 이동하고 metadata는 제거
        for item in filtered_data:
            metadata = item.pop('metadata')
            item.update(metadata)

        # article_date를 datetime 객체로 변환하여 내림차순 정렬
        sorted_data = sorted(filtered_data, key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)
        
        # 최종적으로 summary_title, summary, medium_class, main, article_date, url 만 반환
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
    

    def _make_id(self, article):
        
        article_id = hashlib.sha256(article.encode('utf-8')).hexdigest()
        
        return article_id

    # 날짜 + set_mum 일치 항목 검색
    def get_by_setnum_date(self, set_num, search_date):
        # search_date와 일치하는 ID 목록 가져오기
        if search_date not in self.date_index:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return []
        matching_ids = self.date_index[search_date]

        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=matching_ids)

        # 조건에 맞는 데이터를 필터링
        filtered_data = []
        for i in range(len(response['documents'])):
            metadata = response['metadatas'][i]

            if set_num == metadata['set_num']:
                filtered_data.append({
                    'id': response['ids'][i],
                    'document': response['documents'][i],
                    'metadata': metadata
                })

        return filtered_data


    # 날짜 + 메인 | 중분류 입력 버튼
    def get_by_main_and_date(self, 
                             main_tag='', 
                             medium_class='', 
                             search_date=''):
        # search_date와 일치하는 ID 목록 가져오기
        if search_date not in self.date_index:
            print(f"{search_date}에 대한 데이터를 찾을 수 없습니다.")
            return []
        matching_ids = self.date_index[search_date]

        # 해당 ID 목록에 대해 데이터를 가져오기
        response = self.article_collection.get(ids=matching_ids)

        # Main Match DB 가져오기
        main_match_db_path = r'/home/data_ai/Project/function/data/main_match_db.json'
        with open(main_match_db_path, 'r', encoding='utf-8') as file:
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
        print(len(filtered_data))
        return filtered_data
    

    def search(self, embedding, search_date):
        # try :
        #     matching_ids = self.date_index[search_date]
        # except:
        #     self.date_index[search_date] = []
        #     matching_ids = self.date_index[search_date]
        
        # # 해당 날짜의 ID에 대해 쿼리 수행
        # response = self.article_collection.query(
        #     query_embeddings=embedding,
        #     n_results=len(matching_ids),  # 해당 날짜에 있는 모든 ID와 비교
        #     where={"index": {"$in": matching_ids}}  # 메타 데이터만 사용 가능
        # )
        # # 유사도가 높은 순으로 정렬된 결과를 반환
        # results = []
        # for i in range(len(response['ids'][0])):
        #     results.append({
        #         'id': response['ids'][0][i],
        #         'distance': response['distances'][0][i],
        #         'document': response['documents'][0][i],
        #         'metadata': response['metadatas'][0][i]
        #     })

        # # 상위 20개 결과 반환
        # return results[:20]

        response = self.article_collection.query(
            query_embeddings=embedding,
            n_results=50,
        )
        # where에서 앞에 날짜 부분만 매칭할 수 있게 해야함.
        filtered_results = []
        for i, metadata in enumerate(response['metadatas'][0]):
            db_date = metadata['article_date']
            if db_date.startswith(search_date):
                filtered_results.append({
                    'id': response['ids'][0][i],
                    'distance': response['distances'][0][i],
                    'document': response['documents'][0][i],
                    'metadata': metadata
                })
        # 필요에 따라 상위 n_results 개수만큼 반환
        n_results = 20
        return filtered_results[:n_results]
    
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
    

    def get_most_recent_items(self):
        last_date = max(self.date_index.keys())
        matching_ids = self.date_index[last_date]
        response = self.article_collection.get(ids=matching_ids)

        most_recent_date = None
        most_recent_set_num = 0
        most_recent_index = 0

        # Iterate through fetched documents to find the most recent one
        for i in range(len(response['documents'])):
            article_date = response['metadatas'][i]['article_date']
            article_date_dt = datetime.strptime(article_date, '%Y-%m-%d %H:%M')  # Adjust format if needed
            article_date_dt = article_date_dt.strftime('%m-%d %H:%M')

            if most_recent_date is None or article_date_dt > most_recent_date:
                most_recent_date = article_date_dt

            article_set_num = int(response['metadatas'][i]['set_num'])
            if article_set_num > most_recent_set_num:
                most_recent_set_num = article_set_num

            article_index = int(response['metadatas'][i]['index'])
            if article_index > most_recent_index:
                most_recent_index = article_index



        return str(most_recent_date), most_recent_set_num, most_recent_index
    

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
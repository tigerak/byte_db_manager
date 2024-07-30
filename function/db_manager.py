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
        print(self.chroma_client.list_collections())
        self.collection_name = collection_name
        if collection_name not in self.chroma_client.list_collections():
            try:
                self.article_collection = \
                    self.chroma_client.get_or_create_collection(name=collection_name,
                                                                metadata={"hnsw:M": 64})
                print(f"열린 컬렉션 : {collection_name}")
            except Exception as e:
                pass
        
    def add_or_update(self, embedding, media, url, 
                      title, article, article_date, 
                      summary_title, summary, summary_reason, 
                      main, sub, major_class, medium_class,
                      set_num):
            id = self._make_id(article=article)
            # 데이터 추가 (upsert는 업데이트. 추가만 하려면 add)
            self.article_collection.upsert(
                                ids=[id],
                                embeddings=[embedding],
                                documents=[article],
                                metadatas=[{'title' : title,
                                            'url': url,
                                            'media' : media,
                                            'article_date' : article_date,
                                            'summary_title': summary_title,
                                            'summary': summary,
                                            'summary_reason': summary_reason,
                                            'major_class': major_class,
                                            'medium_class': medium_class,
                                            'main': main,
                                            'sub': sub,
                                            'set_num': set_num}]
                                )
            print(f"저장 완료 : {title}")
            

    def _make_id(self, article):
        
        article_id = hashlib.sha256(article.encode('utf-8')).hexdigest()
        
        return article_id

    def search(self, embedding, search_date):
        response = self.article_collection.query(
            query_embeddings=embedding,
            n_results=20,
        )
        # where에서 앞에 날짜 부분만 매칭할 수 있게 해야함.
        filtered_results = []
        for i, metadata in enumerate(response['metadatas'][0]):
            db_date = metadata['article_date']
            if db_date.startswith(search_date):
                filtered_results.append({
                    'ids': response['ids'][0][i],
                    'distances': response['distances'][0][i],
                    'document': response['documents'][0][i],
                    'metadata': metadata
                })
        # 필요에 따라 상위 n_results 개수만큼 반환
        n_results = 20
        return filtered_results[:n_results]
    
    def export_all(self):
        # Initialize an empty list to store all documents
        all_documents = []
        start = 0
        batch_size = 100  # Adjust the batch size as needed

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
    

    def get_most_recent_date_and_setnum(self):
        most_recent_article = None
        most_recent_date = None
        most_recent_set_num = 0
        start = 0
        batch_size = 100  # Adjust the batch size as needed

        while True:
            # Fetch documents in batches
            response = self.article_collection.get(
                limit=batch_size,
                offset=start
            )

            if not response['documents']:
                break

            # Iterate through fetched documents to find the most recent one
            for i in range(len(response['documents'])):
                article_date = response['metadatas'][i]['article_date']
                article_date_dt = datetime.strptime(article_date, '%Y-%m-%d %H:%M')  # Adjust format if needed
                article_date_dt = article_date_dt.strftime('%m-%d %H:%M')

                if most_recent_date is None or article_date_dt > most_recent_date:
                    most_recent_date = article_date_dt

                article_set_num = response['metadatas'][i]['set_num']
                
                if article_set_num > most_recent_set_num:
                    most_recent_set_num = article_set_num

            # Update the starting point for the next batch
            start += batch_size

        return str(most_recent_date), most_recent_set_num
    

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
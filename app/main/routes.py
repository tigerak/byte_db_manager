import json
import logging

from flask import request, jsonify
# modules
from app.main import bp
from function.db_manager import ChromaManager


article_chromadb = ChromaManager(collection_name='article_data')
summary_chromadb = ChromaManager(collection_name='summary_data')
ytn_chromadb = ChromaManager(collection_name='ytn_data')

@bp.route('/')
def index():
    print('접근함!!')
    return jsonify(
        message="You're connected to the Data Manage Server API !!",
        contant={
            "key":"Make Somthing",
            "value":"I have No Idea :["
        }
        )
    # return "You're connected to the Main Server API !!"

@bp.route('/api', methods=['POST'])
def get_data():
    data = request.form
    # collection 선택
    collection_name = data.get('getDataAPI')
    if collection_name == 'ArticleBase':
        chromadb = article_chromadb
    elif collection_name == 'SummaryBase':
        chromadb = summary_chromadb
    elif collection_name == 'YtnBase':
        chromadb = ytn_chromadb
    
    # db_manager 페이지에서 삭제 버튼 누른 경우
    if data['buttonId'] == 'delButton':
        db_id = data['dbIdDiv']
        chromadb.delete_data(del_id=db_id)
        return_message = '기사가 삭제되었습니다. :['
        return jsonify(return_message)
    
    # db_manager 페이지에서 기사 보기 버튼 누른 경우
    elif data['buttonId'] == 'view-article':
        db_id = data['showIdData']
        document = chromadb.get_data(db_id=db_id)
        if 'metadata' in document:
            document.update(document.pop('metadata'))
        
        # 웹용 set_list 만들기
        send_set_list = []
        if document['set_list'] != '':
            set_list = document['set_list'].split(', ')
            for set in set_list:
                set = set.split('->')
                set[2] = round(float(set[2]),3)
                send_set_list.append(set)
        sorted_set_list = sorted(send_set_list, key=lambda x: int(x[0]))

        document['similarity_list'] = sorted_set_list
        return jsonify(document)
    
    # db_manager 페이지에서 DB 가져오기 버튼 누른 경우 
    elif data['buttonId'] == 'get_data':
        all_documents = chromadb.export_all()
        for doc in all_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))
        # article_date, set_num, index 순으로 올림차순 정렬
        sorted_values = sorted(all_documents, key=lambda x: (x['article_date'].split(' ')[0],
                                                             x['set_num'], 
                                                             x['index']))
        
        return jsonify(sorted_values)
    
    # db_manager 페이지에서 저장하기 버튼 누른 경우 
    elif data['buttonId'] == 'saveButton':
        chromadb.update_specific_metadata_fields(
                        id=data['dbIdDiv'],
                        summary_title=data['modelTitle'],
                        summary=data['modelSummary'],
                        major_class=data['majorTagDiv'],
                        medium_class=data['mediumTagDiv'],
                        main=data['mainTagDiv'],
                        sub=data['subTagDiv']
        )
        return_message = '기사가 저장되었습니다 !!!'
        return jsonify(return_message)
    
    # API 테스트 버튼
    elif data['buttonId'] == 'getSearchDataButton':
        search_date = data['searchDate']
        main_tag = data['searchTag']
        search_documents = chromadb.get_by_main_and_date(main_tag=main_tag,
                                                         search_date=search_date)
        for doc in search_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))
        # article_date, set_num, index 순으로 올림차순 정렬
        sorted_values = sorted(search_documents, key=lambda x: (x['article_date'].split(' ')[0],
                                                                x['set_num'], 
                                                                x['index']))
        
        return jsonify(sorted_values)

@bp.route('/api/mvp', methods=['POST'])
def mvp_test():
    logging.basicConfig(filename='/home/data_ai/Project/app/gunicorn.log', level=logging.INFO)
    
    data = request.get_json()

    topTag = data['topTag']
    middleTag = data['middleTag']
    searchDate = data['searchDate']

    
    response = summary_chromadb.search_by_tags_and_date(topTag=topTag,
                                                    middleTag=middleTag,
                                                    searchDate=searchDate)
    
    return jsonify(response)
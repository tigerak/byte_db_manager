import json

from flask import request, jsonify
# modules
from app.main import bp
from function.db_manager import ChromaManager


article_chromadb = ChromaManager(collection_name='article_data')
summary_chromadb = ChromaManager(collection_name='summary_data')

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

    # db_manager 페이지에서 삭제 버튼 누른 경우
    if 'dbIdDiv' in data.keys():
        db_id = data['dbIdDiv']
        chromadb.delete_data(del_id=db_id)
        return_message = {'articleDiv': '기사가 삭제되었습니다. :['}
        return jsonify(return_message)
    # db_manager 페이지에서 기사 보기 버튼 누른 경우
    elif 'showIdData' in data.keys():
        db_id = data['showIdData']
        document = chromadb.get_data(db_id=db_id)
        if 'metadata' in document:
            document.update(document.pop('metadata'))
        
        send_set_list = []
        if document['set_list'] != '':
            set_list = document['set_list'].split(', ')
            for set in set_list:
                set = set.split('->')
                set[2] = round(float(set[2]),3)
                send_set_list.append(set)
        sorted_set_list = sorted(send_set_list, key=lambda x: int(x[0]))
        response = {
            'titleDiv': document['title'],
            'mediaDiv': document['media'],
            'dateDiv': document['article_date'],
            'dbIdDiv': document['id'],
            'articleDiv': document['document'],
            'similarityDiv': sorted_set_list,
            'modelTitle': document['summary_title'],
            'modelSummary': document['summary'],
            'modelReason': document['summary_reason'] + "\n" \
                            + "기업 태그(Company Tag):\n" \
                            + "Main:" + document['main'] + "\n" \
                            + "Sub:" + document['sub'] + "\n" \
                            + "대분류(Major Classification):\n" \
                            + document['major_class'] + "\n" \
                            + "중분류(Medium Classification):\n" \
                            + document['medium_class']
        }
        return jsonify(response)
    # db_manager 페이지에서 DB 가져오기 버튼 누른 경우
    elif 'getDataAPI' in data.keys():
        all_documents = chromadb.export_all()
        for doc in all_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))

        # set_num 값으로 정렬
        sorted_values = sorted(all_documents, key=lambda x: (x['set_num'], x['index']))
        
        return jsonify(sorted_values)
    

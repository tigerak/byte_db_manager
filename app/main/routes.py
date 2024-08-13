import json
import logging
from datetime import datetime

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
        main_tag = data['searchTag'] if data['searchTag'] != '' else '없음'
        medium_class = data['searchCategory'] if data['searchCategory'] != '' else '없음'

        search_documents = chromadb.get_by_main_and_date(main_tag=main_tag,
                                                         medium_class=medium_class,
                                                         search_date=search_date)
        for doc in search_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))
        # article_date, set_num, index 순으로 올림차순 정렬
        sorted_values = sorted(search_documents, key=lambda x: (x['article_date'].split(' ')[0],
                                                                x['set_num'], 
                                                                x['index']))
        
        return jsonify(sorted_values)



############################## API ##############################
@bp.route('/api/mvp/economy', methods=['POST'])
def mvp_economy():
    # logging.basicConfig(filename='/home/data_ai/Project/app/gunicorn.log', level=logging.INFO)
    
    data = request.get_json()

    topTag = data['topTag']
    middleTag = data['middleTag']
    searchDate = data['searchDate']
    
    response = ytn_chromadb.get_by_medium_date(topTag=topTag,
                                               middleTag=middleTag,
                                               searchDate=searchDate)
    
    return jsonify(response)


@bp.route('/api/mvp/kos', methods=['POST'])
def mvp_kos():
    data = request.get_json()

    topTag = data['topTag']
    main_tag = data['middleTag']
    search_date = data['searchDate']

    response = ytn_chromadb.get_by_main_date(main_tag=main_tag,
                                             search_date=search_date)
    # final_results에서 keyword를 기준으로 데이터를 묶음
    grouped_results = {}

    for item in response:
        id = item.get('id')
        keyword = item.get('keyword')
        summary_title = item.get('summary_title')
        article_date = item.get('article_date')
        
        if keyword in grouped_results:
            grouped_results[keyword].append({
                'id': id,
                'summary_title': summary_title,
                'article_date': article_date
            })
        else:
            grouped_results[keyword] = [{
                'id': id,
                'summary_title': summary_title,
                'article_date': article_date
            }]

    # 각 키워드 내에서 summary_title을 최신 시간 기준으로 정렬
    for keyword in grouped_results:
        grouped_results[keyword] = sorted(grouped_results[keyword], key=lambda x: datetime.strptime(x['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

    # 키워드를, 그 키워드의 최신 summary_title의 시간 기준으로 정렬
    grouped_list_sorted = sorted(grouped_results.items(), key=lambda x: datetime.strptime(x[1][0]['article_date'], '%Y-%m-%d %H:%M'), reverse=True)

    return jsonify(grouped_list_sorted)

@bp.route('/api/mvp/kos/keyword', methods=['POST'])
def mvp_kos_keyword():
    search_ids = request.get_json()

    response = ytn_chromadb.get_by_ids(search_ids)

    return jsonify(response)

######################################################################
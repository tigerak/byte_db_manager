import json

from flask import request, jsonify
# modules
from app.main import bp
from function.db_manager import ChromaManager


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
    collection_name = 'article_data'
    chromadb = ChromaManager(collection_name=collection_name)
    data = request.form

    if 'dbIdDiv' in data.keys():
        db_id = data['dbIdDiv']
        chromadb.delete_data(del_id=db_id)
        return_message = {'articleDiv': '기사가 삭제되었습니다. :['}
        return jsonify(return_message)

    else:
        all_documents = chromadb.export_all()
        for doc in all_documents:
            if 'metadata' in doc:
                doc.update(doc.pop('metadata'))

        # set_num 값으로 정렬
        sorted_values = sorted(all_documents, key=lambda x: x['set_num'])
        
        return jsonify(sorted_values)
    

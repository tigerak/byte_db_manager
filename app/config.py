import sys
# modules
try:
    from secret import csrf_token_secret, model_api_address, BASE_DIR
    print('추라이')
except:
    from app.secret import csrf_token_secret, model_api_address, BASE_DIR
    print('예외')


sys.path.append(BASE_DIR)
print(sys.path)

# secret key for CSRF token
SECRET_KEY = csrf_token_secret

MODEL_API_ADDRESS = model_api_address
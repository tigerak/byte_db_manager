import sys
# modules
try:
    from app.secret import *
except:
    from secret import *

sys.path.append(BASE_DIR)

# secret key for CSRF token
SECRET_KEY = csrf_token_secret
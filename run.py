from waitress import serve
from app import app  # replace 'app' with your filename if it's different

serve(app, host="0.0.0.0", port=8080)

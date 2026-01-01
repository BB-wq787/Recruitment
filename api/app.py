from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello from Vercel!'

# Vercel需要的导出
app = app


from flask import Flask,render_template,request
from flask_sockets import Sockets
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer 
from flask_cors import CORS
app = Flask(__name__)
sockets = Sockets(app)
CORS(app, supports_credentials=True)
#http://127.0.0.1:5000/index
@app.route("/index")
def index():
    return "hello"
    

@sockets.route("/message", websocket=True)
def message(ws):
    client=request.environ.get("wsgi.websocket")
    if not client:
        return "您使用的是Http协议"
    print(ciient)
    return "您使用的是websbcket协议"
    while not ws.closed:
        message= ws.receive()
        print(message)
        now = datetime.datetime.now().isoformat()
        ws.send(now)

if __name__ =="__main__":
    http_server = WSGIServer(('127.0.0.1',5001), app,handler_class=WebSocketHandler)
    print("server start")
    http_server.serve_forever()
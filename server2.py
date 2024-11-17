import pandas as pd
from regression import regression
from picarro_G2301 import Picarro_G2301
import json
import logging
from mySerial import RS232_Device
import re
import datetime
import time
import traceback
from flask import Flask, render_template
from flask_socketio import SocketIO, emit



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins='*')

name_space = '/echo'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/push')
def push_once():
    event_name = 'echo'
    broadcasted_data = {'data': "test message!"}
    # 设置广播数据
    socketio.emit(event_name, broadcasted_data, broadcast=False, namespace=name_space)
    return 'done!'

@socketio.on('connect', namespace=name_space)
def connected_msg():
    print('client connected.')

@socketio.on('disconnect', namespace=name_space)
def disconnect_msg():
    print('client disconnected.')


@socketio.on('picarroConfig', namespace=name_space)
def mtest_message(picarroConfig):
    print(picarroConfig)
    config = picarroConfig




    # from logger_moudle import logger

    logger = logging.getLogger('mylogger')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()


    # Open and read the JSON file
    # with open('picarro_G2302.json', 'r') as file:
    #     config = json.load(file)
    # file.close()

    if config["logStart"] in ["True", "true", "TRUE"]:
        logFolder = config["logFolder"]
        logDtStr = datetime.datetime.now().strftime("%Y%m%d")
        file_handler = logging.FileHandler(logFolder+'_{}.txt'.format(logDtStr))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)


    rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                            request=False, hello=None, answer=None, termin=chr(13),
                            timesleep=0.2, logger=None)


    picarro = Picarro_G2301(rs232Device, logger, config, False)
    funStr=config["execFun"]
    fun= getattr(picarro, funStr)
    data = fun()
    print(data)
    # # result = bar()
    # # picarro._Meas_GetBufferFirst()
    # # picarro._Meas_ClearBuffer()
    # # picarro._Meas_GetScanTime()
    # # picarro._Instr_GetStatus()
    # # picarro._Valves_Seq_Start()
    # # picarro._Valves_Seq_Readtstate()
    # # picarro._Pulse_GetBuffer()
    # # picarro._Pulse_GetBufferFirst()
    # # picarro._Plus_ClearBuffer()
    # # picarro._Plus_GetStatus()
    # # picarro._Flux_Mode_Switch()


    reg = regression("data.csv")

    reg.readFile()

    # # print(type(reg.data.loc[1,"meas_time"]))
    print(reg.data["meas_datetime"].tolist())


    # beginTimeStamp = (beginTime-datetime.datetime(1970, 1, 1)).total_seconds()
    # endTimeStamp = (endTime-datetime.datetime(1970, 1, 1)).total_seconds()
    beginTimeStamp = datetime.datetime.strptime(
        "2024-09-21 00:00:00", "%Y-%m-%d %H:%M:%S").timestamp()
    print(beginTimeStamp)
    endTimeStamp = datetime.datetime.strptime(
        "2024-09-21 01:10:01", "%Y-%m-%d %H:%M:%S").timestamp()
    subData = reg.data.loc[(reg.data["meas_datetimestamp"] >= beginTimeStamp) & (
        reg.data["meas_datetimestamp"] <= endTimeStamp)]
    print(subData)
    y = subData["meas_val1"].tolist()
    x = subData["meas_datetimestamp"].tolist()

    print(reg.data["meas_val1"].tolist())
    print(reg.data["meas_datetimestamp"].tolist())


    print("regression value", reg.calNetArea(y, x))


    # if config["logStart"] == "True":
    #     logger.handlers.clear()
    # print("yes")
    emit('my_response', {'message': "sucessful"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

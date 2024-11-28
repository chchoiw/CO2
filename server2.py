import pandas as pd
import json
import re
import time
import datetime
import traceback
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from scipy import integrate
import os
import glob
from myLogger import mylogger
from mySerial import RS232_Device
from regression import regression
from picarro_G2301 import Picarro_G2301
from tecancavro.transport import TecanAPISerial, TecanAPINode
from tecancavro.models import TecanXLP6000
from myMeasureAction import measureAction
from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)
# class instrument():

#     @abstractmethod
#     def (self):
#         pass




    
#     picarroConfig={
#         "data":{
#                 "logFolder": "picarro_log/",
#                 "logFlag": "True",
#                 "dataFolder": "picarro_data/",
#                 }
#                 # "instrument":["picarro",
#                 "action"："set_picarro_config"                           
#             }
#     config = picarroConfig["data"]
#     # from logger_moudle import logger
#     # picarro = Picarro_G2301(rs232Device, logger, config, False)
#     funStr=config["execFun"]
#     fun= getattr(picarro, funStr)
#     data = fun()
#     print(data)
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
    # if config["logStart"] == "True":
    #     logger.handlers.clear()
    # print("yes")
    # emit('my_response', {'message': "sucessful"})

# xlp = TecanXLP6000(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600))







        

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins='*')

name_space = '/echo'
# socketio.run(app, host='0.0.0.0', port=5001)
pump_config={}
with open('pump_config.json') as json_file:
    pump_config = json.load(json_file)
json_file.close()

picarro_config={}
with open('picarro_config.json') as json_file:
    picarro_config = json.load(json_file)
json_file.close()

xlp=None
picarro=None
rs232Device=None
ma=None

# config = {
#     "logFolder": "picarro_log/",
#     "logStart": "True",
#     "dataFolder": "picarro_data/"
# }
logger = mylogger(name=__name__, logFolder=pump_config["debug_log_path"],level=0, sio=socketio, name_space=name_space)
loggerPicarro=mylogger(name="Picarro", logFolder=pump_config["debug_log_path"],level=0, sio=socketio, name_space=name_space)
loggerSerial = mylogger(
    name="Serial", logFolder=pump_config["debug_log_path"], level=0, sio=socketio, name_space=name_space)
# loggerXlp=logger.getLogger("Tecan_XLP6000")
loggerXlp = mylogger(
    name="Tecan_XLP6000", logFolder=pump_config["debug_log_path"], level=0, sio=socketio, name_space=name_space)
print(loggerXlp)
print(pump_config["com"])
try:
    rs232Device = RS232_Device(device_name="Picarro_G2301", com=picarro_config["com"], baud=9600,
                                request=False, hello=None, answer=None, termin=chr(13),
                                timesleep=0.2, logger=loggerSerial)
    picarro=Picarro_G2301(rs232Con=rs232Device, logger=loggerPicarro, config=picarro_config, prodFlag=False)

    xlp=TecanXLP6000(  com_link=TecanAPISerial(0, pump_config["com"], 9600),\
                    num_ports=int(pump_config["num_ports"]), syringe_ul=int(pump_config["syringe_ul"]),\
                    direction=pump_config["direction"],microstep=int(pump_config["microstep"]), \
                    waste_port=pump_config["waste_port"], slope=int(pump_config["slope"]), \
                    init_force=int(pump_config["init_force"]),debug=pump_config["debug"], \
                    debug_log_path=pump_config["debug_log_path"],logger=loggerXlp)
    ma = measureAction(xlp=xlp, picarro=picarro,
                            logger=logger, prodFlag=False,name_space=name_space,sio=socketio)
except:
    traceback.print_exc()



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


# loggerPicarro = mylogger(name="Picarro",logFolder="picarro_log/", level=0, sio=socketio, name_space=name_space)
# loggerPicarro = logging.getLogger('Picarro')
# loggerPicarro.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()
# # logFolder = config["logFolder"]
# # logDtStr = datetime.datetime.now().strftime("%Y%m%d")

# formatter = logging.Formatter(
#     '%(asctime)s - %(levelname)-8s - %(name)-12s - %(message)s')
# # file_handler = logging.FileHandler(
# #     logFolder+'_{}.txt'.format(logDtStr))
# file_handler = logging.handlers.TimedRotatingFileHandler(
#     "picarro_log/"+"picaro", when='d', interval=1, backupCount=365, encoding='utf-8')
# file_handler.suffix = "%Y%m%d"
# file_handler.extMatch = re.compile(r"^\d{4}\d{2}\d{2}$")
# console_handler.setFormatter(formatter)
# file_handler.setFormatter(formatter)
# loggerPicarro.addHandler(console_handler)
# loggerPicarro.addHandler(file_handler)



# if config["logStart"] in ["True", "true", "TRUE"]:
#     logFolder = config["logFolder"]
#     # logDtStr = datetime.datetime.now().strftime("%Y%m%d")

#     formatter = logging.Formatter(
#         '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
#     # file_handler = logging.FileHandler(
#     #     logFolder+'_{}.txt'.format(logDtStr))
#     file_handler=logging.handlers.TimedRotatingFileHandler(logFolder+"frontEndLog",when='d',interval=1,backupCount=365)
#     file_handler.suffix="%Y%m%d_%H%M.log"
#     console_handler.setFormatter(formatter)
#     file_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)

# ia = instrumentActoin(xlp=xlp, picarro=picarro,
#                         logger=logger, prodFlag=False,name_space=name_space,sio=socketio)






# @socketio.on('responseData', namespace=name_space)
# def mtest_message(receiveData):
#     print(receiveData)

#     # print(ia.getCO2Sample(receiveData["data"][0], baseValue=0))
#     # res=ia.runEntireMeasure(receiveData["data"])
#     # res2=ia.cal_a_b(res)
#     for i in range(3):
#         ia.getCO2Sample_with_std()
    # print(res2)

# @socketio.on('connectPump', namespace=name_space)
# def connectPump(receiveData):
#     print(receiveData)
#     xlp = TecanXLP6000(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600),num_ports=4, syringe_ul=1000, direction='CW',
#                  microstep=2, waste_port=4, slope=14, init_force=0,
#                  debug=True, debug_log_path='./pump_log/')
# @socketio.on('connectPicarro', namespace=name_space)
# def connectPump(receiveData):
#     print(receiveData)
#     rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
#                                 request=False, hello=None, answer=None, termin=chr(13),
#                                 timesleep=0.2, logger=None)
#     picarro = Picarro_G2301(rs232Device, logger, config, prodFlag=False)


@socketio.on('getDefaultConfig', namespace=name_space)
def getDefaultSpeed(receiveData):
    '''
    receiveData={}
    '''
    logger.info("Channel-getDefaultSpeed","取得顯示介面的設定值")
    pump_config={}
    with open('pump_config.json') as json_file:
        pump_config = json.load(json_file)
    json_file.close()

    picarro_config={}
    with open('picarro_config.json') as json_file:
        picarro_config = json.load(json_file)
    json_file.close()
    responseData={
        "pump":pump_config,
        "picarro":picarro_config
    }
    socketio.emit("getDefaultConfig",responseData, namespace=name_space)


@socketio.on('getPicarroDataRealTime', namespace=name_space)
def getPicarroDataRealTime(receiveData):
    logger.info("Channel-getPicarroDataRealTime","取得Picarro中CO2最新的數據")
    if picarro is not None:
        responseData=picarro.getLatestData()
        socketio.emit("getPicarroDataRealTime",responseData, namespace=name_space)
        # print("---dataTmpDf")
        # print(dataTmpDf)
        # resNewDf=pd.concat([resDf, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
        
        # csvStr=dataTmpDf.to_csv()



@socketio.on('getFullLog', namespace=name_space)
def getFullLog(receiveData):
    logger.info("Channel-getFullLog","取得最新BUFFER中的LOG")
    list_of_files = glob.glob('/main_log/*.log') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    file = open(latest_file, "r")
    logContent = file.read()
    socketio.emit("getFullLog",{"data",logContent}, namespace=name_space) 
    file.close()


@socketio.on("connectInstrument", namespace=name_space)
def connectInstrument(receiveData):
    '''
    receiveData={"plump":"connect","picarro":"connect"}
    '''
    logger.info("Channel-connectInstrument","連接儀器")
    if "plump" in receiveData.keys() and receiveData["plump"]=="connect":
        if xlp is None:
            xlp = TecanXLP6000(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600),num_ports=4, syringe_ul=1000, direction='CW',
                    microstep=2, waste_port=4, slope=14, init_force=0,
                    debug=True, debug_log_path='./pump_log/')
            socketio.emit("connectInstrument",{"data","Connect xlp6000 sucessfully."}, namespace=name_space) 
        else:
            socketio.emit("connectInstrument",{"data","Already connect xlp6000."}, namespace=name_space)

    if "picarro" in receiveData.keys() and receiveData["picarro"]=="close":
        if picarro is None:
            rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                                request=False, hello=None, answer=None, termin=chr(13),
                                timesleep=0.2, logger=None)
            picarro = Picarro_G2301(rs232Device, logger, config, prodFlag=False)
            socketio.emit("connectInstrument",{"data","Connect picarro sucessfully."}, namespace=name_space)
        else:
            socketio.emit("connectInstrument",{"data","Already connect picarro."}, namespace=name_space)

# my_dict = {}

# def change_dict(str_file_path, dict_param):
#   with open(str_file_path) as opened_file:
#     dict_param = json.load(opened_file)  # **
#   opened_file.close()

# change_dict(my_file_path, my_dict)  # *


@socketio.on("configInstrument", namespace=name_space)
def configInstrument(receiveData):
    '''
    receiveData={"plump":configData,"picarro":configData}
    '''

    logger.info("Channel-configInstrument","更改儀器配置")
    if "plump" in receiveData.keys() and isinstance(receiveData["pump"], dict):
        newConfig=receiveData["pump"]
        for key,value in newConfig.items():
            pump_config[key]=value
        with open("pump_config.json", "w") as outfile: 
            json.dump(pump_config, outfile)
        outfile.close()

    if "picarro" in receiveData.keys() and isinstance(receiveData["picarro"], dict):
        newConfig=receiveData["picarro"]
        for key,value in newConfig.items():
            picarro_config[key]=value
        with open("picarro_config.json", "w") as outfile: 
            json.dump(picarro_config, outfile)
        outfile.close()



@socketio.on("closeInstrument", namespace=name_space)
def closeInstrument(receiveData):
    '''
    receiveData={"plump":"close","picarro":close}
    '''
    logger.info("Channel-closeInstrument","關閉儀器")
    if "plump" in receiveData.keys() and receiveData["plump"]=="close":
        del xlp
        xlp=None

    if "picarro" in receiveData.keys() and receiveData["picarro"]=="close":
        rs232Device.close()



@socketio.on('initPump', namespace=name_space)
def initPump(receiveData):
    '''
    receiveData={}
    '''
    logger.info("Channel-initPump","初始化泵XLP6000")
    command=xlp.init( init_force=None, direction=None, in_port=None,
             out_port=None)
    logger.info("泵己初始化完成,指令為{}".format(command))

    


@socketio.on('dispense', namespace=name_space)
def dispense(receiveData):
    '''
    收到注射器放出液體的指令
    receiveData={
    "data":[
        {
            "to_port":1, 
            "volumn_ul":100,
            "dispenseSpeed":1000,
        }
         ]
    }
    "volumn_ul":抽入容液量
    dispenseSpeed: TopSpeed
    "to_port":由哪一個port放出液體
    '''

    logger.info("Channel-dispense","注射器放出液體")
    for subData in receiveData["data"]:
        to_port=subData["to_port"]
        volume_ul=subData["volume_ul"]
        if "dispenseSpeed" in subData.keys():
            dispenseSpeed = int(subData("dispenseSpeed"))
        else:
            dispenseSpeed =pump_config["dispenseSpeed"]        
        xlp.setTopSpeed(dispenseSpeed)
        xlp.dispene( to_port, volume_ul)
        command=xlp.self.cmd_chain
        delay = xlp.executeChain()
        logger.info("{}加樣{}ul,指令{},請等待{}秒").format(to_port,volume_ul,command,delay)
        xlp.waitReady(delay)    


@socketio.on('extract', namespace=name_space)
def extract(receiveData):
    '''
    收到注射器抽入液體的指令
    receiveData={
    "data":[
        {
            "from_port":1, 
            "volumn_ul":100,
            "extractSpeed":1000,
        }
         ]
    }
    "volumn_ul":抽入容液量
    extractSpeed: TopSpeed
    "from_port":由哪一個port抽取液體
    '''

    logger.info("Channel-extract","泵抽樣")
    for subData in receiveData["data"]:
        from_port=subData["from_port"]
        volume_ul=subData["volume_ul"]
        if "extractSpeed" in subData.keys():
            extractSpeed = int(subData("extractSpeed"))
        else:
            extractSpeed =pump_config["extractSpeed"]
        
        xlp.setTopSpeed(extractSpeed)
        xlp.extract( from_port, volume_ul)
        command=xlp.self.cmd_chain
        delay = xlp.executeChain()
        logger.info("從{}抽樣{}ul,指令{},請等待{}秒").format(from_port,volume_ul,command,delay)
        xlp.waitReady(delay)    


@socketio.on('getPlungerStatus', namespace=name_space)
def getPlungerPosition(receiveData):
    '''
    拿到注射器的位置
    receiveData={}
    '''

    logger.info("Channel-getPlungerStatus","取得泵的狀態")
    pos=xlp.getPlungerPos()
    modeNum=xlp.getCurrentMode()
    volumn_ul=xlp._stepsToUl()
    curPort=xlp.getCurPort()
    nowDt=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    responseData={
        "data":
        {
            "modeNum":modeNum,
            "pos":pos,
            "volumn_ul":volumn_ul,
            "curPort":curPort,
            "datetime":nowDt
        }

    }
    socketio.emit('getPlungerPosition', responseData, namespace=name_space)

@socketio.on('flush', namespace=name_space)
def flush_pump(receiveData):
    '''
    收到清洗泵的指令, 開始清洗
    receiveData={
    "data":[
            {
            "in_port":1,
            "flush_times":1,
            "wait_gap_ms":100,
            "waste_port":2,
            "volumn_ul":1000,
            }
        ]
    }
    '''

    logger.info("Channel-flush","清洗泵")
    if receiveData["data"] is None:
        return
    dataAry=receiveData["data"]
    for subData in dataAry:
        if "flush_times" in subData.keys():
            times=subData["flush_times"].astype("int")
        if "wait_gap_ms" in subData.keys():
            wait_gap_ms=subData["wait_gap_ms"].astype("int")
        if "waste_port" in subData.keys():
            out_port=subData["waste_port"]
        else:
            out_port=xlp.waste_port
        for i in range(times ):
            waitSeconds=xlp.extractToWaste( in_port=subData["in_port"], volume_ul=subData["volume_ul"], out_port=out_port,
                    speed_code=None, minimal_reset=False, flush=True)
            xlp.waitReady(waitSeconds)
            logger.info("{}清洗第{}次").format(subData["in_port"],i)
        xlp.waitReady(wait_gap_ms*1./1000)





@socketio.on('sampling', namespace=name_space)
def sampling(receiveData):
    '''
    這是收到需要自動做一套實驗
    receiveData={
    "batchMinTimes":2,
    "batchMaxTimes":5,
    "maxTolerateError":0.01,
    "data": 
    [{
        "flush":True,
        "in_port":1,
        "sample_vol":2,
        "out_port":2,
        "sample_DIC":1090,
        "sample_name":"sample1",
        "sample_usage":"sample"
    }
    ,
    {
        "flush":True,
        "in_port":1,
        "sample_vol":2,
        "out_port":2,
        "sample_DIC":1090,
        "sample_name":"sample2",
        "sample_usage":"sample"
    }]
    '''
    # dataFull,batchMinTimes=2, batchMaxTimes=5,esp=0.01
    logger.info("Channel-sampling","進行取樣,計算a,b")
    if receiveData["data"] is None:
        return
    batchMinTimes=int(receiveData["batchMinTimes"])
    batchMaxTimes=int(receiveData["batchMaxTimes"])
    esp=float(receiveData["maxTolerateError"])
    dataAry=receiveData["data"]
    # for subData in dataAry:
    ma = measureAction(xlp=xlp, picarro=picarro,
                       logger=logger, prodFlag=False, name_space=name_space, sio=socketio)
    resDf=ma.runEntireMeasure(dataFull=receiveData["data"],batchMinTimes=batchMinTimes, batchMaxTimes=batchMaxTimes,esp=esp)
    
    
    resDfWithab= ma.cal_a_b(resDf)
    resDfWithab.to_csv(picarro_config["data_path"]+"data_with_a_b.csv",encoding="utf-8",index=False)

    csvStr = resDfWithab.to_csv()
    # resFinalDf=ma.cal_DIC_content(resDfWithab)
    # csvStr=resFinalDf.to_csv()
    responseData={"data":csvStr,"type":"full_sample_data"}
    socketio.emit('sampleing', responseData, namespace=name_space)
    logger.info("Sampling計算已完成")


@socketio.on('measuring', namespace=name_space)
def measuring(receiveData):
    '''
    這是收到需要自動做一套實驗
    receiveData={
    "data":[{
            "flush":True,
            "in_port":1,
            "sample_vol":2,
            "out_port":2,
            "sample_DIC":1090,
            "sample_name":"measure1",
            "sample_usage":"measure"
        },
    {
            "flush":True,
            "in_port":1,
            "sample_vol":2,
            "out_port":2,
            "sample_DIC":1090,
            "sample_name":"measure2",
            "sample_usage":"measure"
        }
    ]
    }
    '''

    logger.info("Channel-measuring","進行測量,已完成計算a,b,計算DIC")
    # dataFull,batchMinTimes=2, batchMaxTimes=5,esp=0.01
    folder=picarro_config["data_path"]
    fileDtStr=datetime.datetime.now().strftime("%y%d%m_%H%M")
    sampleingWitabFile=folder+"data_temp_with_a_b.csv"
    finalResultFile=folder+"data"+fileDtStr+".csv"
    # csvStr = resDfWithab.to_csv()
    resFinalDf=ma.runEntireMeasuring(dataFull=receiveData["data"],sampleingWitabFile=sampleingWitabFile,finalResultFile=finalResultFile)
    csvStr=resFinalDf.to_csv()
    responseData={"data":csvStr,"type":"full_experiment_data"}
    socketio.emit('measuring',responseData, namespace=name_space)
    logger.info("Measuring計算已完成")
# @socketio.on('setSpeed', namespace=name_space)
# def mtest_message(receiveData):
#     print(receiveData)
#     keys=receiveData["data"].keys()

#     if "extractSpeed" in keys:
#         startSpeed=receiveData["data"]["extractSpeed"]
#         xlp.setStartSpeed( pulses_per_sec=startSpeed,execute=True)
#         logger.info("將初始").format(to_port,volume_ul)    
    # if "topSpeed" in keys:
    #     topSpeed=receiveData["data"]["topSpeed"]
    #     xlp.setTopSpeed( pulses_per_sec=startSpeed,execute=True)
    # if "slopeValue" in keys:
    #     slopeValue=receiveData["data"]["slopeValue"]
    #     xlp.setSlope( slope_value=slopeValue,execute=True)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
#     pass

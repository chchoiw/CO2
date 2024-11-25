import pandas as pd
from regression import regression
from picarro_G2301 import Picarro_G2301
import json
import logging
from myLogger import mylogger
from mySerial import RS232_Device
import re
import datetime
import time
import traceback
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from scipy import integrate
from tecancavro.models import XCaliburD

from tecancavro.transport import TecanAPISerial, TecanAPINode
# class instrument():

#     @abstractmethod
#     def (self):
#         pass



class measureAction:
    #     # if config["logStart"] == "True":
    #     logger.handlers.clear()
    def __init__(self, logger=None,sio=None, picarro=None, xlp=None, prodFlag=True,name_space="echo"):
        self.picarro=picarro
        self.xlp=xlp
        self.logger=logger
        self.name_space = name_space
        self.sio=sio
        self.prodFlag=prodFlag
        self.oldConcDataWithStdDf=None
    def set_config(self,acitionKey,actionData):
        config = actionData
        logger=self.logger
        
        # if actionKey.lower()=="set_picarro_config":
        # from logger_moudle import logger
        if logger is None :
            self.logger = logging.getLogger('mylogger')
            logger.setLevel(logging.DEBUG)
            console_handler = logging.StreamHandler()
        # Open and read the JSON file
        # with open('picarro_G2302.json', 'r') as file:
        #     config = json.load(file)
        # file.close()
        if config["logStart"].lower()== "true":
            logFolder = config["logFolder"]
            logDtStr = datetime.datetime.now().strftime("%Y%m%d")
            file_handler = logging.FileHandler(logFolder+'_{}.txt'.format(logDtStr))
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
    def close_log(self):
        if self.logger is not None:
            self.logger.handlers.clear()
        return True
    def open_connection(self,actionKey):
        if actionKey=="open_connection_picarro":
            rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                                    request=False, hello=None, answer=None, termin=chr(13),
                                    timesleep=0.2, logger=None)

            self.picarro = Picarro_G2301(rs232Device, logger, config, False)
        elif actionKey=="open_connection_xlp":
            pass
            # rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
            #                         request=False, hello=None, answer=None, termin=chr(13),
            #                         timesleep=0.2, logger=None)

            # self.picarro = Picarro_G2301(rs232Device, logger, config, False)        
        return True





    def getCO2Second(self,resDf,gapSencond=1):
        
        '''
        每秒讀取儀器最近的DATA, 
        輸入:resDf-之前的數據
        輸出:resNewDf-讀取後更新的數據
        '''
        
        

        dataTmpDf=self.picarro._Meas_GetBuffer()
        # print("---dataTmpDf")
        # print(dataTmpDf)
        resNewDf=pd.concat([resDf, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
        
        csvStr=resNewDf.to_csv()
        self.sio.emit('responseData', {
                      "data": csvStr}, namespace=self.name_space)
        time.sleep(gapSencond)

        return resNewDf
    def calNetArea(self, x, y, baseValue=0):
        result = integrate.trapezoid(y, x)
        print(result)
        if result-baseValue < 0:
            result2 = 0
        else:
            result2 = result-baseValue
        return result
    def getCO2Sample(self,data,estimateSampeSecond=150,baseValue=0):
        """
        測定已知DIC的1次Sample的過程, 並計算面積
        input:    
          "data":{
            "flush":True,
            "in_port":1,
            "sample_vol":2,
            "out_port":2,
            "sample_DIC":1090,
            "sample_name":"sample1",
            "sample_usage":"sample"
            }
        output: result dataframe
        "meas_datetime", get realtime data from picarro 
        'meas_datetimestamp',
        "meas_name":pass from sample_name
        "meas_usage":pass from sample_usage
        "meas_vol":pass from sample_vol
        "meas_DIC":pass from sample_DIC
        "meas_val1":get realtime data from picarro 
        "meas_val2":get realtime data from picarro 
        "meas_val3":get realtime data from picarro 
        "meas_netarea":integral by 'meas_datetimestamp'-"meas_val1"
        """

        resDf=pd.DataFrame(columns=["meas_datetime",'meas_datetimestamp',"meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3","meas_netarea"])
        oldDf = resDf
        for j in range(estimateSampeSecond):
            resDf=self.getCO2Second(resDf)
            print("--get bew resDf")
            print(resDf)
            if not self.prodFlag:
                print("------------------test")
                if data["sample_name"]=="sample1":
                    resDf["meas_val1"] = resDf["meas_val1"].astype(float)+1.1*(j)
                elif data["sample_name"] == "sample2":
                    resDf["meas_val1"]=resDf["meas_val1"].astype(float)+1.2*(j)
                elif data["sample_name"] == "sample3":
                    resDf["meas_val1"] = resDf["meas_val1"].astype(float)+1.3*(j)
                elif data["sample_name"] == "measure1":
                    print("shape",resDf["meas_val1"].shape)
                    resDf["meas_val1"] = resDf["meas_val1"].astype(float)+0.9*(j)
        for i in resDf.index:
            #########################
            # resDf.loc[i,"analysis_time"].timestamp()= utc time stamp, so subtract 8*60*60
            #####################
            # datas['meas_datetime'])
                resDf.loc[i, 'meas_datetimestamp']=pd.to_datetime(resDf.loc[i,
                                                           "meas_datetime"]).timestamp()-60*60*8
        resDf["meas_DIC"]=data["sample_DIC"]
        resDf["meas_name"]=data["sample_name"]
        resDf["meas_vol"]=data["sample_vol"]
        resDf["meas_usage"]=data["sample_usage"]
        # x=resDf["meas_DIC"].tolist()
        y = resDf["meas_val1"].tolist()
        print("---", data["sample_name"])
        x = resDf["meas_datetimestamp"].tolist()


        resDf["meas_netarea"]=self.calNetArea(x=x, y=y,baseValue=baseValue)
        csvStr=resDf.to_csv()
        self.sio.emit('responseData', {
                      "data": csvStr}, namespace=self.name_space)
        return resDf

    def runOneMeasure(self,data):
        """
        測定已知DIC的1次Sample的過程, 包括泵的操作
        """
        completeFlag=False
        if self.prodFlag:
            completeFlag=self.xlp.primePort( in_port=data["in_port"], volume_ul=data["sample_vol"], speed_code=None, out_port=data["out_port"],
                  split_command=False)
        if completeFlag or not self.prodFlag:
            tmpDf=self.getCO2Sample(data,estimateSampeSecond=3)
        if "flush" in data.keys() and data["flush"] and self.prodFlag:
            self.flush_pump()
        return tmpDf


    def runEntireMeasure(self,dataFull,batchMinTimes=2, batchMaxTimes=5,esp=0.01):
        """
        測定已知DIC的2-5次Sample的過程, 包括泵的操作
        """
        sampleName="test1"
        resDf=pd.DataFrame(columns=["meas_datetime","meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3"])
        sucessfulTimes=0
        for i in range(int(batchMaxTimes)):
            data=dataFull[i]
            tmpDf=self.runOneMeasure(data)
            # add flag to reduce the successful measure
            pulseDtStr,pulseMean,pulseStd,pulseSlope=self.getCO2PulseBuffer()
            RSD=(float(pulseStd)/float(pulseMean))
            if RSD <= esp:
                sucessfulTimes+=1
            tmpDf.loc[tmpDf.index,"RSD"]=round(RSD,2)
            
            resDf=pd.concat([resDf, tmpDf]).drop_duplicates(keep=False, ignore_index=True)
            csvStr=resDf.to_csv()
            print(resDf)
            self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)

                # self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)
            if sucessfulTimes >=batchMinTimes:
                return resDf
            
        # fileName="/picarro_data/{}__{}.csv".format(sampleName,logDtStr)
        # resDf.to_csv(fileName, encoding='utf-8', index=False, header=True)

        return resDf

    def cal_a_b(self,resDf):
        reg= regression(data=resDf)
        regData = resDf.loc[resDf["meas_usage"]=="sample"]
        calDICData= resDf.loc[(resDf["meas_usage"]=="measure")]
        y = regData["meas_val1"].astype(float).tolist()
        x = regData["meas_DIC"].astype(float).tolist()
        slope, intercept, r_value, p_value, std_err =reg.cal_regression( x,y)
        resDf["a"]=slope
        resDf["b"]=intercept
        return resDf
    def cal_DIC_content(self,resDf):
        reg= regression(data=resDf)
        regData = resDf.loc[resDf["meas_usage"]=="sample"]
        calDICData= resDf.loc[(resDf["meas_usage"]=="measure")]    
        measureDfFirstIdx=calDICData.index[0]
        meas_netarea=calDICData.loc[measureDfFirstIdx, "meas_netarea"]
        DICValue=reg.dicContent(co2PeakArea=meas_netarea,slope=slope,intercept=intercept,sampleVol=1)
        resDf.loc[calDICData.index,"meas_DIC"]=DICValue
        nowDt=datetime.datetime.now().strftime("%Y%m%d_%H%M")
        fileName="picarro_data/{}_{}.csv".format("test",nowDt)
        resDf.to_csv(fileName, encoding='utf-8', index=False, header=True)
        csvStr=resDf.to_csv()
        self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)
        return resDf    

    def getCO2PulseBuffer_notUse(self):
        """
        取得最新的Pulse data
        """
        dataTmpDf = self.picarro._Pulse_GetBuffer()
        # print("---dataTmpDf")
        # print(dataTmpDf)
        print("get data with std")
        print(dataTmpDf)
        for i in range(3):
            if self.oldConcDataWithStdDf is None:
                # resNewDf=dataTmpDf
                dataTmpJson = dataTmpDf.to_json(orient="records")
                self.sio.emit('concDataWithStd', {
                              "data": dataTmpJson}, namespace=self.name_space)
            else:
                resNewDf=pd.concat([self.oldConcDataWithStdDf, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
                diffDf=dataTmpDf[~self.oldConcDataWithStdDf.eq(dataTmpDf).all(axis=1)]
                self.oldConcDataWithStdDf=resNewDf
                if diffDf.shape[0]>0:
                    diffDataJson=diffDf.to_json(orient="records")
                    self.sio.emit('concDataWithStd', {"data":diffDataJson}, namespace=self.name_space)
                if not self.prodFlag:
                    # "plus_datetime","mean1","std1","slope1","mean2","std2","slope2","mean3","std3","slope3"
                    diffDataJson.loc[0,"mean1"]=1.1*i
                    diffDataJson.loc[0, "mean2"] = 1.2*i
                    diffDataJson.loc[0, "mean3"] = 1.3*i
                    diffDataJson.loc[0, "std1"] = 1.1*i
                    diffDataJson.loc[0, "std2"] = 1.2*i
                    diffDataJson.loc[0, "std3"] = 1.3*i
                    diffDataJson.loc[0, "slope1"] = 1.1*i
                    diffDataJson.loc[0, "slope2"] = 1.2*i
                    diffDataJson.loc[0, "slope3"] = 1.3*i
                    self.sio.emit('concDataWithStd', {"data":diffDataJson}, namespace=self.name_space)
            time.sleep(1)

        return resNewDf
    


    def getCO2PulseBuffer(self):
        """
        取得最新的Pulse data
        """
        dataTmpDf = self.picarro._Pulse_GetBuffer()
        # print("---dataTmpDf")
        # print(dataTmpDf)
        print("get data with std")
        print(dataTmpDf)

        for i in dataTmpDf.index:
            #########################
            # resDf.loc[i,"analysis_time"].timestamp()= utc time stamp, so subtract 8*60*60
            #####################
            # datas['meas_datetime'])
                dataTmpDf.loc[i, 'meas_datetimestamp']=pd.to_datetime(dataTmpDf.loc[i,
                                                           "plus_datetime"]).timestamp()-60*60*8
        idMax=dataTmpDf["meas_datetimestamp"].idxmax()

        return dataTmpDf.loc[idMax,"plus_datetime"],dataTmpDf.loc[idMax,"mean1"],dataTmpDf.loc[idMax,"std1"],dataTmpDf.loc[idMax,"slope1"]
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

# xlp = XCaliburD(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600))




        

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
xlp=None


config = {
    "logFolder": "picarro_log/",
    "logStart": "True",
    "dataFolder": "picarro_data/"
}
logger = mylogger(name=__name__, logFolder="main_log/",level=0, sio=socketio, name_space=name_space)
# loggerPicarro = mylogger(name="Picarro",logFolder="picarro_log/", level=0, sio=socketio, name_space=name_space)
loggerPicarro = logging.getLogger('Picarro')
loggerPicarro.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
# logFolder = config["logFolder"]
# logDtStr = datetime.datetime.now().strftime("%Y%m%d")

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)-8s - %(name)-12s - %(message)s')
# file_handler = logging.FileHandler(
#     logFolder+'_{}.txt'.format(logDtStr))
file_handler = logging.handlers.TimedRotatingFileHandler(
    "picarro_log/"+"picaro", when='d', interval=1, backupCount=365, encoding='utf-8')
file_handler.suffix = "%Y%m%d"
file_handler.extMatch = re.compile(r"^\d{4}\d{2}\d{2}$")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
loggerPicarro.addHandler(console_handler)
loggerPicarro.addHandler(file_handler)



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


pumpDefaultSetting={
    "extractSpeed":900,
    "dispenseSpeed":900,

}
try:
    rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                                request=False, hello=None, answer=None, termin=chr(13),
                                timesleep=0.2, logger=None)
    picarro=Picarro_G2301(rs232Device, loggerPicarro, config, prodFlag=False)
    xlp=XCaliburD(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600),num_ports=4, syringe_ul=1000, direction='CW',
                    microstep=2, waste_port=4, slope=14, init_force=0,
                    debug=True, debug_log_path='./pump_log/')
    ma = measureAction(xlp=xlp, picarro=picarro,
                            logger=logger, prodFlag=False,name_space=name_space,sio=socketio)
except:
    traceback.print_exc()


# @socketio.on('responseData', namespace=name_space)
# def mtest_message(receiveData):
#     print(receiveData)

#     # print(ia.getCO2Sample(receiveData["data"][0], baseValue=0))
#     # res=ia.runEntireMeasure(receiveData["data"])
#     # res2=ia.cal_a_b(res)
#     for i in range(3):
#         ia.getCO2Sample_with_std()
    # print(res2)

@socketio.on('connectPump', namespace=name_space)
def connectPump(receiveData):
    print(receiveData)
    xlp = XCaliburD(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600),num_ports=4, syringe_ul=1000, direction='CW',
                 microstep=2, waste_port=4, slope=14, init_force=0,
                 debug=True, debug_log_path='./pump_log/')
@socketio.on('connectPicarro', namespace=name_space)
def connectPump(receiveData):
    print(receiveData)
    rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                                request=False, hello=None, answer=None, termin=chr(13),
                                timesleep=0.2, logger=None)
    picarro = Picarro_G2301(rs232Device, logger, config, prodFlag=False)


@socketio.on("connectInstrument", namespace=name_space)
def connectInstrument(receiveData):
    '''
    receiveData={"plump":"connect","picarro":"connect"}
    '''
    if "plump" in receiveData.keys() and receiveData["plump"]=="connect":
        if xlp is None:
            xlp = XCaliburD(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600),num_ports=4, syringe_ul=1000, direction='CW',
                    microstep=2, waste_port=4, slope=14, init_force=0,
                    debug=True, debug_log_path='./pump_log/')
            socketio.emit("responseConnect",{"data","Connect xlp6000 sucessfully."}, namespace=name_space) 
        else:
            socketio.emit("responseConnect",{"data","Already connect xlp6000."}, namespace=name_space)

    if "picarro" in receiveData.keys() and receiveData["picarro"]=="close":
        if picarro is None:
            rs232Device = RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                                request=False, hello=None, answer=None, termin=chr(13),
                                timesleep=0.2, logger=None)
            picarro = Picarro_G2301(rs232Device, logger, config, prodFlag=False)
            socketio.emit("responseConnect",{"data","Connect picarro sucessfully."}, namespace=name_space)
        else:
            socketio.emit("responseConnect",{"data","Already connect picarro."}, namespace=name_space)




@socketio.on("close", namespace=name_space)
def closeInstrument(receiveData):
    '''
    receiveData={"plump":"close","picarro":close}
    '''
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
    print(receiveData)
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
    for subData in receiveData["data"]:
        to_port=subData["to_port"]
        volume_ul=subData["volume_ul"]
        if "dispenseSpeed" in subData.keys():
            dispenseSpeed = int(subData("dispenseSpeed"))
        else:
            dispenseSpeed =pumpDefaultSetting["dispenseSpeed"]        
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
    for subData in receiveData["data"]:
        from_port=subData["from_port"]
        volume_ul=subData["volume_ul"]
        if "extractSpeed" in subData.keys():
            extractSpeed = int(subData("extractSpeed"))
        else:
            extractSpeed =pumpDefaultSetting["extractSpeed"]
        
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
    socketio.emit('responsePlungerStatus', responseData, namespace=name_space)

@socketio.on('flush', namespace=name_space)
def flush_pump(receiveData):
    '''
    收到清洗泵的指令, 開始清洗
    receiveData={
    "data":[
            {
            "flush_times":1,
            "wait_gap_ms":100,
            "waste_port":2
            }
        ]
    }
    '''
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
            waitSeconds=xlp.extractToWaste( in_port=subData["in_port"], volume_ul=1100, out_port=out_port,
                    speed_code=None, minimal_reset=False, flush=True)
            xlp.waitReady(waitSeconds)
            logger.info("{}清洗第{}次").format(subData["in_port"],i)
        xlp.waitReady(wait_gap_ms*1./1000)

@socketio.on('measure', namespace=name_space)
def measure(receiveData):
    '''
    這是收到需要自動做一套實驗
    receiveData={
    "batchMinTimes":2,
    "batchMaxTimes":5,
    "maxTolerateError":0.01,
    "data":[{
            "flush":True,
            "in_port":1,
            "sample_vol":2,
            "out_port":2,
            "sample_DIC":1090,
            "sample_name":"sample1",
            "sample_usage":"sample"
        }
    },
    {
            "flush":True,
            "in_port":1,
            "sample_vol":2,
            "out_port":2,
            "sample_DIC":1090,
            "sample_name":"sample2",
            "sample_usage":"sample"
        }
    },
    ]
    }
    '''
    # dataFull,batchMinTimes=2, batchMaxTimes=5,esp=0.01
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
    csvStr = resDfWithab.to_csv()
    # resFinalDf=ma.cal_DIC_content(resDfWithab)
    # csvStr=resFinalDf.to_csv()
    socketio.emit('responseData', {"data": csvStr}, namespace=name_space)
    logger.info("計算已完成")

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

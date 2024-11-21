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



class instrumentActoin:
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





    def reagent_get_each_conc_data(self,resDf):
        dataTmpDf=self.picarro._Meas_GetBuffer()
        # print("---dataTmpDf")
        # print(dataTmpDf)
        resNewDf=pd.concat([resDf, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
        
        csvStr=resNewDf.to_csv()
        self.sio.emit('responseData', {
                      "data": csvStr}, namespace=self.name_space)
        time.sleep(1)

        return resNewDf
    def calNetArea(self, x, y, baseValue=0):
        result = integrate.trapezoid(y, x)
        print(result)
        if result-baseValue < 0:
            result2 = 0
        else:
            result2 = result-baseValue
        return result
    def reagent_get_conc_data(self,data,baseValue=0):
        """
        input: data={"meas_datetime":"", "meas_name":"","meas_vol":"","meas_DIC":""}
        get CO content each seconds and calculate net aeas 
        output: result dataframe
        """

        resDf=pd.DataFrame(columns=["meas_datetime","meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3"])
        oldDf = resDf
        for j in range(3):
            resDf=self.reagent_get_each_conc_data(resDf)
            print("--get bew resDf")
            print(resDf)
            if not self.prodFlag:
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
        x=resDf["meas_DIC"].tolist()
        y = resDf["meas_val1"].tolist()
        print("---", data["sample_name"])
        x = resDf["meas_datetimestamp"].tolist()


        resDf["meas_netarea"]=self.calNetArea(x=x, y=y,baseValue=baseValue)
        csvStr=resDf.to_csv()
        self.sio.emit('responseData', {
                      "data": csvStr}, namespace=self.name_space)
        return resDf

    def run_one_test(self,data):
        completeFlag=False
        if self.prodFlag:
            completeFlag=self.xlp.primePort( in_port=data["in_port"], volume_ul=data["sample_vol"], speed_code=None, out_port=data["out_port"],
                  split_command=False)
        if completeFlag or not self.prodFlag:
            tmpDf=self.reagent_get_conc_data(data)
        if "flush" in data.keys() and data["flush"] and self.prodFlag:
            self.flush_pump()
        return tmpDf


    def run_full_test(self,dataFull):
        sampleName="test1"
        resDf=pd.DataFrame(columns=["meas_datetime","meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3"])
        for i in range(len(dataFull)):
            data=dataFull[i]
            tmpDf=self.run_one_test(data)
            resDf=pd.concat([resDf, tmpDf]).drop_duplicates(keep=False, ignore_index=True)
        # fileName="/picarro_data/{}__{}.csv".format(sampleName,logDtStr)
        # resDf.to_csv(fileName, encoding='utf-8', index=False, header=True)
        csvStr=resDf.to_csv()
        self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)
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

    def reagent_get_conc_data_with_std(self):

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
logger = mylogger(name='mylogger', level=0, sio=socketio, name_space=name_space)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
if config["logStart"] in ["True", "true", "TRUE"]:
    logFolder = config["logFolder"]
    logDtStr = datetime.datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        logFolder+'_{}.txt'.format(logDtStr))
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# ia = instrumentActoin(xlp=xlp, picarro=picarro,
#                         logger=logger, prodFlag=False,name_space=name_space,sio=socketio)



pumpDefaultSetting={
    "extractSpeed":900,
    "dispenseSpeed":900,

}


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

# @socketio.on('responseData', namespace=name_space)
# def mtest_message(receiveData):
#     print(receiveData)

#     # print(ia.reagent_get_conc_data(receiveData["data"][0], baseValue=0))
#     # res=ia.run_full_test(receiveData["data"])
#     # res2=ia.cal_a_b(res)
#     for i in range(3):
#         ia.reagent_get_conc_data_with_std()
    # print(res2)

@socketio.on('init', namespace=name_space)
def initPump(receiveData):
    print(receiveData)
    command=xlp.init( init_force=None, direction=None, in_port=None,
             out_port=None)
    logger.info("泵己初始化完成,指令為{}".format(command))

    


@socketio.on('dispense', namespace=name_space)
def dispense(receiveData):
    # print(receiveData)
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
def dispense(receiveData):
    # print(receiveData)
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


@socketio.on('getPumpStatus', namespace=name_space)
def getPumpPosition(receiveData):
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
    socketio.emit('responsePumpStatus', responseData, namespace=name_space)

@socketio.on('flush', namespace=name_space)
def flush_pump(receiveData):
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
    socketio.run(app, host='0.0.0.0', port=5000)

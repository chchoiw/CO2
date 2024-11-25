import datetime
import logging
import time
import pandas as pd
from regression import regression
from scipy import integrate
import random
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
        self.storedData=None

        
    def close_log(self):
        if self.logger is not None:
            self.logger.handlers.clear()
        return True






    def getCO2Second(self,resDf,dataKnown,gapSencond=1):
        
        '''
        每秒讀取儀器最近的DATA, 
        輸入:resDf-之前的數據
        輸出:resNewDf-讀取後更新的數據
        '''

        dataTmpDf=self.picarro._Meas_GetBuffer()
        dataTmpDf["meas_DIC"]=dataKnown["sample_DIC"]
        dataTmpDf["meas_name"]=dataKnown["sample_name"]
        dataTmpDf["meas_vol"]=dataKnown["sample_vol"]
        dataTmpDf["meas_usage"]=dataKnown["sample_usage"]       
        if self.storedData is None:
            # resNewDf=dataTmpDf
            dataTmpJson = dataTmpDf.to_json(orient="records")
            resNewDf=dataTmpDf
        
        else:
            resNewDf=pd.concat([self.storedData, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
            diffDf=dataTmpDf[~self.storedData.eq(dataTmpDf).all(axis=1)]
            self.storedData=resNewDf
            if diffDf.shape[0]>0:
                # diffDataJson=diffDf.to_json(orient="records")
                # "meas_datetime","meas_val1","meas_val2","meas_val3"
                diffCSV=diffDf.to_csv()
                responseData={"data":diffCSV,"sample_name":dataKnown["sample_name"],"type":"latest_data"}
                self.sio.emit('realTimeData',responseData , namespace=self.name_space)
            if not self.prodFlag:
                # "plus_datetime","mean1","std1","slope1","mean2","std2","slope2","mean3","std3","slope3"
                diffDf.loc[-1,"meas_mean1"]=1.1*random.randint(0, 10)
        
        # print("---dataTmpDf")
        # print(dataTmpDf)

        
        csvStr=resNewDf.to_csv()
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
            resDf=self.getCO2Second(resDf, dataKnown=data)
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
        # resDf["meas_DIC"]=data["sample_DIC"]
        # resDf["meas_name"]=data["sample_name"]
        # resDf["meas_vol"]=data["sample_vol"]
        # resDf["meas_usage"]=data["sample_usage"]   
        # x=resDf["meas_DIC"].tolist()
        y = resDf["meas_val1"].tolist()
        x = resDf["meas_datetimestamp"].tolist()
        resDf["meas_netarea"]=self.calNetArea(x=x, y=y,baseValue=baseValue)
        csvStr=resDf.to_csv()
        responseData={"data":csvStr,"sample_name":data["sample_name"],"type":"a_sample_data"}
        self.sio.emit('realTimeData', responseData, namespace=self.name_space)
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


    def runEntireSampling(self,dataFull,sampleingWitabFile,batchMinTimes=2, batchMaxTimes=5,esp=0.01):
        """
        測定已知DIC的2-5次Sample的過程, 包括泵的操作
        """
        resDf=pd.DataFrame(columns=["meas_datetime","meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3"])
        sucessfulTimes=0
        for i in range(int(batchMaxTimes)):
            data=dataFull[i]
            tmpDf=self.runOneMeasure(data)
            # add flag to reduce the successful measure
            pulseDtStr,pulseMean,pulseStd,pulseSlope=self.picarro.getLatestPulseBuffer()
            RSD=(float(pulseStd)/float(pulseMean))
            if RSD <= esp:
                sucessfulTimes+=1
            tmpDf.loc[tmpDf.index,"RSD"]=round(RSD,2)
            
            resDf=pd.concat([resDf, tmpDf]).drop_duplicates(keep=False, ignore_index=True)
            # csvStr=resDf.to_csv()
            # print(resDf)
            # self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)

                # self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)
            if sucessfulTimes >=batchMinTimes:
                return resDf
            
        # fileName="/picarro_data/{}__{}.csv".format(sampleName,logDtStr)
        resDf.to_csv(sampleingWitabFile, encoding='utf-8', index=False, header=True)

        return resDf


    def runEntireMeasuring(self,dataFull,sampleingWitabFile,finalResultFile,sampleingWitabDf=None):
        """
        測定已知DIC的2-5次Sample的過程, 包括泵的操作
        """
        # resDf=pd.DataFrame(columns=["meas_datetime","meas_name","meas_usage","meas_vol","meas_DIC","meas_val1","meas_val2","meas_val3"])
        if sampleingWitabDf is None:
            resDf=pd.read_csv(sampleingWitabFile)
        else:
            resDf=sampleingWitabDf
        sucessfulTimes=0
        for i in range(len(dataFull)):
            data=dataFull[i]
            tmpDf=self.runOneMeasure(data)
            tmpDf["a"]=resDf.loc[resDf.index[0],"a"]
            tmpDf["b"]=resDf.loc[resDf.index[0],"b"]
            resDf=pd.concat([resDf, tmpDf]).drop_duplicates(keep=False, ignore_index=True)
            
        # fileName="/picarro_data/{}__{}.csv".format(sampleName,logDtStr)
        # resDf.to_csv(fileName, encoding='utf-8', index=False, header=True)
        resFinalDf=self.cal_DIC_content(resDf)
        resDf.to_csv(finalResultFile, encoding='utf-8', index=False, header=True)
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
        resDf["r_value"]=r_value
        return resDf
    def cal_DIC_content(self,resDf):
        reg= regression(data=resDf)
        regData = resDf.loc[resDf["meas_usage"]=="sample"]
        calDICData= resDf.loc[(resDf["meas_usage"]=="measure")]    
        measureDfFirstIdx=calDICData.index[0]
        meas_netarea=calDICData.loc[measureDfFirstIdx, "meas_netarea"]
        slope=resDf.loc[resDf.index[0],"a"]
        intercept=resDf.loc[resDf.index[0],"b"]
        DICValue=reg.dicContent(co2PeakArea=meas_netarea,slope=slope,intercept=intercept,sampleVol=1)
        resDf.loc[calDICData.index,"meas_DIC"]=DICValue
        nowDt=datetime.datetime.now().strftime("%Y%m%d_%H%M")
        fileName="picarro_data/{}_{}.csv".format("test",nowDt)
        resDf.to_csv(fileName, encoding='utf-8', index=False, header=True)
        csvStr=resDf.to_csv()
        # self.sio.emit('responseData', {"data": csvStr}, namespace=self.name_space)
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
                # self.sio.emit('concDataWithStd', { "data": dataTmpJson}, namespace=self.name_space)
            else:
                resNewDf=pd.concat([self.oldConcDataWithStdDf, dataTmpDf]).drop_duplicates(keep=False, ignore_index=True)
                diffDf=dataTmpDf[~self.oldConcDataWithStdDf.eq(dataTmpDf).all(axis=1)]
                self.oldConcDataWithStdDf=resNewDf
                if diffDf.shape[0]>0:
                    diffDataJson=diffDf.to_json(orient="records")
                    # self.sio.emit('concDataWithStd', {"data":diffDataJson}, namespace=self.name_space)
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
                    # self.sio.emit('concDataWithStd', {"data":diffDataJson}, namespace=self.name_space)
            time.sleep(1)

        return resNewDf
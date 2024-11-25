import pandas as pd
import traceback
import time
import datetime
import re
# from logger_moudle import logger
from mySerial import RS232_Device
import logging
import json

class Picarro_G2301():
    def __init__(self,rs232Con,logger,config,prodFlag):
        # self.collectDataFlag=collectDataFlag
        self.rs232Conn=rs232Con
        self.logger=logger
        self.prodFlag=prodFlag
        self.config=config

    def collectDataFromFirstBuffFirst(self):
        while self.collectDataFlag==True:
            try:
                ret= self.ExecCMD("_MEAS_GETBUFFERFIRST_")
                ret=ret.split(";")
                sampleTime=ret[0]
                for value in ret[1:]:
                    print("value={}".format(value))
            except:
                time.sleep(1.0)
    def _Meas_GetBuffer(self):
        command="_Meas_GetBuffer"
        "Run command:{}".format(command)
        # self.logger.info("> {:<15}:{}".format("Run Command",command))
        self.logInfoCall("Run Command",command)
        ########################################################
        # <Time>;<MeasN_Conc1>;<MeasN_Conc2>;<MeasN_Conc3>;<CR>
        ###############################################
        retDf=pd.DataFrame(columns=["meas_datetime","meas_val1","meas_val2","meas_val3"])
        retDfIdx=0
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn="2"+chr(13)+"2024-09-21 00:00:00;23.180;1.333;20.111;"+chr(13)+\
           "2024-09-21 00:05:00;23.280;1.433;21.111;"+chr(13)+\
                "2024-09-21 00:10:00;23.380;1.533;22.111;"+chr(13)
        if self.handleError(buffReturn): return 

        # self.logger.info("> {<:15}:".format("Reutrn Result:"))
        self.logDebugCall("Reutrn Result:", "")
        
        retAry=buffReturn.split(chr(13))
        for i in range(1,len(retAry)):
            ret=retAry[i]
            # self.logger.info("> {<:15}:{}".format(ret))
            self.logDebugCall("", ret)
            measGetBuffReg=r"(?i)[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2};[0-9]{1,3}.[0-9]{1,3};[0-9]{1,3}.[0-9]{1,3};[0-9]{1,3}.[0-9]{1,3};"
            reGroup=re.search(measGetBuffReg, ret) 
            if reGroup is not None:
                begIdx, endIdx = reGroup.span()
                valAry=ret[begIdx:endIdx].split(";")
                retDf.loc[retDfIdx,"meas_datetime"]=valAry[0]
                retDf.loc[retDfIdx,"meas_val1"]=valAry[1]
                retDf.loc[retDfIdx,"meas_val2"]=valAry[2]
                retDf.loc[retDfIdx,"meas_val3"]=valAry[3]
                retDfIdx+=1
        # print(retDf)
        # retDf.to_csv("data.csv")
        return retDf


    def _Meas_GetBufferFirst(self):
        command="_Meas_GetBufferFirst"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command",command)
        ########################################################
        # <Time>;<MeasN_Conc1>;<MeasN_Conc2>;<MeasN_Conc3>;<CR>
        ###############################################
        retDf=pd.DataFrame(columns=["meas_datetime","meas_val1","meas_val2","meas_val3"])
        retDfIdx=0
        if self.prodFlag:
            buffReturn=self.rs232Conn.query(command+chr(13))        
        else:
            buffReturn=chr(13)+"2024-09-12 00:00:00;23.480;1.233;20.111;"+chr(13)
        retAry=buffReturn.split(chr(13))
        if self.handleError(buffReturn): return 
        # self.logInfoCall("Return Result", "")
        self.logDebugCall("Return Result", "")
        for i in range(len(retAry)):
            ret=retAry[i]

            # self.logger.info("> "+ret)
            # self.logInfoCall("", ret)
            self.logDebugCall("", ret)
            measGetBuffReg=r"(?i)[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2};[0-9]{1,3}.[0-9]{1,3};[0-9]{1,3}.[0-9]{1,3};[0-9]{1,3}.[0-9]{1,3};"
            reGroup=re.search(measGetBuffReg, ret) 
            if reGroup is not None:
                begIdx, endIdx = reGroup.span()
                valAry=ret[begIdx:endIdx].split(";")
                retDf.loc[retDfIdx,"meas_datetime"]=valAry[0]
                retDf.loc[retDfIdx,"meas_val1"]=valAry[1]
                retDf.loc[retDfIdx,"meas_val2"]=valAry[2]
                retDf.loc[retDfIdx,"meas_val3"]=valAry[3]
                retDfIdx+=1
        # print(retDf)
        return retDf

    def _Meas_ClearBuffer(self):
        command="_Meas_ClearBuffer"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command",command)
        ########################################################
        # Respected Result:OK
        ###############################################
        retDf=pd.DataFrame(columns=["meas_datetime","meas_val1","meas_val2","meas_val3"])
        retDfIdx=0
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"OK"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn)
        # )
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn

    def _Meas_GetScanTime(self):
        command="_Meas_GetScanTime"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: seconds
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"10.2323"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn
    def _Instr_GetStatus(self):
        command="_Instr_GetStatus"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: 16 bit int
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"963"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        buffReturnBinary="{:b}".format(int(buffReturn))
        # buffReturnBinary.zfill(16)
   
        self.logDebugCall("Return Result", buffReturn)
        self.logger.info("> {:<15}: {:b}".format("",int(buffReturn)))
        

        lenBinary=len(buffReturnBinary)
        if lenBinary>=15:
            if (buffReturnBinary[lenBinary-1-14] == '0'):
                self.logInfoCall("", "The instrument is not currently in an error state.")
            elif (buffReturnBinary[lenBinary-1-14]=='1'): 
                self.logInfoCall("", "A system error is present. Use _Instr_GetError for more information.")
        if lenBinary>=14:
            if (buffReturnBinary[lenBinary-1-13]=='0'): 
                self.logInfoCall("", "The instrument has successfully started up.")
            elif (buffReturnBinary[lenBinary-1-13]=='1'): 
                self.logInfoCall("", "The instrument is currently warming up from power-off or restart.")
        if lenBinary>=10:     
            if (buffReturnBinary[lenBinary-1-9]=='0'): 
                self.logInfoCall("", "The warm box temperature is not stabilized within acceptable bounds.")
            elif (buffReturnBinary[lenBinary-1-9]=='1'): 
                self.logInfoCall("", "The warm box temperature is within acceptable bounds for measurements.")
        if lenBinary>=9:
            if (buffReturnBinary[lenBinary-1-8]=='0'): 
                self.logInfoCall("", "The cavity temperature is not stabilized within acceptable bounds.")
            elif (buffReturnBinary[lenBinary-1-8]=='1'): 
                self.logInfoCall("", "The cavity temperature is within acceptable bounds for measurements.")
        if lenBinary>=8:
            if (buffReturnBinary[lenBinary-1-7]=='0'): 
                self.logInfoCall("", "The gas sample pressure is not stabilized within acceptable bounds.")
            elif (buffReturnBinary[lenBinary-1-7]=='1'):  
                self.logInfoCall("", "The gas sample pressure is within acceptable bounds for measurement..") 
        if lenBinary>=6:       
            if (buffReturnBinary[lenBinary-1-6]=='0'): 
                self.logInfoCall("", "Valves are closed and no gas is flowing.") 
            elif (buffReturnBinary[lenBinary-1-6]=='1'): 
                self.logInfoCall("", "Valves are open (pressure is within acceptable bounds for measurement.") 
        if lenBinary>=3:
            if (buffReturnBinary[lenBinary-1-2]=='0'): 
                self.logInfoCall("", "The error queue is empty.")
            elif (buffReturnBinary[lenBinary-1-2]=='1'): 
                self.logInfoCall("", "There is at least one value in the error queue.")
        if lenBinary>=2:
            if (buffReturnBinary[lenBinary-1-1]=='0'): 
                self.logInfoCall("", "The measurement system is currently inactive.")
            elif (buffReturnBinary[lenBinary-1-1]=='1'): 
                self.logInfoCall("", "The measurement system is currently active.")    
        if lenBinary>=1:          
            if (buffReturnBinary[lenBinary-1]=='0'): 
                self.logInfoCall("", "The instrument currently cannot make a gas measurement.")
            elif (buffReturnBinary[lenBinary-1]=='1'):   
                self.logInfoCall("", "The instrument is currently capable of measuring the sample gas.")
        # self.logger.info("# Status end")                        
        return buffReturn   

    def _Valves_Seq_Start(self):

        command="_Valves_Seq_Start"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: seconds
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"OK"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn
    def _Valves_Seq_Stop(self):

        command="_Valves_Seq_Stop"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: seconds
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"OK"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn


    def _Valves_Seq_Readtstate(self):

        command="_Valves_Seq_Readstate"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: seconds
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"ON;8"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        buffReturnAry=buffReturn.split(";")
        buffReturnBinary="{:b}".format(int(buffReturnAry[1]))
        valves=[]
        # print(buffReturnBinary)
        lenBin=len(buffReturnBinary)
        for i in range(lenBin):
            # print(i,buffReturnBinary[i])
            if buffReturnBinary[lenBin-1-i]=='1':
                valves.append(str(i))
        explainStr=",".join(valves)+ " "+buffReturnAry[0]

        # self.logger.info("Return result: {}".format(explainStr))
        self.logDebugCall("Explain", explainStr)
        return buffReturn

    def _Valves_Seq_Settstate(self,num):

        command="_Valves_Seq_Readstate "+num
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result: seconds
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"ON;8"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        buffReturnAry=buffReturn.split(";")
        buffReturnBinary="{:b}".format(int(buffReturnAry[1]))
        valves=[]
        # print(buffReturnBinary)
        lenBin=len(buffReturnBinary)
        for i in range(lenBin):
            # print(i,buffReturnBinary[i])
            if buffReturnBinary[lenBin-1-i]=='1':
                valves.append(str(i))
        explainStr=",".join(valves)+ " "+buffReturnAry[0]

        # self.logger.info("Return result:explain-Valves {}".format(explainStr))
        self.logDebugCall("Explain", explainStr)
        return buffReturn

    def _Pulse_GetBuffer(self):
        command="_Pulse_GetBuffer"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # N;<CR><Time>;<mean1>;<std1>;<slope1>;<mean2>;<std2>;<slope2>;<mean3>;<std3>;<slope3>;<CR>
        ###############################################
        retDf=pd.DataFrame(columns=["plus_datetime","mean1","std1","slope1","mean2","std2","slope2","mean3","std3","slope3"])
        retDfIdx=0
        if self.prodFlag:
            buffReturn=self.rs232Conn.query(command+chr(13))        
        else:
            buffReturn="3"+chr(13)+"09/21/24 00:00:00.123;23.480;-123331.233;20.111;23.480;-123331.233;20.111;23.480;-123331.233;20.111;"+chr(13)+\
           "09/21/24 00:05:00.123;23.480;-123331.233;20.111;23.480;-123331.233;20.111;23.480;-123331.233;20.111;"+chr(13)+\
                "09/21/24 00:10:00.123;23.480;-123331.233;20.111;23.480;-123331.233;20.111;23.480;-123331.233;20.111;"+chr(13)
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:")
        self.logDebugCall("Return Result", "")
        
        retAry=buffReturn.split(chr(13))
        for i in range(len(retAry)):
            ret=retAry[i]
            # self.logger.info("# "+ret)
            self.logDebugCall("", ret)
            measGetBuffReg=r"(?i)[0-9]{2}/[0-9]{2}/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};"
            reGroup=re.search(measGetBuffReg, ret) 
            if reGroup is not None:
                begIdx, endIdx = reGroup.span()
                valAry=ret[begIdx:endIdx].split(";")
                retDf.loc[retDfIdx,"plus_datetime"]=valAry[0]
                retDf.loc[retDfIdx,"mean1"]=valAry[1]
                retDf.loc[retDfIdx,"std1"]=valAry[2]
                retDf.loc[retDfIdx,"slope1"]=valAry[3]
                retDf.loc[retDfIdx,"mean2"]=valAry[4]
                retDf.loc[retDfIdx,"std2"]=valAry[5]
                retDf.loc[retDfIdx,"slope2"]=valAry[6]
                retDf.loc[retDfIdx,"mean3"]=valAry[7]
                retDf.loc[retDfIdx,"std3"]=valAry[8]
                retDf.loc[retDfIdx,"slope3"]=valAry[9]
                retDfIdx+=1
        print(retDf)
        return retDf
    def _Pulse_GetBufferFirst(self):
        command="_Pulse_GetBufferFirst"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # <Time>;<mean1>;<std1>;<slope1>;<mean2>;<std2>;<slope2>;<mean3>;<std3>;<slope3>;
        ###############################################
        retDf=pd.DataFrame(columns=["plus_datetime","mean1","std1","slope1","mean2","std2","slope2","mean3","std3","slope3"])
        retDfIdx=0
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"09/12/19 00:00:00.123;23.480;-123331.233;20.111;23.480;-123331.233;20.111;23.480;-123331.233;20.111;"+chr(13)
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:")
        self.logDebugCall("Return Result", "")
        retAry=buffReturn.split(chr(13))
        for i in range(len(retAry)):
            ret=retAry[i]
            # self.logger.info(ret)
            self.logDebugCall("", ret)
            measGetBuffReg=r"(?i)[0-9]{2}/[0-9]{2}/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};[-]{0,1}[0-9]{1,7}.[0-9]{1,3};"
            reGroup=re.search(measGetBuffReg, ret) 
            if reGroup is not None:
                begIdx, endIdx = reGroup.span()
                valAry=ret[begIdx:endIdx].split(";")
                retDf.loc[retDfIdx,"plus_datetime"]=valAry[0]
                retDf.loc[retDfIdx,"mean1"]=valAry[1]
                retDf.loc[retDfIdx,"std1"]=valAry[2]
                retDf.loc[retDfIdx,"slope1"]=valAry[3]
                retDf.loc[retDfIdx,"mean2"]=valAry[4]
                retDf.loc[retDfIdx,"std2"]=valAry[5]
                retDf.loc[retDfIdx,"slope2"]=valAry[6]
                retDf.loc[retDfIdx,"mean3"]=valAry[7]
                retDf.loc[retDfIdx,"std3"]=valAry[8]
                retDf.loc[retDfIdx,"slope3"]=valAry[9]
                retDfIdx+=1
        # print(retDf)
        return retDf
    def _Plus_ClearBuffer(self):
        command="_Plus_ClearBuffer"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result:OK
        ###############################################
        if self.prodFlag:
            buffReturn=self.rs232Conn.query(command+chr(13))        
        else:
            buffReturn=chr(13)+"OK"+chr(13)
        
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn
    def _Plus_GetStatus(self):
        command="_Plus_GetStatus"
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # Respected Result:0,1,2
        ###############################################
        if self.prodFlag:
            buffReturn = self.rs232Conn.query(command+chr(13))
        else:
            buffReturn=chr(13)+"1"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        if self.handleError(buffReturn): return 
        if buffReturn=="0":
            status="Waiting"
        elif buffReturn=="1":
            status="Armed"
        elif buffReturn=="2":
            status="Triggered"
        else:
            status=""
        # self.logger.info("Return result:{}-{}".format(buffReturn,status))
        self.logDebugCall("Return Result", buffReturn)
        self.logDebugCall("Explain", status)
        return buffReturn
    def _Flux_Mode_Switch(self,para="CO2_H2O"):
        command="_Plus_GetStatus "+para
        # self.logger.info("Run command:{}".format(command))
        self.logInfoCall("Run Command", command)
        ########################################################
        # para= CO2_H2O, H2O_CH4,CO2_CH4
        # Respected Result:OK
        ###############################################
        if self.prodFlag:
            buffReturn=self.rs232Conn.query(command+chr(13))        
        else:
            buffReturn=chr(13)+"OK"+chr(13)
        buffReturn=buffReturn.replace(chr(13),"")
        # buffReturn="'ERR:6001"
        if self.handleError(buffReturn): return 
        # self.logger.info("Return result:{}".format(buffReturn))
        self.logDebugCall("Return Result", buffReturn)
        return buffReturn
    
    def handleError(self,code):
        # print(code[:5])
        reGroup=re.search("(?i)ERR\s{0,3}:",code)
        if reGroup is not None:
            if re.search("(?i)ERR\s{0,3}:1000",code):
                self.logger.error("> {:<15}:{}".format("Error code:","1000-Communication failed."))
            elif re.search("(?i)ERR\s{0,3}:1001",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "1001-Processing previous command."))
            elif re.search("(?i)ERR\s{0,3}:1002",code):
                self.logger.error("> {:<15}:{}".format(
                    "Error code:", "1002-Command not recognized."))
            elif re.search("(?i)ERR\s{0,3}:1004",code):
               self.logger.error("> {:<15}:{}".format("Error code:", "1003-Parameters invalid."))
            elif re.search("(?i)ERR\s{0,3}:3001",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "004-Command execution failed."))
            elif re.search("(?i)ERR\s{0,3}:3002",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "3001-Measurement system disabled."))
            elif re.search("(?i)ERR\s{0,3}:5001",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "3002-No measurements data exists."))
            elif re.search("(?i)ERR\s{0,3}:5002",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "5002-Processing previous command."))
            elif re.search("(?i)ERR\s{0,3}:6001",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "6001-No pulse analyzer data exits."))
            elif re.search("(?i)ERR\s{0,3}:6002",code):
                self.logger.error("> {:<15}:{}".format("Error code:", "6002-Pulse analyzer is not running."))
            return True
        else:
            return False
    def getLatestData(self):    
        '''
        每秒讀取儀器最近的DATA, 
        輸入:resDf-之前的數據
        輸出:resNewDf-讀取後更新的數據
        '''
        resDf=pd.DataFrame(columns=["meas_datetime","meas_val1","meas_val2","meas_val3"])
        # resDf=self._Meas_GetBuffer()
        resDf=self.getLatestMeasBuffer()
        if resDf.shape[0]>0:
            maxidx=resDf.index[0]
                
            pulseDateTime, mean,std,slope=self.getLatestPulseBuffer()
            responseData={
                "data":{
                    "meas_datetime":resDf.loc[maxidx,"meas_datetime"],
                    "meas_val1":resDf.loc[maxidx,"meas_val1"],
                    "pulse_datetime":pulseDateTime,
                    "pulse_mean":mean,
                    "pulse_std":std,
                    "pulse_slope":slope
                }
            }
            
        else:
            responseData={
            "data":{
                "meas_datetime":None,
                "meas_val1":None,
                "pulse_datetime":pulseDateTime,
                "pulse_mean":mean,
                "pulse_std":std,
                    "pulse_slope":slope
                }
            }      
        return responseData     
    def getLatestMeasBuffer(self):    
        '''
        每秒讀取儀器最近的DATA, 
        輸入:resDf-之前的數據
        輸出:resNewDf-讀取後更新的數據
        '''
        resDf=pd.DataFrame(columns=["meas_datetime","meas_val1","meas_val2","meas_val3"])
        resDf=self._Meas_GetBuffer()
        for i in resDf.index:
            #########################
            # resDf.loc[i,"analysis_time"].timestamp()= utc time stamp, so subtract 8*60*60
            #####################
            # datas['meas_datetime'])
                resDf.loc[i, 'meas_datetimestamp']=pd.to_datetime(resDf.loc[i,
                                                           "meas_datetime"]).timestamp()-60*60*8
        maxidx=resDf['meas_datetimestamp'].idxmax()    
        return resDf[resDf.index==maxidx]
    
    def getLatestPulseBuffer(self):
        """
        取得最新的Pulse data
        """
        dataTmpDf = self._Pulse_GetBuffer()
        for i in dataTmpDf.index:
            #########################
            # resDf.loc[i,"analysis_time"].timestamp()= utc time stamp, so subtract 8*60*60
            #####################
            # datas['meas_datetime'])
                dataTmpDf.loc[i, 'meas_datetimestamp']=pd.to_datetime(dataTmpDf.loc[i,
                                                           "plus_datetime"]).timestamp()-60*60*8
        idMax=dataTmpDf["meas_datetimestamp"].idxmax()

        return dataTmpDf.loc[idMax,"plus_datetime"],dataTmpDf.loc[idMax,"mean1"],dataTmpDf.loc[idMax,"std1"],dataTmpDf.loc[idMax,"slope1"]
    def logInfoCall(self, prefixName,command):
        # self.logger.debug(' {}: {}'.format(f_name, f_locals))
        msg = " {:<15}: {}".format(prefixName, command)
        self.logger.info(msg=msg)
    
    def logDebugCall(self, prefixName,command):
        # self.logger.debug(' {}: {}'.format(f_name, f_locals))
        msg = " {:<15}: {}".format(prefixName, command)
        self.logger.debug(msg=msg)    
# reg=regression("data.csv")
# reg.readFile()

# # slope, intercept, r_value, p_value, std_err=calRegression=regression("data.csv")
# index0=reg.data.index[0]
# x=reg.data.loc[:,"analysis_result"]
# y=reg.data.loc[:,"area_net"]
# sampleVol=reg.data.loc[index0,"spl_volumn"]
# slope, intercept, r_value, p_value, std_err=reg.cal_regression(x,y)
# co2PeakArea=10654.8
# resultDIC=reg.dicContent(co2PeakArea,slope,intercept,sampleVol)
# print("resulDIC( \mu mol/L):{}".format(resultDIC))


# logger = logging.getLogger('mylogger')
# logger.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler()



# # Open and read the JSON file
# with open('picarro_G2302.json', 'r') as file:
#     config = json.load(file)
# file.close()

# if config["logStart"] in ["True","true","TRUE"]:
#     logFolder=config["logFolder"]
#     logDtStr = datetime.datetime.now().strftime("%Y%m%d")
#     file_handler = logging.FileHandler(logFolder+'_{}.txt'.format(logDtStr))
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     console_handler.setFormatter(formatter)
#     file_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
#     logger.addHandler(file_handler)


# rs232Device=RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
#                  request=False, hello=None, answer=None, termin=chr(13),
#                  timesleep=0.2,logger=None)


# picarro = Picarro_G2301(rs232Device, logger, config, False)
# picarro._Meas_GetBuffer()
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

# if config["logStart"]=="True":
#     logger.handlers.clear()
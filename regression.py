import numpy as np
import scipy.stats as st
import pandas as pd
import traceback
import serial
import time
from threading import RLock
import re
from scipy import integrate
import datetime
lock = RLock()
# from logger_moudle import logger
import logging
pd.options.display.float_format = '{:.3f}'.format
class regression:
    def __init__(self, fileName=None,data=None ):
        self.fileName = fileName
        self.data=data


    def readData(self):
        if self.data is None:
            datas=pd.read_csv(self.fileName,index_col=0 )
            datas['meas_datetime'] = pd.to_datetime(datas['meas_datetime'])
        else:
            datas=self.data
        for i in datas.index:
            #########################
            # datas.loc[i,"analysis_time"].timestamp()= utc time stamp, so subtract 8*60*60
            #####################
            datas.loc[i, 'meas_datetimestamp'] = datas.loc[i,"meas_datetime"].timestamp()-60*60*8
        # datas['analysis_timestamp'] =datas["analysis_time"].value
        print(datas)
        # y = datas.loc[:,""] 
        # x = datas.iloc[:, 2] 
        # subData=datas.loc[(datas["type"]=="Valid")]
        self.data=datas   
        return datas
    def cal_regression(self, x,y):
        # datas = pd.read_excel(self.fileName) # 读取 excel 数据，引号里面是 excel 文件的位置


        # # 线性拟合，可以返回斜率，截距，r 值，p 值，标准误差
        slope, intercept, r_value, p_value, std_err = st.linregress(x, y)

        print("slope:{}\nintercept:{}\nr:{}".format(slope,intercept,r_value))# 输出斜率
        return slope, intercept, r_value, p_value, std_err 

    def dicContent(self,co2PeakArea,slope,intercept,sampleVol):
        ################################################
        # co2PeakAre=slope*DIC+intercept
        # sampleVol unit :mL
        # diContent unit :\mu mol/mL
        # diContentEachL unit : \mu mol/L or \muM
        # ##############################################
        
        dicContent=(co2PeakArea-intercept)/slope
        dicContentEachL=dicContent/sampleVol 
        
        return dicContent


    def convert_density(T,S):
        ################################################
        # from \mu M/L to \mu mol/kg
        ################################################
        density = (999.842594 + 0.06793952*T - 0.00909529*T^2 + 0.0001001685*T^3 -0.000001120083*T^4 + 0.000000006536332*T^5 + (0.824493-0.0040899*T + 0.000076438*T^2 - 0.00000082467*T^3 + 0.0000000053875*T^4)*S + (-0.00572466 + 0.00010227*T - 0.0000016546*T^2)*S^1.5 +0.00048314*S^2)/1000
        return density

    def calNetArea(self,x,y,baseValue=0):        
        result=integrate.trapezoid(y, x)
        print(result)
        if result-baseValue<0:
            result2=0
        else:
            result2=result-baseValue
        return result









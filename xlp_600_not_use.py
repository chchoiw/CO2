import traceback
import re
from communication import RS232_Device
import logging

class XLP_600:
    def __init__(self,rs232Con,logger,prodFlag):
        self.rs232Conn=rs232Con
        self.logger=logger
        self.prodFlag=prodFlag     
        self.beginSymbol=chr(2)
        self.endSymbol=chr(3)

    def handleError(self,code):
        errorCodeDict={
            0:"Error Free Condition",
            1:"Initialization error.",
            2:"Invalid Command.",
            3:"Invalid Operand.",
            6:"EEPROM Failure.",
            7:"Device Not Initialized.",
            8:"Internal failure.",
            9:"Plunger Overload.",
            10:"Valve Oerload.",
            11:"Plunger Move Not Allowed.",
            12:"Internal failure.",
            14:"A/D converter failure.",
            15:"Command Overflow"
        }
        for i in errorCodeDict.keys():
            if code in [chr(i),i]:
                self.logger.error("Error Code:{}-{}".format(i,errorCodeDict[i]))
                return True
        return False

    def reportCommand(self,rptName):
        reportCmdDict={
            "StartSpeed":"?1",
            "TopSpeed":"?2",
            "CutoffSpeed":"?3",
            "ActualPosition":"?4",
            "ValvePosition":"?6",
            "CommandBufferStatus":"?10",
            "NumberOfBacklashIncrements":"?12",
            "StatusOfAuxiliaryInput1":"?13",
            "StatusOfAuxiliaryInput2":"?14",
            "NumberOfPumpInitalizations":"?15",
            "NumberOfPlungerMovements":"?16",
            "NumberOfValveMovements":"?17",
            "NumberOfValveMovementsSinceLastReport":"?18",
            "FirmwareVersion":"?20",
            "TheZeroGapIncrements":"?24",
            "SlopeCodeSetting":"?25",
            "CurrentMode":"?28",
            "TheDeviceStatus":"?29",
            "PumpConfiuration":"?76",
            "Voltage":"*",
            "UserData":"<",
        }
        return reportCmdDict[rptName]
    
    def excCMD(self,command):
        if self.prodFlag:
            buffReturn=self.rs232Conn.query(command)        
        else:
            buffReturn=chr(13)+"2024-09-12 00:00:00;23.480;1.233;20.111;"+chr(13)+\
           "2024-09-12 00:01:00;23.480;1.233;20.111;"+chr(13)+\
                "2024-09-12 00:02:00;23.480;1.233;20.111;"+chr(13)
        if self.handleError(buffReturn): return 

        self.logger.info("Return result:")





logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('log.txt')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.warning("test")
rs232Device=RS232_Device(device_name="Picarro_G2301", com='COM1', port=9600,
                 request=False, hello=None, answer=None, termin=chr(13),
                 timesleep=0.2,logger=None)


xlp600=XLP_600(rs232Device,logger,False)
xlp600.excCMD("")
logger.handlers.clear()

# https://github.com/benpruitt/tecancavro




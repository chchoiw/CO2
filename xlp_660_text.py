from tecancavro.models import TecanXLP6000

from tecancavro.transport import TecanAPISerial, TecanAPINode
from time import sleep
# from .tecanapi import TecanAPI
# from .transport import TecanAPISerial, TecanAPINode, TecanAPITimeout
# from .syringe import Syringe, SyringeError, SyringeTimeout
# from .models import XCaliburD


# Functions to return instantiated XCaliburD objects for testing

def returnSerialXCaliburD():
    # test0 = XCaliburD(com_link=TecanAPISerial(0, '/dev/tty.usbserial', 9600))
    # /dev/ttyUSB0
    test0 = XCaliburD(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600))
    return test0

def returnNodeXCaliburD():
	test0 = XCaliburD(com_link=TecanAPINode(0, '192.168.1.140:80'), waste_port=6)
	return test0

def findSerialPumps():
    return TecanAPISerial.findSerialPumps()

def getSerialPumps():
    ''' Assumes that the pumps are XCaliburD pumps and returns a list of
    (<serial port>, <instantiated XCaliburD>) tuples
    '''
    pump_list = findSerialPumps()
    return [(ser_port, XCaliburD(com_link=TecanAPISerial(0,
             ser_port, 9600))) for ser_port, _, _ in pump_list]


if __name__ == '__main__':
    print("find serial pumps")
    print(findSerialPumps(),getSerialPumps())
    print("init tecancavro")
    pump = TecanXLP6000(com_link=TecanAPISerial(0, '/dev/ttyUSB0', 9600))
    # pump.init( init_force=0, direction="CW", in_port=0,out_port=0)
    # print(pump.getStartSpeed())
    # print(pump.getTopSpeed())
    # print(pump.getCutoffSpeed())
    # print(pump.sim_state['start_speed'],
    #       pump.sim_state['top_speed'], pump.sim_state['cutoff_speed'])
    waitSeconds=pump.extractToWaste( in_port=1, volume_ul=1100, out_port=3,
                   speed_code=None, minimal_reset=False, flush=False)
    print(waitSeconds)
    pump.waitReady(waitSeconds)
    # waitSeconds=pump.primePort( in_port=1, volume_ul=100, speed_code=None, out_port=3)
    # print(waitSeconds)
    # pump.waitReady(waitSeconds)
    # pump.cmd_chain="O9A0I1A0O9A0"
    # pump.cmd_chain="O4"
    
    # waitSeconds=pump.executeChain( minimal_reset=False)
    # print(waitSeconds)
    # sleep(1)
    # pump.waitReady(1)
    # for i in range(30):
    #     pump.cmd_chain='Q'
    #     pump.executeChain( minimal_reset=False)
    #     sleep(0.2)

    # print(pump.getStartSpeed())
    # print(pump.getTopSpeed())
    # print(pump.getCutoffSpeed())
    # print(pump.sim_state['start_speed'],pump.sim_state['top_speed'],pump.sim_state['cutoff_speed'])
    # # print(pump)
    

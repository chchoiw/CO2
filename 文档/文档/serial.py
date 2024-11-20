import random
import time
import serial

# # 串口客户端（正常）
class SerialHelper(serial.Serial):
    """
    serial client
    """
    def __init__(self, port,
                 baudrate=9600,
                 bytesize=serial.EIGHTBITS,
                 timeout=1,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE):
        super().__init__(port=port,
                         baudrate=baudrate,
                         bytesize=bytesize,
                         timeout=timeout,
                         parity=parity,
                         stopbits=stopbits
                         )
    def send_cmd(self, cmd, sleep_time=0.5):
        ret_len = self.write((cmd + '\r').encode())
        # 发送完毕后，等待指令返回结果
        time.sleep(sleep_time)
        return ret_len

    def read_cmd(self):
        response = self.readline().decode('utf-8', errors="ignore")
        return response

    def read_all_cmd(self):
        response = self.read_all().decode('utf-8', errors="ignore")
        return response

    def read_num(self, num):
        response = self.read(num)
        return response

# 串口客户端（模拟）
class SerialHelperSim(SerialHelper):

    def open(self):
        return

    def send_cmd(self, cmd, sleep_time=0.3):
        time.sleep(sleep_time)
        return

    def read_cmd(self):
        response = ''
        return response

    def read_all_cmd(self):
        response = f"`{int(random.randint(0,3000))}"
        return response

    def read_num(self, num: int):
        response = '1' * num
        return response

import math
import re
import time
from abc import abstractmethod

from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox

from app.helpers.my_logger import LOGGER
from app.helpers.my_logger import LogType
from app.helpers.serial import SerialHelper


class PumpBase(object):
    def __init__(
            self,
            num: int,
            mod: int,
            max_vol: float,
            max_step: int,
            pump_serial: SerialHelper,
            read_position_by_cmd=True,
            name="PumpBase"
    ) -> None:
        self.name = name
        self.num = num  # 泵的指令地址
        self.mod = mod
        self.max_vol = max_vol
        self.max_step = max_step
        self.pump_serial = pump_serial
        self.read_position_by_cmd = read_position_by_cmd
        self.pump_current_position = 0

        self.not_support_tip = f"{self.num}号注射泵型号{self.name}不支持该操作，请联系开发商"

    # 根据体积，计算步数
    def get_steps_by_vol(self, vol):
        steps = math.ceil(vol / self.max_vol * self.max_step)  # 向上取整
        return steps

    # 根据步数，计算体积
    def get_vol_by_steps(self, steps):
        v = steps / self.max_step * self.max_vol
        return v

    # 初始化泵，并设置泵的模式
    @abstractmethod
    def initialization(self):
        raise NotImplementedError(self.not_support_tip)

    # 润洗
    @abstractmethod
    def clean(self, margin, times):
        raise NotImplementedError(self.not_support_tip)

    # 通过串口查询的方式，获取泵的绝对位置
    @abstractmethod
    def read_pump_position(self) -> int:
        raise NotImplementedError(self.not_support_tip)

    # 执行吸样加样命令，要求所有参数正确无误
    @abstractmethod
    def send_sample_cmd(self, vol, direction, input_speed=3000, output_speed=3000):
        raise NotImplementedError(self.not_support_tip)


# 第一版的型号
class KloehnBase(PumpBase):

    # 初始化
    def initialization(self):
        cmd = '/{}W4R'.format(self.num)
        LOGGER.log(LogType.INFO, self.name, f'发送初始化{self.num}号泵初始化指令{cmd}')
        self.pump_serial.send_cmd(cmd)
        self.pump_serial.send_cmd(f'/{self.num}A0R')
        self.pump_current_position = 0

    # 润洗
    def clean(self, margin, times):
        cmd1 = '/{}gIV3000A{}M{}OA0G{}R'.format(self.num, self.max_step, margin, times)
        LOGGER.info(self.name, f'发送{self.num}号泵润洗指令{cmd1}')
        self.pump_serial.send_cmd(cmd1)
        self.pump_current_position = 0

    # 计算泵的绝对位置，0-48000(MAX)
    def read_pump_position(self):
        # 先清空缓存
        self.pump_serial.read_all_cmd()
        # 发送命令再读取
        self.pump_serial.send_cmd("/{}?".format(self.num))
        result = self.pump_serial.read_all_cmd()
        p = re.compile(r'`(\d+)')
        r = re.search(p, result)
        if not r:
            raise Exception('未找到位置信息，请确认注射泵型号是否正确')
        position = int(r.group(1))
        self.pump_current_position = position
        return position

    # 执行吸样加样命令，要求所有参数正确无误，属于私有函数
    def send_sample_cmd(self, vol, direction, input_speed=3000, output_speed=3000):
       
        # 泵的固定准备时间 单位：秒
        _prepare_time = 2
        _exe_cmd_time = 0.3
        _sync_time = 0.3

        tip_str = '吸样'
        if direction == -1:
            tip_str = '加样'

        # 计算泵应该处于什么样的绝对位置
        steps = self.get_steps_by_vol(vol)

        if self.read_position_by_cmd:
            current_step = self.read_pump_position()
        else:
            current_step = self.pump_current_position

        # LOGGER.info(self.name,f'泵的位置{current_step}')

        res_step = current_step + direction * steps

        # 校正检验
        if res_step > self.max_step:
            res_step = self.max_step
        elif res_step < 0:
            res_step = 0

        # 实际添加的体积
        correct_v = self.get_vol_by_steps(steps)
        if abs(correct_v - vol) >= 0.0001:
            LOGGER.warn(self.name, f"由于最小精度问题，实际{tip_str}体积由{vol}ul修正为{correct_v}ul")

        # 定义input和output
        flag = 'O'
        _speed = output_speed
        if direction == 1:
            # input方向，泵内的溶液会变多，吸样操作
            flag = 'I'
            _speed = input_speed

        # 合成命令
        cmd = '/{}{}V{}A{}R'.format(self.num, flag, _speed, res_step)
        _consume_seconds = steps / _speed

        self.pump_serial.send_cmd(cmd, sleep_time=_exe_cmd_time)

        # 更新状态!! 位置状态
        self.pump_current_position = res_step

        # 等待时间需要加上泵的固定准备时间
        _consume_seconds += _prepare_time + _exe_cmd_time + _sync_time
        LOGGER.info(self.name, f'发送{self.num}号泵{tip_str}{correct_v:.6f}ul指令{cmd},请等待{_consume_seconds:.2f}秒')

        return correct_v, _consume_seconds, res_step


class Kloehn(KloehnBase):
    pass


class TecanBase(PumpBase):

    def clean(self, margin, times):
        _cmd = f"/{self.num}IA{self.max_step}OA0R"
        self.pump_serial.send_cmd(_cmd)
        LOGGER.info(self.name, f"发送润洗指令{_cmd}")

    # 初始化泵，并设置泵的模式
    def initialization(self):
        _cmd = f"/{self.num}ZN{self.mod}R"
        self.pump_serial.send_cmd(_cmd)
        LOGGER.info(self.name, f"发送初始化指令{_cmd}")

    # 通过串口查询的方式，获取泵的绝对位置
    def read_pump_position(self):
        
        # 先清空缓存
        self.pump_serial.read_all_cmd()
        
        # 发送命令再读取
        _cmd = f"/{self.num}?"
        LOGGER.info(self.name, f"发送润洗指令{_cmd}")
        self.pump_serial.send_cmd(_cmd)
        result = self.pump_serial.read_all_cmd()
        
        p = re.compile(r'`(\d+)')
        r = re.search(p, result)
        if not r:
            raise Exception('未找到位置信息，请确认注射泵型号是否正确')
        position = int(r.group(1))
        self.pump_current_position = position
        return position

    # 执行吸样加样命令，要求所有参数正确无误，私有函数
    def send_sample_cmd(self, vol, direction, input_speed=3000, output_speed=3000):
        # 泵的固定准备时间 单位：秒
        _prepare_time = 2
        _exe_cmd_time = 0.3
        _sync_time = 0.3

        tip_str = '吸样'
        if direction == -1:
            tip_str = '加样'

        # 计算泵应该处于什么样的绝对位置
        steps = self.get_steps_by_vol(vol)

        if self.read_position_by_cmd:
            current_step = self.read_pump_position()
        else:
            current_step = self.pump_current_position

        res_step = current_step + direction * steps

        # 校正检验
        if res_step > self.max_step:
            res_step = self.max_step
        elif res_step < 0:
            res_step = 0

        # 实际添加的体积
        correct_v = self.get_vol_by_steps(steps)
        if abs(correct_v - vol) >= 0.0001:
            LOGGER.warn(self.name, f"由于最小精度问题，实际{tip_str}体积由{vol}ul修正为{correct_v}ul")

        # 定义input和output
        flag = 'O'
        _speed = output_speed
        if direction == 1:
            # input方向，泵内的溶液会变多，吸样操作
            flag = 'I'
            _speed = input_speed

        # 合成命令
        cmd = '/{}{}V{}A{}R'.format(self.num, flag, _speed, res_step)
        _consume_seconds = steps / _speed

        self.pump_serial.send_cmd(cmd, sleep_time=_exe_cmd_time)

        # 更新状态!! 位置状态
        self.pump_current_position = res_step

        # 等待时间需要加上泵的固定准备时间
        _consume_seconds += _prepare_time + _exe_cmd_time + _sync_time
        LOGGER.info(self.name, f'发送{self.num}号泵{tip_str}{correct_v:.6f}ul指令{cmd},请等待{_consume_seconds:.2f}秒')

        return correct_v, _consume_seconds, res_step


class TecanXCalibur(TecanBase):
    pass

   
        

class TecanXLP6000(TecanBase):
    pass

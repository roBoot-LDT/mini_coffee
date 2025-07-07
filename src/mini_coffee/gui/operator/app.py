#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2022, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

"""
# Notice
#   1. Changes to this file on Studio will not be preserved
#   2. The next conversion will overwrite the file with the same name
# 
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
#   1. git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
#   2. cd xArm-Python-SDK
#   3. python setup.py install
"""
import sys
import math
import time
import queue
import datetime
import random
import traceback
import threading
from src.mini_coffee.hardware.arm.xarm import version
from src.mini_coffee.hardware.arm.xarm.wrapper import XArmAPI


class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._ignore_exit_state = False
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 20
        self._angle_acc = 500
        self._vars = {}
        self._funcs = {}
        self._robot_init()

    # Robot init
    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.register_state_changed_callback(self._state_changed_callback)

    # Register error/warn changed callback
    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data['error_code']))
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    # Register state changed callback
    def _state_changed_callback(self, data):
        if not self._ignore_exit_state and data and data['state'] == 4:
            self.alive = False
            self.pprint('state=4, quit')
            self._arm.release_state_changed_callback(self._state_changed_callback)

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._arm.connected, self._arm.state, self._arm.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._ignore_exit_state:
                return True
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False

    # Robot Main Run
    def run(self):
        plc = PLC()
        
        try:
            self._angle_speed = 80
            code = self._arm.set_servo_angle(angle=[180.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[188.8, 17.0, 35.0, 9.6, -72.3, -4.8], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            plc.dispenserS(1)
            code = self._arm.set_servo_angle(angle=[180.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[180.0, -24.9, 5.6, 15.6, -60.8, -9.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[159.7, -52.8, 5.7, 12.1, -29.5, -14.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[137.2, -27.4, 34.8, -8.5, -27.3, 5.7], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[132.0, -6.2, 60.6, -14.4, -24.9, 9.4], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[125.7, 6.9, 75.4, -24.9, -24.0, 21.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            plc.relay("all00010000")
            time.sleep(1)
            plc.relay("all00000000")
            
            code = self._arm.set_servo_angle(angle=[132.0, -6.2, 60.6, -14.4, -24.9, 9.4], speed=self._angle_speed, mvacc=self._angle_acc, wait=True, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[137.2, -27.4, 34.8, -8.5, -27.3, 5.7], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[159.7, -52.8, 5.7, 12.1, -29.5, -14.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[180.0, -24.9, 5.6, 15.6, -60.8, -9.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[180.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[265.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[276.5, 83.5, 99.9, -51.5, -82.7, 12.6], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[276.5, 83.5, 99.9, -57.6, -67.5, 18.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[266.7, 83.5, 98.0, -70.5, -71.1, 17.5], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[265.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
            code = self._arm.set_servo_angle(angle=[180.0, 0.0, 10.0, -2.8, -75.0, 0.0], speed=self._angle_speed, mvacc=self._angle_acc, wait=False, radius=5.0)
            if not self._check_code(code, 'set_servo_angle'):
                return
        except Exception as e:
            self.pprint('MainException: {}'.format(e))
        finally:
            self.alive = False
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
            self._arm.release_state_changed_callback(self._state_changed_callback)

import time, socket, os
from dotenv import load_dotenv # type: ignore
from mini_coffee.utils.logger import setup_logger

logger = setup_logger()
load_dotenv()

class PLC:
    def __init__(self):
        self.RELAY_IP = str(os.getenv("RELAY_IP", "192.168.1.130"))
        self.RELAY_UTP_PORT = int(os.getenv("RELAY_UTP_PORT", 5005))
        self.BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", 1024))
        self.DISM = str(os.getenv("DISPENSER_M", "all10000000"))
        self.DISS = str(os.getenv("DISPENSER_S", "all00000100"))
        self.BIN = str(os.getenv("BIN", "all00001000"))
        self.SHIELD = str(os.getenv("SHIELD", "all00000001"))
        self.rel = [
            ["off1", "on1"],
            ["off2", "on2"],
            ["off3", "on3"],
            ["off4", "on4"],
            ["off5", "on5"],
            ["off6", "on6"],
            ["off7", "on7"],
            ["off8", "on8"]
        ]

    def relay(self, port_state) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(bytes(port_state, 'utf-8'),(self.RELAY_IP, self.RELAY_UTP_PORT))

    def dispenserS(self, sec) -> None:
        self.relay("all01000000")
        time.sleep(sec)
        self.relay("all00000000")

    def dispenserM(self, sec) -> None:
        self.relay(self.DISM)
        time.sleep(sec)
        self.relay("all00000000")
    
    def shield(self, sec) -> None:
        self.relay(self.SHIELD)
        time.sleep(sec)
        self.relay("all00000000")

    def bin(self, sec) -> None:
        self.relay(self.BIN)
        time.sleep(sec)
        self.relay("all00000000")
        
    def trigger_all(self) -> None:
        logger.info("Triggering all relays")
        self.relay("all11111111")
        time.sleep(2)
        self.relay("all00000000")

    def detect(self) -> None:
        # Generate port states with only one '1' in each (8 relays)
        for i in range(8):
            state = f"all{format(1 << i, '08b')}"
            logger.info(f"Detecting ports: {state}")
            self.relay(state)
            time.sleep(2)
            
if __name__ == '__main__':
      # Turn on all relays
    
    RobotMain.pprint('xArm-Python-SDK Version:{}'.format(version.__version__))
    arm = XArmAPI('192.168.1.191', baud_checkset=False)
    robot_main = RobotMain(arm)
    robot_main.run()
   

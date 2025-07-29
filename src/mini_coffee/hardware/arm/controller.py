import time, os
import traceback
try:
    from mini_coffee.hardware.arm.xarm.tools import utils
except:
    pass
from mini_coffee.hardware.arm.xarm import version
from mini_coffee.hardware.arm.xarm.wrapper import XArmAPI
from dotenv import load_dotenv # type: ignore

load_dotenv()
    
class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._ignore_exit_state = False
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 50
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
                

class MockArmController:
    def __init__(self):
        self.current_position = "Arm Base"
        
    def move_to(self, **kwargs):
        # Existing movement logic
        pass
        
    def get_position_name(self):
        return self.current_position
        
    def set_position_name(self, name):
        self.current_position = name
    
class xArmRobot: 
    def __init__(self):
        def pprint(*args, **kwargs):
            try:
                stack_tuple = traceback.extract_stack(limit=2)[0]
                print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
            except:
                print(*args, **kwargs)

        pprint('xArm-Python-SDK Version:{}'.format(version.__version__))

        self.arm = XArmAPI(os.getenv("XARMAPI", "192.168.1.191"))
        self.arm.clean_warn()
        self.arm.clean_error()
        self.arm.motion_enable(True)
        self.arm.set_simulation_robot(False)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        self.variables = {}
        self.params = {'speed': 200, 'acc': 8000, 'angle_speed': 100, 'angle_acc': 1000, 'events': {}, 'variables': self.variables, 'callback_in_thread': True, 'quit': False}
        time.sleep(1)

        # Register error/warn changed callback
        def error_warn_change_callback(self, data):
            if data and data['error_code'] != 0:
                self.params['quit'] = True
                pprint('err={}, quit'.format(data['error_code']))
                self.arm.release_error_warn_changed_callback(error_warn_change_callback)
        self.arm.register_error_warn_changed_callback(error_warn_change_callback)

        # Register state changed callback
        def state_changed_callback(data):
            if data and data['state'] == 4:
                if self.arm.version_number[0] >= 1 and self.arm.version_number[1] >= 1 and self.arm.version_number[2] > 0:
                    self.params['quit'] = True
                    pprint('state=4, quit')
                    self.arm.release_state_changed_callback(state_changed_callback)
        self.arm.register_state_changed_callback(state_changed_callback)

        # Register counter value changed callback
        if hasattr(self.arm, 'register_count_changed_callback'):
            def count_changed_callback(data):
                if not self.params['quit']:
                    pprint('counter val: {}'.format(data['count']))
            self.arm.register_count_changed_callback(count_changed_callback)

        # Register connect changed callback
        def connect_changed_callback(data):
            if data and not data['connected']:
                self.params['quit'] = True
                pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
                self.arm.release_connect_changed_callback(error_warn_change_callback)
        self.arm.register_connect_changed_callback(connect_changed_callback)

        if not self.params['quit']:
            self.arm.set_tcp_offset([0, 0, 312, 0, 80, 0], wait=True)
            #arm.set_tcp_offset([0, 0, 230, 0, 0, 0], wait=True)
            self.arm.set_state(0)

        if hasattr(self.arm, 'release_count_changed_callback'):
            self.arm.release_count_changed_callback(count_changed_callback) # type: ignore
        self.arm.release_error_warn_changed_callback(state_changed_callback)
        self.arm.release_state_changed_callback(state_changed_callback)
        self.arm.release_connect_changed_callback(error_warn_change_callback)

    def errprint(self, *args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    def home_pose(self):
        self.move_joint([90.0,0.0,-180.0,0.0,90.0,0.0], ang_speed=50,ang_acc=50,set_wait=True, set_radius=0)

    def grip_open(self):
        self.arm.set_tgpio_digital(0, 1)
        self.arm.set_tgpio_digital(1, 0)
        print('gripper open')
        time.sleep(1)

    def grip_close(self):
        self.arm.set_tgpio_digital(0, 0)
        self.arm.set_tgpio_digital(1, 1)
        print('gripper close')
        time.sleep(1)

    # Linear Motion
    def move_linear(self, coords, set_speed=50,set_acc=50,set_wait=False,set_radius=5):
        if not self.params['quit']:
            self.params['speed'] = set_speed
        if not self.params['quit']:
            self.params['acc'] = set_acc
        if self.arm.error_code == 0 and not self.params['quit']:
            code = self.arm.set_position(*coords, speed=self.params['speed'], mvacc=self.params['acc'], wait=set_wait, radius=set_radius)
            if code != 0:
                self.params['quit'] = True
                self.errprint('set_position, code={}'.format(code))                

    # Joint Motion
    def move_joint(self, coords, ang_speed=25,ang_acc=25,set_wait=False, set_radius=5):
        if not self.params['quit']:
            self.params['angle_speed'] = ang_speed
            self.params['angle_acc'] = ang_acc
        if self.arm.error_code == 0 and not self.params['quit']:
            code = self.arm.set_servo_angle(angle=coords, speed=self.params['angle_speed'], mvacc=self.params['angle_acc'], wait=set_wait, radius=set_radius)
            if code != 0:
                self.params['quit'] = True
                self.errprint('set_servo_angle, code={}'.format(code))
                

class xArmRobot_test: 
    """Mock class for xArmRobot to simulate arm movements for testing"""
    def __init__(self):
        self.arm = True

    def errprint(self, *args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    def home_pose(self):
        print("Moving to home position")

    def grip_open(self):
        print('gripper open')
        time.sleep(1)

    def grip_close(self):
        print('gripper close')
        time.sleep(1)

    # Linear Motion
    def move_linear(self, coords, set_speed=50,set_acc=50,set_wait=False,set_radius=5):
        print("Moving linear into", coords, "with speed", set_speed, "and acceleration", set_acc)               

    # Joint Motion
    def move_joint(self, coords, ang_speed=25,ang_acc=25,set_wait=False, set_radius=5):
        print("Moving joint into", coords, "with speed", ang_speed, "and acceleration", ang_acc)
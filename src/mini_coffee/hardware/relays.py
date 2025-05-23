import time, socket

class PLC:
    def __init__(self):
        self.RELAY_IP = '192.168.1.130'
        self.RELAY_UTP_PORT = 5005
        self.BUFFER_SIZE = 1024
        self.rel = [["off1","on1"],["off2","on2"],["off3","on3"],["off4","on4"],["off5","on5"],["off6","on6"],["off7","on7"],["off8","on8"]]

    def relay(self, port_state):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(bytes(port_state, 'utf-8'),(self.RELAY_IP, self.RELAY_UTP_PORT))

    def group_1(self, sec):
        self.relay("all00000100")
        time.sleep(sec)
        self.relay("all00000000")
        pass

    def group_2(self, sec):
        self.relay("all10000000")
        time.sleep(sec)
        self.relay("all00000000")
        pass
    
if __name__ == "__main__":
    plc = PLC()
    plc.group_1(1)
    
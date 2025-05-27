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
        self.relay(self.DISS)
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
        
if __name__ == "__main__":
    plc = PLC()
    plc.relay("all11111111")  # Turn on all relays
    time.sleep(2)
    plc.relay("all00000000")  # Turn off all relays
    
import serial

ser = serial.Serial(
    port='/COM4',
    baudrate=57600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

while(True):
    print(ser.readline())

ser.close()
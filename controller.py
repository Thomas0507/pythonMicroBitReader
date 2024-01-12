# Program to control passerelle between Android application
# and micro-controller through USB tty
import time
import argparse
import signal
import sys
import socket
import socketserver
import serial
import threading
import json


HOST           = "0.0.0.0"
UDP_PORT       = 10000
MICRO_COMMANDS = ["TL" , "LT"]
FILENAME        = "values.txt"
LAST_VALUE      = ""


REFRESH_FETCH = 200 # refresh le fetch des capteurs toutes les 200 secondes


class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        current_thread = threading.current_thread()
        print("{}: client: {}, wrote: {}".format(current_thread.name, self.client_address, data))
        if data != "":
                        if data in MICRO_COMMANDS: # Send message through UART
                                sendUARTMessage(data)
                                
                        elif data == "getValues()": # Sent last value received from micro-controller
                                socket.sendto(LAST_VALUE, self.client_address) 
                                # TODO: Create last_values_received as global variable      
                        else:
                                print("Unknown message: ",data)

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


# send serial message 
# SERIALPORT = "/dev/ttyACM0"
# BAUDRATE = 115200
ser = serial.Serial("/dev/ttyACM1", baudrate = 115200)

def initUART():        
        # ser = serial.Serial(SERIALPORT, BAUDRATE)
        # ser.port=SERIALPORT
        # ser.baudrate=BAUDRATE
        ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        ser.parity = serial.PARITY_NONE #set parity check: no parity
        ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        ser.timeout = None          #block read

        # ser.timeout = 0             #non-block read
        # ser.timeout = 2              #timeout block read
        ser.xonxoff = False     #disable software flow control
        ser.rtscts = False     #disable hardware (RTS/CTS) flow control
        ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
        #ser.writeTimeout = 0     #timeout for write
        print ('Starting Up Serial Monitor')
        try:
                if(ser.isOpen() == False):
                        ser.open()
        except serial.SerialException:
                print("Serial {} port not available".format(SERIALPORT))
                exit()

# convert list to string and send on string at a time        
def sendMessages(sensorList):
        # reset_input_buffer()
        # reset_output_buffer()
        for s in sensorList:
                sendUARTMessage(str(s) + '|')
                ser.flush()
                line = ser.readline()
                print(line.decode('utf-8'))

# postData to DjangoAPI
def postData(data):
        print(data)



# Main program logic follows:
if __name__ == '__main__':
        initUART()
        f= open(FILENAME,"a")
        print ('Press Ctrl-C to quit.')

        server = ThreadedUDPServer((HOST, UDP_PORT), ThreadedUDPRequestHandler)

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True

        try:
                while (ser.isOpen()):
                        server_thread.start()
                        print("Server started at {} port {}".format(HOST, UDP_PORT))
                        ser.reset_input_buffer()
                        ser.reset_output_buffer()
                        while(1):                    
                                print("Waiting for data...")
                                # ser.flush()
                                line = ser.readline()
                                ser.reset_input_buffer()
                                ser.reset_output_buffer()
                                postData(line.decode('utf-8'))  
        except (KeyboardInterrupt, SystemExit):
                server.shutdown()
                server.server_close()
                f.close()
                ser.close()
                exit()
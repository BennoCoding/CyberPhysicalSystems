#!/usr/bin/env python3


import curses
import signal
import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from gpiozero import Motor, Robot

# pins for the motors
LEFT_PINS = ('GPIO19', 'GPIO13')
RIGHT_PINS = ('GPIO12', 'GPIO18')

STOP_VOLTAGE = 1.85
MICRO_HOLD = 0.07       # small puffer for the latency of the SSH connection

# start hardware
robot = Robot(left=Motor(*LEFT_PINS), right=Motor(*RIGHT_PINS))
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
mcp_chip = MCP.MCP3008(spi, digitalio.DigitalInOut(board.CE0))
sensor = AnalogIn(mcp_chip, MCP.P0)

def brake():
    robot.left_motor.forward_device.value = 1
    robot.left_motor.backward_device.value = 1
    robot.right_motor.forward_device.value = 1
    robot.right_motor.backward_device.value = 1
    time.sleep(0.3)
    robot.stop()

def main(stdscr):
    stdscr.nodelay(True)
    stdscr.addstr(0, 0, "Control: w/s = forward/backward, a/d = turn, space = stopp, +/- = speed, q = quit")
    



    speed = 0.6
    last_valid_key= -1
    until = 0.0
    
    try:
        while True:
            now = time.monotonic()
            key_pressed = False
            key = stdscr.getch()


            while key != -1:
                if key == ord('q'):
                    return
                elif key == ord(' '):
                    until = 0
                    last_valid_key = -1
                elif key == ord('+'):
                    speed = min(1.0, speed + 0.1)
                elif key == ord('-'):
                    speed = max(0.2, speed - 0.1)
                elif key in (ord('w'), ord('s'), ord('a'), ord('d')):
                    last_valid_key = key
                    until = now + MICRO_HOLD
                    key_pressed = True



                key = stdscr.getch()
            
            volt = sensor.voltage
            blocked = volt > STOP_VOLTAGE
            status = "stopp"
            
            driving = now < until
            
            if driving:
                if last_valid_key == ord('w'):
                    if not blocked:
                        robot.forward(speed)
                        status = "forward"
                    else:
                        if robot.value != (0, 0):
                            brake()
                        status = "obstacle"
                elif last_valid_key == ord('s'):
                    robot.backward(speed)
                    status = "backward"
                elif last_valid_key == ord('a'):
                    robot.left(speed)
                    status = "left"
                elif last_valid_key == ord('d'):
                    robot.right(speed)
                    status = "right"
            else:
                robot.stop()
                status = "stopp"
                
            stdscr.addstr(2, 0, f"Status: {status:<10} Speed: {speed:.1f}  Sensor: {volt:.2f} V      ")
            time.sleep(0.02)
            
    finally:
        robot.stop()




def handle_exit(signum, frame):
    raise SystemExit




if __name__ == '__main__':
    signal.signal(signal.SIGHUP, handle_exit)
    curses.wrapper(main)
import machine
import time
import neopixel
import asyncio
import struct
import network
from machine import Pin, PWM
from mqtt import MQTTClient

class Car:
    
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.driveForward = False
        self.driveBackward = False
        self.driveRight = False
        self.driveLeft = False
        self.motorOn = False
        self.motorOff = False
        
        # Pico board initializations: neopixel, led, buzzer
        self.neo = neopixel.NeoPixel(Pin(28), 1)
        self.button = Pin(8, Pin.IN, Pin.PULL_UP)
        self.blue_led = PWM(Pin(7, Pin.OUT))
        self.blue_led.freq(100)
        self.buzzer = PWM(Pin(18, Pin.OUT))
        self.buzzer.freq(440)
        self.motor1_a = PWM(Pin(0, Pin.OUT))
        self.motor1_b = PWM(Pin(1, Pin.OUT))
        self.motor1_a.freq(1000)
        self.motor1_b.freq(1000)

        # Call internet connection
        self.internet_connection()
        self.mqtt_subscribe()


    def mqtt_subscribe(self):
        # MQTT initialization of client and subscribing to topic 'Mater'
        mqtt_broker = 'broker.hivemq.com'
        port = 1883
        topic_sub = 'ME35-24/mater'

        def callback(topic, msg):
            topic, msg = topic.decode(), msg.decode()
            print(msg)
            if msg == "1.00, 0.00":
                print('Start')
                self.motorOff = False
                self.motorOn = True
                self.motor_control()
            elif msg == "0.00, 1.00":
                print('Stop')
                self.motorOn = False
                self.motorOff = True
                self.motor_control()
            elif msg == "right":
                self.driveRight = True
                self.driveForward = False
                self.driveBackward = False
                self.driveLeft = False
                self.turn_Right()
            elif msg == "left":
                self.driveRight = False
                self.driveForward = False
                self.driveBackward = False
                self.driveLeft = True
                self.turn_Left()
            elif msg == "forward":
                self.driveRight = False
                self.driveForward = True
                self.driveBackward = False
                self.driveLeft = False
                self.forward()
            elif msg == "backward":
                self.driveRight = False
                self.driveForward = False
                self.driveBackward = True
                self.driveLeft = False
                self.backward()


        self.client = MQTTClient('ME35_mater', mqtt_broker, port, keepalive=60)
        self.client.connect()
        print('Connected to %s MQTT broker' % mqtt_broker)
        self.client.set_callback(callback)  # Set the callback for incoming messages
        self.client.subscribe(topic_sub.encode())  # Subscribe to a topic
        print(f'Subscribed to topic {topic_sub}')  # Debug print

    async def check_mqtt(self):
        while True:
            self.client.check_msg()
            await asyncio.sleep(.01)

    def internet_connection(self):
        try:
            self.wlan.active(True)
            self.wlan.connect('Tufts_Robot', '')

            while self.wlan.ifconfig()[0] == '0.0.0.0':
                print('.', end=' ')
                time.sleep(1)

            # We should have a valid IP now via DHCP
            print(self.wlan.ifconfig())
        except Exception as e:
            print("Failed Connection: ", e)
            quit()

    def motor_control(self):
        print("in motor control")
        if self.motorOn:
            print("motor on")
            
        elif self.motorOff:
            self.motor1_a.duty_u16(0)
            self.motor1_b.duty_u16(0)
            print("motor off")
            
    def turn_Right(self):
        if self.driveRight and self.motorOn:
            self.motor1_a.duty_u16(0)
            self.motor1_b.duty_u16(65535)
            print("Turning right")

    def turn_Left(self):
        if self.driveLeft and self.motorOn:
            self.motor1_a.duty_u16(0)
            self.motor1_b.duty_u16(0)
            print("Turning left")
    
    def forward(self):
        if self.driveForward and self.motorOn:
            self.motor1_a.duty_u16(0)
            self.motor1_b.duty_u16(65535)
            print("Forward")

    def backward(self):
        if self.driveBackward and self.motorOn:
            self.motor1_a.duty_u16(50000)
            self.motor1_b.duty_u16(0)
            print("Backward")

    async def main(self):
        asyncio.create_task(self.check_mqtt())
        asyncio.get_event_loop().run_forever()

# Create Car instance
c = Car()

asyncio.run(c.main())
# To run the MQTT loop, you might want to create an asyncio loop here if necessary

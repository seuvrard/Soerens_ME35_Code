import time
from BLE_CEEO import Yell
from mqtt import MQTTClient
import asyncio
from machine import Pin, ADC  # Import machine's ADC for reading LDR values


def lightsensor():
    """Reads the LDR value from ADC pin 27."""
    ldr = ADC(27)  # Initialize an ADC object for pin 27
    ldr_value = ldr.read_u16()  # Read the LDR value as a 16-bit unsigned integer
    print("LDR Value:", ldr_value)  # Print the LDR value to the console
    return ldr_value


async def music():
    """Sends music notes with pauses based on the light sensor value."""
    NoteOn = 0x90
    NoteOff = 0x80
    StopNotes = 123
    SetInstroment = 0xC0
    Reset = 0xFF

    velocity = {'off': 0, 'pppp': 8, 'ppp': 20, 'pp': 31, 'p': 42, 'mp': 53,
                'mf': 64, 'f': 80, 'ff': 96, 'fff': 112, 'ffff': 127}

    try:
        p = Yell('Soeren2', verbose=True, type='midi')
        p.connect_up()
    except Exception as e:
        print(e)
        return

    channel = 0
    note = 55
    cmd = NoteOn

    channel = 0x0F & channel
    timestamp_ms = int(time.time() * 1000)  # Replace MicroPython's time.ticks_ms()
    tsM = (timestamp_ms >> 7 & 0b111111) | 0x80
    tsL = 0x80 | (timestamp_ms & 0b1111111)

    c = cmd | channel
    payload = bytes([tsM, tsL, c, note, velocity['f']])
    payload2 = bytes([tsM, tsL, c, note, velocity['off']])

    for i in range(15):
        ldr_value = lightsensor()  # Get the LDR value

        if ldr_value <= 400:  # If light sensor value is below 400, pause
            print("Paused, waiting for sensor value to rise...")
            # Instead of return, use time.sleep to pause
            time.sleep(1)  # Pause for 1 second
            continue  # Go to the next iteration and check sensor value again

        # If the sensor value is above 400, play the note
        print("Unpaused, playing note")
        p.send(payload)  # Send the note

        await asyncio.sleep(1)  # Normal pause after sending each payload
            
    p.disconnect()


async def main():
    """Main function to handle MQTT messages and trigger music."""
    mqtt_broker = 'broker.hivemq.com'
    port = 1883
    topic_sub = 'ME35-24_se'  # Topic to subscribe to

    def callback(topic, msg):
        """Callback function to handle MQTT messages."""
        print((topic.decode(), msg.decode()))

    client = MQTTClient('Soeren', mqtt_broker, port, keepalive=60)
    client.connect()
    print('Connected to %s MQTT broker' % mqtt_broker)
    client.set_callback(callback)  # Set the callback for received messages
    client.subscribe(topic_sub.encode())  # Subscribe to the topic

    while True:
        client.check_msg()  # Check for MQTT messages
        if str(msg.decode()) == "on":  # Properly decode the message
            await music()  # Call the async music function with await
        elif str(msg.decode()) == "off":
            client.disconnect()  # Disconnect the client
        await asyncio.sleep(1)  # Non-blocking sleep to avoid high CPU usage


# Run the main function using asyncio
# Run just the music: mqtt not working
asyncio.run(main())

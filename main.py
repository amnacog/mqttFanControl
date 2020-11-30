#!/usr/bin/env python3

import threading
import logging
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

pwmPin = 13
mqtt_host="pi1.iot"
mqtt_port=1883

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(pwmPin, GPIO.OUT)
pwmctr=GPIO.PWM(pwmPin, 100)
pwmctr.start(100)

formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s:\t%(message)s')
logger = logging.getLogger('fan')
logger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler('/var/log/fan.log')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

#console output
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

def mqtt_on_connect(client, userdata, flags, rc):
    logger.info('Connected to the broker...')
    client.subscribe('cmnd/fan/DUTY', 2)

def on_subscribe(client, obj, mid, granted_qos):
    logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def mqtt_on_message(client, userdata, msg):
    logger.debug('received from queue:' + str(msg.payload))
    try:
        pwmctr.ChangeDutyCycle(float(msg.payload))
    except TypeError:
        pass

def runMqtt():
    client = mqtt.Client('Fan-daemon')
    client.enable_logger(logger)
    client.on_connect = mqtt_on_connect
    client.on_message = mqtt_on_message
    client.on_subscribe = on_subscribe
    client.connect(host=mqtt_host, port=mqtt_port, keepalive=60, bind_address="")
    client.loop_start()
    try:
        threading.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        GPIO.cleanup()
        client.loop_stop()
        client.disconnect()

def run():
    mqtt = threading.Thread(name='mqtt', target=runMqtt)
    mqtt.daemon = True
    mqtt.start()

    try:
        threading.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping server..")

if __name__ == '__main__':
        run()

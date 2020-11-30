package main

import (
        "time"
        "log"
	"strconv"
	"github.com/stianeikeland/go-rpio"
	"github.com/goiiot/libmqtt"
)

var MQTT_HOST = "pi1.iot"
var MQTT_TOPIC = "cmnd/fan/DUTY"

func main() {
        err := rpio.Open()
        if err != nil {
		panic("could not open gpio interface")
	}
        defer rpio.Close()

	//Config pins
        pin := rpio.Pin(13)
        pin.Mode(rpio.Pwm)
	// 25kHz
        pin.Freq(25000)

	client, err := libmqtt.NewClient(
		libmqtt.WithKeepalive(10, 1.2),
		libmqtt.WithAutoReconnect(true),
		libmqtt.WithBackoffStrategy(time.Second, 5*time.Second, 1.2),
		libmqtt.WithRouter(libmqtt.NewRegexRouter()),
		libmqtt.WithConnHandleFunc(connHandler),
	)

	if err != nil {
		panic("create mqtt client failed")
	}

	//Handle subscribed topics
	client.HandleTopic(".*", func(client libmqtt.Client, topic string, qos libmqtt.QosLevel, msg []byte) {
		dutyString := string(msg)
		log.Printf("[%v] message: %v", topic, dutyString)
		duty, err := strconv.ParseUint(dutyString, 10, 32)
		if err != nil {
			log.Println(err)
		}
		pin.DutyCycle(uint32(duty), 100)
	})

	err = client.ConnectServer(MQTT_HOST + ":1883")
	client.Wait()
}

func connHandler(client libmqtt.Client, server string, code byte, err error) {
	if err != nil {
		log.Printf("connect to server [%v] failed: %v", server, err)
		return
	}

	if code != libmqtt.CodeSuccess {
		log.Printf("connect to server [%v] failed with server code [%v]", server, code)
		return
	}

	log.Printf("connected to [%v] broker...", server)

	go func() {
		client.Subscribe([]*libmqtt.Topic{
			{Name: MQTT_TOPIC},
		}...)
	}()
}

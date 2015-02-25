from Pubnub import Pubnub

from iotconnector import iotbridge
from detector import Detector
import RPi.GPIO as GPIO
import time
import picamera
import sys, os
import json,httplib
import base64

sensor = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor, GPIO.IN, GPIO.PUD_DOWN)

previous_state = False
current_state = False

connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()


pi = iotbridge(publish_key = 'demo', subscribe_key = 'demo', uuid = 'PI')
cam = picamera.PiCamera()

startT = time.time()
count = 0

channel = 'iotchannel'
message = "hello from pi"
 
imgCount = 3

def callbackfn(m, n):
  print(m)

def is_person(image):
    det = Detector(image)
    faces = len(det.face())
    print "FACE: ", det.drawColors[det.drawn-1 % len(det.drawColors)], faces
    uppers = len(det.upper_body())
    print "UPPR: ", det.drawColors[det.drawn-1 % len(det.drawColors)], uppers
    fulls = len(det.full_body())
    print "FULL: ", det.drawColors[det.drawn-1 % len(det.drawColors)], fulls
    peds = len(det.pedestrian())
    print "PEDS: ", det.drawColors[det.drawn-1 % len(det.drawColors)], peds
    det.draw()
   
    return faces + uppers + fulls + peds
    # return len(det.face()) or len(det.full_body()) or len(det.upper_body()) # or len(det.pedestrian())

try:
    cam.start_preview()
    cam.preview_fullscreen = False
    cam.preview_window = (10,10, 320,240)
    while True:
        previous_state = current_state
        current_state = GPIO.input(sensor)
        if current_state != previous_state:
            new_state = "HIGH" if current_state else "LOW"
            if current_state:     # Motion is Detected
                cam.start_preview() # Comment in future
                cam.preview_fullscreen = False
                cam.preview_window = (10,10, 320,240)
                print('Motion Detected')
                curTime = (time.strftime("%I:%M:%S")) + "_%d.jpg"
                for i in range(imgCount):
                    cam.capture(curTime % i, resize=(320,240))
                    time.sleep(0.5)
                    print "Taking Photo %d" % i
                cam.stop_preview()
                for i in range(imgCount):
                    imgFile = curTime % i
                    if is_person(imgFile):
                        print "True"
                        with open(imgFile, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read())
                        connection.request('POST', '/1/classes/Selfie', json.dumps({
                            "fileData": encoded_string,
                            "fileName": imgFile,
                        }), {
                            "X-Parse-Application-Id": "S7cS6MQyMb7eMjWRWsC32owq9cDx0zyrM58MSevK",
                            "X-Parse-REST-API-Key": "RghYdl6Z2Pqpl2KjIqacZE6AoRn4csLM02e6j6ZH",
                            "Content-Type": "application/json"
                        })
                        try:
                            result = json.loads(connection.getresponse().read())
                        except:
                            print "Error Uploading."
                        pi.send(channel, imgFile)
                    else:   # Not a person
                        print "False"
                    os.remove(imgFile)  

except KeyboardInterrupt:
  cam.stop_preview()
  sys.exit(0)


import serial
import time
import math
import struct

class DM542t:
    # Establish a serial connection with the Arduino
    arduino = serial.Serial('COM3', 115200)  # replace 'COM3' with the port where your Arduino is connected
    MotorDelay = .0018
    def __init__(self) -> None:
        self.stepsTaken = 0
        self.stepsPerImage = 21
        self.imagesPerScene = 63

    def step(self, steps) -> None:
        if steps != 0:
            self.stepsTaken += steps*self.stepsPerImage
            # Pack integer as signed short
            packed_num = struct.pack('h', steps*self.stepsPerImage)
            # Write packed number to serial port
            self.arduino.write(packed_num)
            # self.arduino.write(str(steps*self.stepsPerImage).encode())
            # Wait for any data to arrive
            while True:
                if self.arduino.inWaiting() > 0:
                    data = self.arduino.read(self.arduino.inWaiting()).decode('utf-8')
                    print("Data received: ", data)
                    break
                # print("Waiting")
            # time.sleep(abs(steps*self.stepsPerImage*self.MotorDelay))


    def reset(self) -> None:
        # Pack integer as signed short
        packed_num = struct.pack('h', 0)
        # Write packed number to serial port
        self.arduino.write(packed_num)
        # self.arduino.write(str(0).encode())
        # Wait for any data to arrive
        while True:
            if self.arduino.inWaiting() > 0:
                data = self.arduino.read(self.arduino.inWaiting()).decode('utf-8')
                print("Data received: ", data)
                break
            # print("Waiting")
        # if self.stepsTaken == 0:
        #     time.sleep(abs(self.stepsPerImage*self.imagesPerScene*self.MotorDelay))
        # else:
        #     time.sleep(abs(self.stepsTaken*self.MotorDelay))
        self.stepsTaken = 0

    def getStepsPerScene(self) -> int:
        return self.stepsPerImage * self.imagesPerScene

    def setStepsPerImage(self, stepsPerImage) -> None:
        self.stepsPerImage = stepsPerImage

    def getStepsPerImage(self) -> int:
        return self.stepsPerImage

    def setImagesPerScene(self, imagesPerScene) -> None:
        self.imagesPerScene = imagesPerScene

    def getImagesPerScene(self) -> int:
        return self.imagesPerScene

    def getStepsTaken(self) -> int:
        return self.stepsTaken

    def setStart(self, startDegree) -> None:
        # .0004 is the movement of one step
        steps = math.floor(startDegree/.0004)
        temp = self.stepsPerImage
        self.stepsPerImage = 1
        self.step(steps)
        self.stepsPerImage = temp


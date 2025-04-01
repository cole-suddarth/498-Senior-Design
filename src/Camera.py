from vmbpy import *
from spectral import *
import numpy as np
import DM542t as Driver
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication

class Camera(QObject):
    progressChanged = pyqtSignal(int)
    cancelledChanged = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.cancelled = False
        self.imagesPerStep = 1

    def setIntegrationTime(self, integrationTime) -> None:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                features = cam.get_all_features()
                for feature in features:
                    if feature.get_name() == 'Gain':
                        feature.set(1)
                    if feature.get_name() == 'GainAuto':
                        feature.set(False)
                exposure_time = cam.ExposureTime
                curtime = exposure_time.get()
                inc = exposure_time.get_increment()

                if curtime < integrationTime:
                # Calculate the number of increments needed to reach the target integration time
                    num_increments = int((integrationTime - curtime) / inc) + 1
                    # Increase the exposure time by the calculated number of increments
                    exposure_time.set(curtime + (inc*num_increments))
                    print(exposure_time.get())
                else:
                # Calculate the number of decrements needed to reach the target integration time
                    num_decrements = int((curtime - integrationTime) / inc) + 1
                    # Decrease the exposure time by the calculated number of decrements
                    exposure_time.set(curtime - (inc*num_decrements))
                    print(exposure_time.get())
                '''
                exposure_time = cam.ExposureTime
                curtime = exposure_time.get()
                inc = exposure_time.get_increment()
                if curtime < integrationTime:
                    while curtime < integrationTime:
                        QCoreApplication.processEvents()
                        #print('new_time: '+str(curtime+inc))
                        exposure_time.set(curtime + inc)
                        curtime = exposure_time.get()
                else:
                    while curtime - inc > integrationTime:
                        QCoreApplication.processEvents()
                        #print('new_time: '+str(curtime-inc))
                        exposure_time.set(curtime - inc)
                        curtime = exposure_time.get()
                '''

    def getIntegrationTime(self) -> float:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.ExposureTime.get()

    def getIntegrationTimeRange(self) -> float:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.ExposureTime.get_range()

    def takeFrame(self) -> Frame:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.get_frame()

    def takeFrameNDArray(self) -> Frame:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.get_frame().as_numpy_ndarray()

    def takeFrameCV(self) -> Frame:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.get_frame().as_opencv_image()

    def scanNDArray(self, d) -> Frame:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                arr = []
                total_images = d.getImagesPerScene()
                for i in range(total_images):
                    a = []
                    for j in range(self.imagesPerStep):
                        QCoreApplication.processEvents()
                        if self.cancelled:
                            break
                        frame = cam.get_frame().as_numpy_ndarray()
                        a.append(frame)
                    if self.cancelled:
                        self.cancelledChanged.emit(True)
                        break
                    # Stack the arrays along a new axis
                    a = np.stack(a)
                    # Compute the average along the new axis
                    a = np.mean(a, axis=0)
                    # below is for SNR verification update on pixels not used
                    #b = np.stddev(a, axis=0)
                    #c = np.divide(a, b)
                    #mi = np.min(c) # this will have to be changed for unused pixels

                    a = np.floor(a)
                    arr.append(a)
                    d.step(1)
                    progress = int(((i + 1) / total_images) * 100)
                    self.progressChanged.emit(progress)
                arrs = np.concatenate(arr, axis=2)
                return arrs

    def cancelOperation(self):
        self.cancelled = True

    def getPixelFormats(self) -> tuple:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.get_pixel_formats()


    def getPixelFormat(self) -> tuple:
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                return cam.get_pixel_format()

    def setPixelFormat(self, format) -> None:
        format1 = format.lower()
        with VmbSystem.get_instance() as vmb:
            cams = vmb.get_all_cameras()
            with cams[0] as cam:
                if format1 == "mono8":
                    cam.set_pixel_format(PixelFormat.Mono8)
                elif format1 == "mono10":
                    cam.set_pixel_format(PixelFormat.Mono10)
                elif format1 == "mono10p":
                    cam.set_pixel_format(PixelFormat.Mono10p)
                elif format1 == "mono12":
                    cam.set_pixel_format(PixelFormat.Mono12)
                elif format1 == "mono12p":
                    cam.set_pixel_format(PixelFormat.Mono12p)
                else:
                    print("Unknown format: " + format1)
    def getImagesPerStep(self) -> int:
        return self.imagesPerStep

    def setImagesPerStep(self, imagesPerStep) -> None:
        self.imagesPerStep = imagesPerStep

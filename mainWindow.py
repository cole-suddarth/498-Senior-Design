'''
This is the basis for the GUI layout
'''

import sys
import re
import time
import math
import copy
import Camera
import numpy as np
import DM542t as Driver
from spectral import *
from PyQt5 import uic, QtCore
from PyQt5.QtCore import pyqtSignal, QEventLoop, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGraphicsView
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

'''
Class for updating progress on current image
Features a ui design with a progress bar and cancellation button
'''
class ImageProgress(QWidget):
    def __init__(self, c, parent=None):
        super().__init__(parent)
        uic.loadUi('imageProgress.ui', self)
        self.setWindowTitle("Image Progress")
        self.camera = c
        self.cancelButton.clicked.connect(self.cancel)

    '''
    Use Case: Called when the cancelButton is clicked
    Purpose: Calls the driver to cancel operation
        * note that user only has to click cancel once wait perhaps a second
        * and then it will communicate with the image info window a cancel
    '''
    def cancel(self):
        self.camera.cancelOperation()

    '''
    When this is called, the progress bar is updated based on passed int progress value
    If the progress is greater than or equal to 100 then we close the window
    '''
    @QtCore.pyqtSlot(int)
    def updateProgressBar(self, progress):
        print(progress)
        self.progressBar.setValue(progress)
        if progress >= 100:
            self.close()

'''
Window to put on enclosure cap for dark subtract image
'''
class DarkWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('darkImageWindow.ui', self)
        self.setWindowTitle('Enclosure Cap Close')

'''
Class is for receiving user input about the image process, including the integration
time, FOR range, fileName, calibration use
'''
class ImageInfo(QWidget):
    dataCollected = pyqtSignal(object, bool, bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('imageInfo.ui', self)
        self.setWindowTitle("Imaging Spectrometer Image Info")

        self.setPlaceholders()
        self.validFOR = False
        self.validTime = False
        self.validName = False

        # when each user input is finished editing, verify its acceptable input
        self.minFORLineEdit.editingFinished.connect(self.updateStepCount)
        self.maxFORLineEdit.editingFinished.connect(self.updateStepCount)
        self.integrationTimeLineEdit.editingFinished.connect(self.validateIntegrationTime)
        self.fileNameLineEdit.editingFinished.connect(self.validateFileName)

        self.takeImageButton.clicked.connect(lambda:
            self.updateImageInfo())

    '''
    Use Case: Called when min and maxFOR are finished editing(updated)
    Purpose:
        Ensures a valid FOR call and update the steps taken for such a FOR
    Successful Input:
        minFOR can be converted to a float and is between -0.25 and 0.0
        maxFOR can be converted to a float and is between 0.0 and 0.25
        Calculates the number of steps that this FOR can take
    '''
    def updateStepCount(self):
        try:
            self.minFOR = float(self.minFORLineEdit.text())
            maxFOR = float(self.maxFORLineEdit.text())
            # check min in requirments, else set the text to empty string
            if self.minFOR < -.25 or self.minFOR > 0.0:
                self.minFORLineEdit.setText('')
                self.validFOR = False
                return
            # check max in requirements, else set that text to empty string
            elif maxFOR > .25 or maxFOR < 0.0:
                self.maxFORLineEdit.setText('')
                self.validFOR = False
                return
            self.validFOR = True

            # calculates the total number of steps for this FOR and displays to user
            stepSize = 0.5/63 # update to reflect accurate step size
            total = maxFOR - self.minFOR
            self.numSteps = math.floor(total / stepSize)
            updatedString = "Number of Steps: " + str(self.numSteps)
            #print(updatedString)
            self.stepsLabel.setText(updatedString)
        # if invalid float value, not a validFOR and return
        except ValueError:
            self.validFOR = False
            return

    '''
    Use Case: Called when integration time text edit is finished editing(updated)
    Purpose:
        Validate the integration time based on the camera requirements between 30 and
        1e7 microseconds
    Valid Input:
        Integration input can be converted to an integer and is between 30-1e7
        If valid set validTime to true and integrationTime to the valid time
    '''
    def validateIntegrationTime(self):
        try:
            integration = int(self.integrationTimeLineEdit.text())
            print(integration)
            # check integration time falls in range, else set to empty line edit
            if integration < 30 or integration > 10000000:
                self.integrationTimeLineEdit.setText('')
                self.validTime = False
            else:
                self.validTime = True
                self.integrationTime = integration
        except ValueError:
            self.validTime = False

    '''
    Use Case: Called when the fileName input text edit is finished editing(updated)
    Purpose/Valid Input:
        Validate that the filename is some valid value that ends in .npy
    '''
    def validateFileName(self):
        # regex to match the expression to a filename that ends in .npy
        regex = r'^.+\.npy$'
        regex2 = r'^.+\.cv$'
        if bool(re.match(regex, self.fileNameLineEdit.text())):
            self.fileName = self.fileNameLineEdit.text()
            self.validName = True
        elif bool(re.match(regex2, self.fileNameLineEdit.text())):
            self.fileName = self.fileNameLineEdit.text()
            self.validName = True
        else:
            self.validName = False
            self.fileNameLineEdit.setText('')

    '''
    Set the placeholders for everything, as expected value ranges
    Resets all validities and sets all inputs to original states
    '''
    def setPlaceholders(self):
        self.integrationTimeLineEdit.setPlaceholderText("30 - 10000000")
        self.minFORLineEdit.setPlaceholderText("-0.25 to 0.0")
        self.maxFORLineEdit.setPlaceholderText("0.0 to 0.25")
        self.fileNameLineEdit.setPlaceholderText("exampleName.npy")

        self.integrationTimeLineEdit.setText('')
        self.minFORLineEdit.setText('')
        self.maxFORLineEdit.setText('')
        self.fileNameLineEdit.setText('')
        self.stepsLabel.setText('Number of Steps: 63')

        self.resolutionSpinBox.setValue(1)
        self.imageCountSpinBox.setValue(1)

        self.calibrationCheckBox.setChecked(False)
        self.sceneCheckBox.setChecked(False)

        self.validFOR = False
        self.validName = False
        self.validTime = False

    '''
    imageEverySteps -> integer between 1 and 65
    imageCountStop -> integer between 1 and 99
    labCalibration -> boolean value
    sceneCalibration -> boolean value
    This function updates all the value for the stepper and determines if
    this is for calibration
    '''
    def updateImageInfo(self):
        # ensures user inputs are valid
        if not self.validFOR or not self.validTime or not self.validName:
            return

        #disable take image button
        self.takeImageButton.setEnabled(False)

        self.imageEverySteps = self.resolutionSpinBox.value()
        # ensures that there is at least one image taken
        if self.imageEverySteps > self.numSteps:
            return
        self.imageCountStop = self.imageCountSpinBox.value()

        self.labCalibration = self.calibrationCheckBox.isChecked()
        self.sceneCalibration = self.sceneCheckBox.isChecked()

        # create driver and camera
        start=time.time()
        self.driver = Driver.DM542t()
        self.driver.reset()
        #return
        self.driver.setStepsPerImage(self.imageEverySteps*21)
        self.driver.setImagesPerScene(math.floor(self.numSteps/self.imageEverySteps))
        #self.driver.setStart(self.minFOR)
        self.camera = Camera.Camera()
        print('here')
        self.camera.setIntegrationTime(self.integrationTime)
        print('here2')
        self.camera.setPixelFormat('mono12')

        # create and displays the progress window
        self.progressWindow = ImageProgress(self.camera)
        self.progressWindow.show()

        # makes connections for when scanning scene to cancel, update and finish
        self.camera.cancelledChanged.connect(self.cancellation)
        self.camera.progressChanged.connect(self.progressWindow.updateProgressBar)

        # take images of the scene
        self.cancelled = False
        self.img = self.camera.scanNDArray(self.driver)
        #a = []
        #for i in range(5):
        #    frame = self.camera.takeFrameNDArray()
        #    a.append(frame)
        # Stack the arrays along a new axis
        #a = np.stack(a)
        # Compute the average along the new axis
        #a = np.mean(a, axis=0)
        #self.img = np.floor(a)
        #self.img = self.camera.takeFrameCV()
        #np.set_printoptions(precision=7)
        end=time.time()
        print(f"Time:{end-start}")

        self.progressWindow.close()
        if not self.cancelled and not self.labCalibration:
            self.darkSub = DarkWindow()
            self.darkSub.show()
            self.darkSub.capOnButton.clicked.connect(lambda: self.darkImages())
            self.loop = QEventLoop()
            self.loop.exec_()
        elif not self.cancelled:
            self.takeImageButton.setEnabled(True)
            self.dataCollected.emit(self.img, self.labCalibration, self.sceneCalibration, self.fileName)

    '''
    Use Case: called when total image has not been cancelled to get the dark subtract
    for current heat and light leaks at that current integration time
    '''
    def darkImages(self):
        self.darkSub.capOnButton.setEnabled(False)
        self.driver.setStepsPerImage(21)
        self.driver.setImagesPerScene(1)
        self.camera.setImagesPerStep(10)
        self.dark = self.camera.scanNDArray(self.driver)
        self.darkSub.close()
        self.takeImageButton.setEnabled(True)
        self.dataCollected.emit(self.img, self.labCalibration, self.sceneCalibration, self.fileName)
        self.loop.quit()
    '''
    Use Case: Called when camera class emits cancellation signal
    Purpose:
        Resets the driver to inital state at -0.25 degrees
        Closes the progress window
    '''
    def cancellation(self):
        self.driver.reset()
        self.progressWindow.close()
        self.cancelled = True
        self.takeImageButton.setEnabled(True)


    '''
    Use Case: Called when camera class is about to return arr
    Purpose:
        Check if there was a cancellation or it finished all the way through
        If finished all the way through return image info to mainWindow
        If cancelled stays open and resets form
    '''
    def checkFinished(self):
        if not self.camera.cancelled:
            self.dataCollected.emit(self.img)#, self.labCalibration, self.sceneCalibration, self.fileName)
        else:
            self.setPlaceholders()

'''
Window to show that processing and classification is happening
'''
class ProcessingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('processingWindow.ui')
        self.setWindowTitle('Processing Occurring')

'''
Class to display the graphic and spectra on the GUI
'''
class ImageCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.axes.axis('off')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def plot_image(self, image, mode='image', cmap='gray'):
        self.axes.clear()  # Clear the previous plot
        if mode == 'image':
            self.axes.imshow(image, cmap)
        elif mode == 'spectrum':
            wavelengths = np.arange(450, 961, 15)
            #data = np.array([1]) # need to change to get the spectra of the camoflauged pixels
            #self.axes.plot(wavelengths, data)
        self.draw()

'''
Main Control Window: to take user input to start taking images, load or save images,
    also allows us to manipulate data to show varying spectra
'''
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        uic.loadUi('mainWindow.ui', self)
        self.setWindowTitle("Imaging Spectrometer Main Window")

        self.takePhotoButton.clicked.connect(lambda: self.imageInfoControl())

        # updates the image for the wavelength ranges
        self.redButton.clicked.connect(lambda: self.updateImageOnGUI(self.image_data, 'Reds'))
        self.greenButton.clicked.connect(lambda: self.updateImageOnGUI(self.image_data, 'Greens'))
        self.blueButton.clicked.connect(lambda: self.updateImageOnGUI(self.image_data, 'Blues'))
        self.irButton.clicked.connect(lambda: self.updateImageOnGUI(self.image_data, 'ir'))
        self.overlayClassesButton.clicked.connect(lambda: self.updateImageOnGUI(self.image_data, 'overlay'))
        # saves and loads image
        self.saveImageButton.clicked.connect(lambda: print('save image clicked'))
        self.loadImageButton.clicked.connect(lambda: print('load image clicked'))

    '''
    Use Case: Called when other window opens to disable user from doing anything on this window
    '''
    def disable_buttons(self):
        self.takePhotoButton.setEnabled(False)
        self.redButton.setEnabled(False)
        self.greenButton.setEnabled(False)
        self.blueButton.setEnabled(False)
        self.irButton.setEnabled(False)
        self.overlayClassesButton.setEnabled(False)
        self.saveImageButton.setEnabled(False)
        self.loadImageButton.setEnabled(False)

    '''
    Use Case: Called when other windows close to enable user to use window
    '''
    def enable_buttons(self):
        self.takePhotoButton.setEnabled(True)
        self.redButton.setEnabled(True)
        self.greenButton.setEnabled(True)
        self.blueButton.setEnabled(True)
        self.irButton.setEnabled(True)
        self.overlayClassesButton.setEnabled(True)
        self.saveImageButton.setEnabled(True)
        self.loadImageButton.setEnabled(True)

    '''
    Use Case: Called when the user goes to take an image, opening up window to take image
    '''
    def imageInfoControl(self):
        self.imageWindow = ImageInfo()
        self.disable_buttons()
        self.imageWindow.dataCollected.connect(self.initialProcess)
        self.imageWindow.show()

    '''
    Use Case: Called when the picture has been fully taken, not cancelled and recieves
    an object data which is the information collected from the camoflauge, and then
    booleans for lab and scene calibration, as well as a string for fileName save
    '''
    @QtCore.pyqtSlot(object, bool, bool, str)
    def initialProcess(self, data, labCalibration, sceneCalibration, fileName):
        # deep copy the image data just incase garbage collection
        self.image_data = copy.deepcopy(data)
        self.imageWindow.close()
        self.enable_buttons()
        self.fileName = fileName

        # lab calibration just show and save image for later processing
        if labCalibration:
            print(self.image_data.shape)
            np.save(fileName, data)
            result = self.image_data
            self.updateImageOnGUI(result, 'gray')
            #imshow(self.image_data)
        elif sceneCalibration:
            # scene run the calibration lookup tables before classification
            # then run a variety of classifications to determine what is best
            # processing file call cube.sceneCalibration()
            # incomplete
            pass
        else:
            # run the calibration lookup tables and then do classification
            # determine camoflauge update the image on GUI
            self.processingWindow = ProcessingWindow()
            self.processingWindow.show()
            self.processingWindow.close()
            print(self.image_data.shape)
            imshow(self.image_data)

            # Define the ranges for the third axis
            ranges = [(0, 182), (182, 388), (388, 560), (560, 728)]
            # Initialize a list to store the averaged arrays
            averaged_arrays = []
            # Loop over the ranges
            for start, end in ranges:
                # Extract the subarray for the current range
                subarray = self.image_data[:, :, start:end]
                # Take the average over the third dimension
                averaged_subarray = np.mean(subarray, axis=2)
                # Append the averaged subarray to the list
                averaged_arrays.append(averaged_subarray)
            # Stack the averaged arrays along the third dimension
            result = np.stack(averaged_arrays, axis=2)
            self.updateImageOnGUI(result, 'color')
            np.save(fileName, result)

    '''
    Use Cases: Called when the image is first processed to display image with marked pixels
        that are part of the camoflauged class
        Called when any color button is clicked to update image with specific classes
    '''
    def updateImageOnGUI(self, img, cmap):
        self.imageCanvas = ImageCanvas(self.centralwidget)
        layout = self.leftVerticalLayout
        layout.itemAt(0).widget().setParent(None)
        layout.insertWidget(0, self.imageCanvas, stretch=3)
        if cmap == 'color':
            self.imageCanvas.plot_image(img)
        else:
            self.imageCanvas.plot_image(img, cmap)


    '''
    Use Cases: Called when the image is first processed to display camoflauge pixels spectra
        Called when any color button is clicked to update the spectra associate with classes
    '''
    def updateGraphView(self, data):
        '''
        likely need to change this so that we graph spectral data of the camoflauge
        may need to change the imagecanvas class possibly
        '''
        self.imageCanvas = ImageCanvas(self.centralwidget)
        layout = self.rightVerticalLayout
        layout.itemAt(0).widget.setParent(None)
        layout.insertWidget(0, self.imageCanvas, stretch=3)
        self.imageCanvas.plot_image(data, mode='spectrum')

    '''
    Use Case: Called when save image is clicked, saving the processed image, which has been
    mapped from calibration
    '''
    def saveImageProcess(self):
        # replace self.img with whatever the actual name of the final processed image is
        np.save(self.fileName, self.img)

    '''
    Use Case: Called when load image is clicked, opening a new window asking for fileName
    Trys to open if it can then does classification and whatnot
    If can not open then returns and does nothing
    '''
    def loadImageProcess(self):
        # create a new window to ask for filename, open and
        # run processing, don't have to do mappings here, just do classification
        # self.final = np.load(fileName)
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
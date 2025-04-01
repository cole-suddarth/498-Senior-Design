'''
This is the basis for handling the information with spectral etc
'''

from spectral import *

class HyperSpectralCube():
    def __init__(self, parent=None, img):
        self.img = img

    def apply_spectral_mapping():
        try:
            file = open('spectralCal.npy')
            '''
            apply the mapping such that we get something where
            each pixel row gets the spectralCal application,
            such that one single frame gets each row a equation
            so we have an input of [544, frames, 764]
            apply for each frame in frames
            '''
        except FileNotFoundError:
            return

    def apply_radiometric_mapping():
        try:
            file = open('initialDarks.npy')
            file = open('radioCal.npy')
            '''
            apply the mapping such that we get something where each pixel
            value read is converted based on radio and then has irradiance

            (value-dark)*R = mW
            6um square then you have an irradiance of 681 W/mm^2,
            and if you have an F/# of 5 you have a radiance of 21663 W/mm^2/sr.
            (sr = pi/(4*(F/#)^2))
            so we have an input of [544, frames, 764]
            apply for each frame in frames
            '''
        except FileNotFoundError:
            return

    def scene_calibration():
        self.up = apply_radiometric_mapping()
        self.final = apply_spectral_mapping()
        '''
        I want this final to be a [y_pixel, frames, 450-950 irradiance values]
        '''
        for i in range (10):
            (m,c) = kmeans(self.final, i, 30)
            # need to do the thing where I graph the things to determine which
            # one works

    def classify():
        classCount = 20 # update classCount
        (m, c) = kmeans(self.img, classCount, 30)
        # where classes is an array of each classes irradiance measurements
        self.classes = c
        self.m = m

        return

    def getClasses():
        return self.classes

    def getRegularImage():
        return self.final

    def getRedImage():
        return

    def getBlueImage():
        return

    def getGreenImage():
        return

    def getIRImage():
        return

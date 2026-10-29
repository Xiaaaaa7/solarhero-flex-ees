import pandas as pd
import numpy as np
import os
from datetime import timedelta

local_path = os.path.dirname(__file__)

class ColdAppliances():

    def __init__(self, annualConsumption, numRefrigerators, numFreezers, refrigeratorPowerRating=200, freezerPowerRating=50):
        self.annualConsumption = annualConsumption
        self.numRefrigerators = max(1,numRefrigerators)
        self.numFreezers = numFreezers
        self.refrigeratorPowerRating = refrigeratorPowerRating
        self.freezerPowerRating = freezerPowerRating
        self.expectedOpHours = None
        self.probabilityOn = None

        # output
        self.P = None
        self.W = None

    def run(self,timeStamps):

        # update dependent values
        self.expectedOpHours = self.annualConsumption / (self.refrigeratorPowerRating * self.numRefrigerators + self.freezerPowerRating * self.numFreezers)
        self.probabilityOn = self.expectedOpHours / 8760.0 # probability of appliance being on at anytime
        
        # get original timeResolution
        timeRes = (timeStamps[1] - timeStamps[0]).seconds // 60 % 60
        
        # output
        self.P = pd.Series(index=timeStamps, dtype=float)

        # resample so everything samples are in intervals of 10 minutes
        if timeRes < 10:
            # self.P = self.P.resample(timedelta(minutes=10)).pad()
            self.P = self.P.resample(timedelta(minutes=10)).interpolate()
        
        # simulate refrigerators
        self.P[:] = np.sum((np.random.uniform(size=(self.numRefrigerators, len(self.P))) < self.probabilityOn) * self.refrigeratorPowerRating,axis=0)
        
        # separate freezers
        if self.numFreezers > 0:
            self.P[:] += np.sum((np.random.uniform(size=(self.numFreezers,len(self.P))) < self.probabilityOn) * self.freezerPowerRating, axis=0)

        # resample
        if timeRes < 10:
            self.P = self.P._append(pd.Series(name=timeStamps[-1],dtype=float))
            # self.P = self.P.resample(timedelta(minutes=timeRes)).pad()
            self.P = self.P.resample(timedelta(minutes=timeRes)).ffill()
            self.P = self.P.pad()

        # get work
        self.W = self.P * float(timeRes) / 60.


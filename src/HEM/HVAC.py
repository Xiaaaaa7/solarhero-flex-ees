import pandas as pd
import numpy as np
import os
import random

local_path = os.path.dirname(__file__)

rng = np.random.default_rng()

# from Lu 2012
class HVAC:

    #defaultHeaterPowerRating = 6000
    #defaultAcPowerRating = 4500
    #defaultHeaterQ = 400
    #defaultAcQ = -150
    
    #defaultHeaterPowerRating = random.uniform(5800, 6200)
    #defaultHeaterPowerRating = random.uniform(3200, 3600)
    defaultHeaterPowerRating = random.uniform(2800, 3200)
    defaultAcPowerRating = random.uniform(4300, 4700)
    defaultHeaterQ = random.uniform(350, 450)
    defaultAcQ = random.uniform(-140, -160)

    class TCL:
        def __init__(self,powerRating,Q):
            self.powerRating = powerRating # (W)
            self.Q = Q # equivalent heat rate (W)

    def __init__(self, electricHeater, electricAirConditioner, setPoint=21, deadband=2): 
        self.electricHeater = electricHeater
        self.electricAirConditioner = electricAirConditioner
        self.heater = HVAC.TCL(HVAC.defaultHeaterPowerRating*electricHeater, HVAC.defaultHeaterQ)
        self.ac = HVAC.TCL(HVAC.defaultAcPowerRating*electricAirConditioner,HVAC.defaultAcQ)
        self.setPoint = random.uniform(20, 25) # celsius
        self.deadband = random.uniform(1.5, 4) # celsius

        #outputs
        self.T = None
        self.P = None
        self.W = None

    def run(self, ambientTemperature, occupancy):

        # adjust values based on household
        self.heater.powerRating = HVAC.defaultHeaterPowerRating * self.electricHeater + 400
        self.ac.powerRating = HVAC.defaultAcPowerRating * self.electricAirConditioner
        
        self.R = .18
        self.C = 7200/self.R

        # get time resolution
        timeStamps = ambientTemperature.index
        timeRes = (timeStamps[1] - timeStamps[0]).seconds // 60 % 60
        
        # add empty hour to avoid checks in iteration
        ambientTemperature = ambientTemperature.values
        occupancy = occupancy.values > 0

        # outputs
        T = np.zeros(len(timeStamps))
        self.ac.P = np.zeros(ambientTemperature.shape)
        self.heater.P = np.zeros(ambientTemperature.shape)
        acOn = 0
        heaterOn = 0

        # set inital temperature
        T[0] = self.setPoint+random.uniform(-1.5, 1.5)
        
        # get boundaries when occupants are home
        
        for t in range(len(timeStamps)-1):
            
            
            if occupancy[t]: 
                # heating 
                heaterOn = np.where(T[t] < self.setPoint-self.deadband, True, heaterOn)
                heaterOn = np.where(T[t] > self.setPoint, False, heaterOn)

                # cooling_season 
                acOn = np.where(T[t] > self.setPoint+self.deadband, True, acOn)
                acOn = np.where(T[t] < self.setPoint, False, acOn)
            # if no one is home, change set point by 5 degrees
            else:
            ### Changed 01/16/2022 for validation
                heaterOn = np.where(T[t] < self.setPoint-self.deadband, True, heaterOn)
                heaterOn = np.where(T[t] > self.setPoint, False, heaterOn)

                # cooling_season 
                acOn = np.where(T[t] > self.setPoint+self.deadband, True, acOn)
                acOn = np.where(T[t] < self.setPoint, False, acOn)
                #acOn = False
                #heaterOn = False
        
            # get power consumption
            self.ac.P[t] = acOn * self.ac.powerRating
            self.heater.P[t] = heaterOn * self.heater.powerRating
            
            # update temperature
            exponential = np.exp(-timeRes*60.0/(self.R*self.C))
            T[t+1] = ambientTemperature[t+1] + (heaterOn*self.heater.Q + acOn*self.ac.Q)*self.R - (ambientTemperature[t+1] + (heaterOn*self.heater.Q + acOn*self.ac.Q)*self.R - T[t])*exponential 
        
        # remove empty hour
        self.T = pd.Series(T,timeStamps)
        self.ac.P = pd.Series(self.ac.P,timeStamps)
        self.heater.P = pd.Series(self.heater.P,timeStamps)
        self.P = self.ac.P + self.heater.P
        self.ac.W = self.ac.P * timeRes / 60.0
        self.heater.W = self.heater.P * timeRes / 60.0
        self.W = self.P * timeRes / 60.0

        return
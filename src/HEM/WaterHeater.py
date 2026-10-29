import numpy as np
import pandas as pd
import math
import random

rng = np.random.default_rng()

# volume = 190 l
# equivalent thermal mass =  794960 J/C
# thermal resistance of tank insulation = 2.657 m2-s-C/J
# 
# find surface area from volume:
# ASSUME
# - cylindrical shape
# - height = 4*radius
# USE
# - V = pi*r^2*h 
# - SA =2*pi*r*(r+h)
# SOLVE
# - r = (V/(4pi))^1/3
# - SA = 10*pi*r^2

class WaterHeater():
    # Values
    radiusHeightRatio = 4
    #powerRating = 3000
    powerRating = random.uniform(2800, 3200)
    #specificHeat = 4186 # J/kg C
    specificHeat =random.uniform(4150, 4222)

    # consumption profiles (liters/minute)
    consumptionProfile = [np.array([]), # away
                          np.array([]), # sleeping
                          np.array([8]*8), # grooming (64 liters)
                          np.array([.1]*10), # cooking (1 liters)
                          np.array([4]*5), # dishwashing (20 liters)
                          np.array([1.2]*5), # cleaning (6 liters)
                          np.array([2.5]*30), # laundry (75 liters)
                          np.array([]), # leisure
                          np.array([])] # other
                        
    def __init__(self,electricWaterHeater,volume,R=1.2, incomingTemperature=10, setPoint=55, deadband=4):
        self.electricWaterHeater = electricWaterHeater
        self.volume = volume
        self.R = R
        self.incomingTemperature = random.uniform(8, 12)
        self.setPoint = random.uniform(50, 60) 
        self.deadband = random.uniform(2, 6)
    
    def run(self,ambientTemperature,activity):
        
        # get time stamps
        timeStamps = ambientTemperature.index
        timeRes = (timeStamps[1]-timeStamps[0]).seconds//60%60

        # if gas water heater return
        if not self.electricWaterHeater:
            self.D = pd.Series(0,timeStamps)
            self.T = pd.Series(0,timeStamps)
            self.P = pd.Series(0,timeStamps)
            self.W = pd.Series(0,timeStamps)
            return

        # convert activity to water demand
        activity = (activity > 0).values
        
        # values
        r = (self.volume/(1000*WaterHeater.radiusHeightRatio*math.pi))**(1/3)
        SA = 2*math.pi*(WaterHeater.radiusHeightRatio+1)*r**2
        C = self.volume*WaterHeater.specificHeat
        G = SA / self.R
        
        upperBound = self.setPoint
        lowerBound = self.setPoint - self.deadband

        # output
        Q = 0
        D = np.zeros(len(timeStamps)) # water demand l/s
        T = np.zeros(len(timeStamps)) # water temperature
        P = np.zeros(len(timeStamps)) # power consumption

        # initial condition (full)
        T[0] = self.setPoint+random.uniform(-3, 3)

        for t in range(len(timeStamps)-1):

            # update water demand based on activity
            #for a in [2,3,4,5,6]:
            for a in [4,6]:
                #if activity[t,a] and not activity[t-1,a] and rng.uniform() < .8:
                if activity[t,a] and not activity[t-1,a] and rng.uniform() < .2: #Double check, changed from 0.3 to 0.2 on Jan 22, error is 13% when 0.3
                    duration = min(len(WaterHeater.consumptionProfile[a]),len(timeStamps)-t)
                    D[t:t+duration] += WaterHeater.consumptionProfile[a][:duration]/60 # liters per minute -> liters per second

            B = D[t] * WaterHeater.specificHeat
            Rprime = 1./(G+B)

            # update heater state
            Q = np.where(T[t] > upperBound,0,Q)
            Q = np.where(T[t] < lowerBound,WaterHeater.powerRating,Q)
            
            # update power
            P[t] = Q

            # update temperature
            exponential = np.exp(-60*timeRes/(Rprime*C))
            T[t+1] = T[t]*exponential + (G*ambientTemperature[t] + B*self.incomingTemperature + Q)*Rprime*(1-exponential)

        # repopulate
        self.D = pd.Series(D,timeStamps)*60
        self.T = pd.Series(T,timeStamps)
        self.P = pd.Series(P,timeStamps)
        self.W = self.P * timeRes / 60.
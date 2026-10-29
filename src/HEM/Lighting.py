import numpy as np
import pandas as pd
import os

local_path = os.path.dirname(__file__)

rng = np.random.default_rng()

# Adapted from I. Richardson, et al., "Domestic Lighting: A high-resolution energy demand model"
class Lighting():

    # threshold
    threshold = 60
    alpha = .1 # for smoothing irradiance
    calibrationScalar = .008

    # ratings
    ledBulbWattage = np.array([9,12,16])
    cflBulbWattage = np.array([15,20,26])
    incBulbWattage = np.array([60,75,100])
    
    # effective occupancy
    effectiveOccupancyValues = np.array([0.0, 1.0, 1.5, 1.7, 2.0, 2.1]+[2.1 for n in range(14)]) # direct indexing up to 20 household members

    # duration probability
    durationProb = np.concatenate(([.1],.1/(np.arange(1,250)**.9)))
    durationProb = durationProb / np.sum(durationProb) # normalize

    def __init__(self, numLedBulbs, numIncBulbs, numCflBulbs, defaultAppliances=True):
        # inputs 
        self.numLedBulbs = numLedBulbs
        self.numIncBulbs = numIncBulbs
        self.numCflBulbs = numCflBulbs
        self.defaultAppliances = defaultAppliances

        # outputs 
        self.P = None
        self.W = None
        
    def run(self,irradiance,activity):
        
        # get variables
        numBulbs = self.numLedBulbs + self.numIncBulbs + self.numCflBulbs
        timeStamps = irradiance.index
        timeRes = (timeStamps[1]-timeStamps[0]).seconds//60%60

        # smooth irradiance data
        irradiance = irradiance.ewm(alpha=Lighting.alpha).mean().values

        # get effective occupancy
        occupancy = activity.T[2:].sum().values
        effectiveOccupancy = Lighting.effectiveOccupancyValues[occupancy]

        # get number of lights, their power ratings, and effective weighting
        ledBulbWattages = Lighting.ledBulbWattage[np.arange(self.numLedBulbs)%3]
        incBulbWattages = Lighting.incBulbWattage[np.arange(self.numIncBulbs)%3]
        cflBulbWattages = Lighting.cflBulbWattage[np.arange(self.numCflBulbs)%3]

        # assign wattage and relative use
        bulbWattage = np.concatenate((ledBulbWattages,incBulbWattages,cflBulbWattages))

        if self.defaultAppliances:
            bulbRelativeUse = -np.log(np.linspace(.01,10,numBulbs)%.99) # distribute deterministically
        else:
            bulbRelativeUse = -np.log(rng.uniform(numBulbs))
        
        # new arrays
        bulbOn = np.zeros((len(timeStamps),numBulbs))
        probOn = bulbRelativeUse*Lighting.calibrationScalar
        P = np.zeros(len(timeStamps))

        for t,ts in enumerate(timeStamps[:]):
            # only turn on when the threshold is met or 
            if (irradiance[t] > Lighting.threshold and rng.uniform() > .05) or occupancy[t] == 0:
                bulbOn[t] = 0
            else:
                effProbOn = probOn * effectiveOccupancy[t]

                # sample turn on
                turnOn = np.logical_and(rng.uniform(size=numBulbs) < effProbOn, np.logical_not(bulbOn[t]))
                durations = turnOn*rng.choice(250,size=numBulbs,p=Lighting.durationProb)
                
                # switch on bulbs
                maxDuration = min(bulbOn.shape[0]-t,250) # how many minutes ahead to plan
                turnOnDuration = np.tile(np.arange(maxDuration),(numBulbs,1)).T<durations

                bulbOn[t:t+maxDuration] = np.where(turnOnDuration,1,bulbOn[t:t+maxDuration])

            P[t] = np.sum(bulbOn[t]*bulbWattage)
        
        self.P = pd.Series(P,timeStamps)
        self.W = self.P * timeRes / 60
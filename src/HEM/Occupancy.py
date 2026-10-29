import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

local_path = os.path.dirname(__file__)

rng = np.random.default_rng()

class Occupant():
    def __init__(self,age=np.nan,occupationStatus=np.nan,occupationCategory=np.nan,parentalStatus=np.nan):
        self.age = age 
        self.occupationStatus = occupationStatus
        self.occupationCategory = occupationCategory
        self.parentalStatus = parentalStatus
        self.universal = np.all(np.isnan([age, occupationStatus, occupationCategory, parentalStatus]))

class Occupancy():
    numActivities = 9
    respondents = pd.read_csv(os.path.join(local_path,'..','..','processed-data','cps','processed-cps-atus-respondents-2023.csv'))#
    activityData = pd.read_csv(os.path.join(local_path,'..','..','processed-data','atus','processed-atus-act-2023-10-min-res.csv'),index_col=0)#
    
    # universal respondent probabilities
    
    universalInitialProb = np.load(os.path.join(local_path,'..','..','processed-data','occupancy','universalInitialProb.npy'))
    universalWeekdayProb = np.load(os.path.join(local_path,'..','..','processed-data','occupancy','universalWeekdayProb.npy'))
    universalWeekendProb = np.load(os.path.join(local_path,'..','..','processed-data','occupancy','universalWeekendProb.npy'))
    
    def __init__(self,occupants):
        self.occupants = occupants
        
    def run(self, timeStamps):
        self.timeStamps = timeStamps
        self.timeRes = (self.timeStamps[1]-self.timeStamps[0]).seconds // 60 % 60
        self.occupancy = pd.Series(0,index=self.timeStamps,dtype=int)
        self.activity = pd.DataFrame(0,index=self.timeStamps,columns=range(Occupancy.numActivities),dtype=int)
    
        # get probabilities and sample
        for (n, occupant) in enumerate(self.occupants):
            self.sample(occupant)    
        
    @staticmethod
    def getCaseIds(age,occupationStatus,occupationCategory,parentalStatus,weekday=True): # return caseIds and their relative weights
            # get classification
            subset = Occupancy.respondents[Occupancy.respondents['weekday'] == weekday]

            if not np.isnan(age):
                subset = subset[subset['age'] == age]
            if not np.isnan(occupationStatus):
                subset = subset[subset['occupation status'] == occupationStatus]
            if not np.isnan(occupationCategory):
                subset = subset[subset['occupation category'] == occupationCategory]
            if not np.isnan(parentalStatus):
                subset = subset[subset['parental status'] == parentalStatus]
                
            # sample size too small
            if len(subset) < 100:
                if not np.isnan(occupationCategory):
                    return Occupancy.getCaseIds(age,occupationStatus,np.nan,parentalStatus,weekday)
                elif not np.isnan(parentalStatus):
                    return Occupancy.getCaseIds(age,occupationStatus,np.nan,np.nan,weekday)
                elif not np.isnan(age):
                    return Occupancy.getCaseIds(np.nan,occupationStatus,np.nan,np.nan,weekday)
                else:
                    return Occupancy.getCaseIds(np.nan,np.nan,np.nan,np.nan,weekday)

            return subset['case id'].values, subset['representative weight'].values
    
    @staticmethod
    def getMCMCProbabilities(activityData,weights,ignore_weights=False,universal=False):

            if ignore_weights:
                weights = np.ones(activityData.shape[1]) 

            totalWeight = np.sum(weights)

            # get probability matrix
            prob = np.zeros((24,Occupancy.numActivities,Occupancy.numActivities)) #hour, start activity, end activity
            for h in range(24):
                for startActivity in range(Occupancy.numActivities):
                    for endActivity in range(Occupancy.numActivities):
                        weightedStart = 0
                        weightedEnd = 0
                        weightedTransitioned = 0
                        # iterate through 10 minute time steps
                        for m in range(6):
                            # get time step
                            t = h*6+m
                            # get subsets
                            startSubset = activityData[t-1] == startActivity
                            endSubset = activityData[t] == endActivity
                            transitionedSubset = np.logical_and(startSubset,endSubset)
                            # add to counts
                            weightedStart += np.sum(startSubset*weights)
                            weightedEnd += np.sum(endSubset*weights)
                            weightedTransitioned += np.sum(transitionedSubset*weights)
                            
                        prob[h,startActivity,endActivity] = -1 if weightedStart == 0 else weightedTransitioned/weightedStart
                        
                    prob[h,startActivity] = prob[h,startActivity]/np.sum(prob[h,startActivity])

            return prob

    def getProbabilities(self,occupant):
        
        # get subsets
        if not occupant.universal:
            weekdayCaseIds, weekdayWeights = Occupancy.getCaseIds(occupant.age,occupant.occupationStatus,occupant.occupationCategory,occupant.parentalStatus,True)
            weekendCaseIds, weekendWeights = Occupancy.getCaseIds(occupant.age,occupant.occupationStatus,occupant.occupationCategory,occupant.parentalStatus,False)
            activityDataWeekdaySubset = Occupancy.activityData.loc[weekdayCaseIds].values.T
            activityDataWeekendSubset = Occupancy.activityData.loc[weekendCaseIds].values.T

        # check for (possibly new) universal occupant
        if occupant.universal:
            initialProb = Occupancy.universalInitialProb
            weekdayProb = Occupancy.universalWeekdayProb
            weekendProb = Occupancy.universalWeekendProb
            return initialProb, weekdayProb, weekendProb

        # get initial probability
        initialProb = np.zeros(Occupancy.numActivities)

        # weekday versus weekend
        if self.timeStamps[0].weekday() < 5: # if weekday
            activityDataSubset = activityDataWeekdaySubset
            weights = weekdayWeights 
        else:
            activityDataSubset = activityDataWeekendSubset
            weights = weekendWeights

        # initial conditions probability 
        for startActivity in range(self.numActivities):
            initialProb[startActivity] = np.sum((activityDataSubset[0] == startActivity)*weights)/np.sum(weights)

        # get weekday probabilities
        weekdayProb = Occupancy.getMCMCProbabilities(activityDataWeekdaySubset,weekdayWeights)
        weekendProb = Occupancy.getMCMCProbabilities(activityDataWeekendSubset,weekendWeights)

        return initialProb, weekdayProb, weekendProb
           
    def sample(self,occupant):
        initialProb, weekdayProb, weekendProb = self.getProbabilities(occupant)

        samplingTimeStamps = np.arange(self.timeStamps[0],self.timeStamps[-1],timedelta(minutes=10)).astype(datetime)

        # must start at 00:00:00
        assert(samplingTimeStamps[0].hour == 0 and samplingTimeStamps[0].minute == 0)

        activity = np.zeros(len(samplingTimeStamps)).astype(int)

        #initial activity
        activity[0] = rng.choice(Occupancy.numActivities,p=initialProb)

        for t,ts in enumerate(samplingTimeStamps[1:]):
            # weekday vs weekend
            prob = weekdayProb if ts.weekday() < 5 else weekendProb
            
            # get probability for given time step and start activity
            prob = prob[(t//6)%24,activity[t]]

            # sample
            activity[t+1] = rng.choice(Occupancy.numActivities,p=prob)
        
        # place in pd.Series and resample
        activity = pd.Series(activity, samplingTimeStamps, dtype=int)
        activity = activity._append(pd.Series(activity.iloc[-1],[self.timeStamps[-1]],dtype=int))
        # activity = activity.resample(timedelta(minutes=self.timeRes)).pad()
        activity = activity.resample(timedelta(minutes=self.timeRes)).ffill()
        activity = activity.pad()
        

        occupant.activity = activity

        for col in self.activity.columns:
            self.activity[col] += activity == col
        self.occupancy += activity > 0


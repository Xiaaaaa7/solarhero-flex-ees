import numpy as np
from datetime import timedelta
import random

rng = np.random.default_rng()

class DirectAppliances():

    numActivities = 9

    # from Diao et   al. with adapted components (i.e. dishwashing and laundry from Muratori et al.)
    activityPowerRatings = [0, # away; none
                            0, # sleeping; none
                            100, # grooming; water heater separate
                            3000, #3500, # cooking; stove, toaster, oven #changed in 01/16/2022 for validation
                            0, # dishwashing; profiled below
                            1500, # cleaning; vacuum cleaner
                            0, # laundry; profiled below
                            180, # leisure; tv, computer #changed in 01/23 for validation, was 120 initially
                            0] # other

    #laundryProfile = np.array([425]*3+[3400]*9) # 30 minute wash, 90 minute dry
    laundryProfile = np.array([random.uniform(400, 450)]*random.randint(3, 6)+[random.uniform(3200, 3600)]*random.randint(6, 9))
    
    #dishwasherProfile = np.array([1800]*6)
    dishwasherProfile = np.array([random.uniform(1600, 2000)]*random.randint(12, 24))

    def __init__(self):
        
        # outputs
        self.P = None
        self.W = None

    def run(self, activity):

        # inputs
        timeStamps = activity.index
        timeRes = (timeStamps[1]-timeStamps[0]).seconds//60%60
        
        # resample
        # activity = activity.resample(timedelta(minutes=10)).pad()
        activity = activity.resample(timedelta(minutes=10)).interpolate()

        # reduce activities to account for sharing
        activity = (activity > 0)

        # direct appliances
        P = activity * DirectAppliances.activityPowerRatings

        # for durational activities iterate
        dishwashing = 4
        laundry = 6
        cooking_n=3
        grooming_n=2
        leisure_n=7

        for t in range(len(activity)):
            #print(len(activity))
            #print(t)
            
            if P.iloc[t,cooking_n] == 0 and activity.iloc[t,cooking_n] == 1 and rng.uniform() < 0.2: #Added on Jan 27 for validation
                
                P.iloc[t,cooking_n] = 0

            # dishwashing (activity 4)
            if P.iloc[t,dishwashing] == 0 and activity.iloc[t,dishwashing] == 1 and rng.uniform() < 0.1: #changed from 80 to 0.8 on Jan 25 changed from 80 to 0.5 on Jan 25
                duration = min(6,P.shape[0]-t)
                P.iloc[t:t+duration,dishwashing] = DirectAppliances.dishwasherProfile[:duration]
            elif P.iloc[t,dishwashing] == 0 and t%144>96 and t%144<126 and rng.uniform() < 0.005: #changed from 0.02 to 0.01 on Jan 22, error is 13% when 0.02 changed from 90 to 72 on Jan23 changed from 72 to 90 on Jan29
                duration = min(6,P.shape[0]-t)
                P.iloc[t:t+duration,dishwashing] = DirectAppliances.dishwasherProfile[:duration]
                

            # laundry (activity 6)
            if P.iloc[t,laundry] == 0 and activity.iloc[t,laundry] == 1 and rng.uniform() < 0.05: # if laundry off and #changed from 80 to 0.8 on Jan 25 changed from 80 to 0.5 on Jan 25
                duration = min(9,P.shape[0]-t)
                P.iloc[t:t+duration,laundry] = DirectAppliances.laundryProfile[:duration]
            elif P.iloc[t,laundry] == 0 and t%144>96 and t%144<126 and rng.uniform() < 0.005: #changed from 0.02 to 0.03 on Jan 22, error is 13% when 0.02 changed from 90 to 72 on Jan23 changed from 72 to 90 on Jan29
                duration = min(9,P.shape[0]-t)
                P.iloc[t:t+duration,laundry] = DirectAppliances.laundryProfile[:duration]
                

                
            #if P.iloc[t,cooking_n] == 0 and t%1440>600 and t%1440<900 and rng.uniform() < 50:
            #    duration = min(9,P.shape[0]-t)
            #    P.iloc[t:t+duration,cooking_n] = DirectAppliances.cooking_nProfile[:duration]
        
        # resample 
        # self.P = P.resample(timedelta(minutes=timeRes)).pad()
        self.P = P.resample(timedelta(minutes=timeRes)).ffill()
        self.P = self.P.pad().sum(axis=1)

        self.W = self.P * timeRes / 60


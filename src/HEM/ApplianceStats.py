import numpy as np
import pandas as pd
import os 

from HEM.utility import utility

local_path = os.path.dirname(__file__)

rng = np.random.default_rng()

class ApplianceStats():

    __recsMicroDataFilename = os.path.join(local_path,'..','..','raw-data','recs','recs2015_public_v4.csv')

    def __init__(self,income,numOccupants,division):
        self.income = income
        self.numOccupants = numOccupants
        self.division = division

    def __getData(self,byIncome=True,byNumOccupants=True,byDivision=True):
        # open microdata
        recs = pd.read_csv(ApplianceStats.__recsMicroDataFilename)
        divisionConversion = {1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:8,10:9}
        recs['census division'] = recs['DIVISION'].map(divisionConversion)
        # get subset
        subset = recs

        if byIncome:
            incomeCode = utility.convert.income2recsIncomeCode(self.income)
            subset = recs[recs['MONEYPY']//2 == incomeCode//2] # divide by two for larger sample
        
        if byNumOccupants:
            if self.numOccupants < 5:
                subset = subset[subset['NHSLDMEM'] == self.numOccupants]
            else:
                subset = subset[subset['NHSLDMEM'] > 4]

        if byDivision:
            subset = subset[subset['census division'] == self.division]
        
        if len(subset) < 10:
            if byDivision:
                subset = self.__getData(byDivision=False)
            else:
                print('SMALL SAMPLE SIZE')

        return subset

    def sampleHousehold(self,occupants_num,defaultAppliances=True):

        if defaultAppliances:
            self.numRefrigerators = 1
            self.numFreezers = 1
            self.electricAirConditioner = True
            self.electricHeater = True
            self.electricWaterHeater = True
            if occupants_num<3:
                self.annualColdAppliancesConsumption = 1100*1000 # Wh
                self.numLedBulbs = 5
                self.numCflBulbs = 15
                self.numIncBulbs = 10
                self.volumeWaterHeater = 190 # liters
            elif occupants_num>2 and occupants_num<5:
                self.annualColdAppliancesConsumption = 1200*1000 # Wh
                self.numLedBulbs = 6
                self.numCflBulbs = 16
                self.numIncBulbs = 12
                self.volumeWaterHeater = 210 # liters
            else:
                self.annualColdAppliancesConsumption = 1300*1000 # Wh
                self.numLedBulbs = 7
                self.numCflBulbs = 18
                self.numIncBulbs = 15
                self.volumeWaterHeater = 240 # liters
            return

        data = self.__getData()

        # get normalized weight
        data['normalized weight'] = data['NWEIGHT']/(data['NWEIGHT'].sum())

        # select a respondent to populate the house with
        respondent = data.index[rng.choice(len(data),p=data['normalized weight'])]

        # cold appliances consumption
        self.annualColdAppliancesConsumption = (data.at[respondent,'KWHRFG']+data.at[respondent,'KWHFRZ'])*1000
        self.numRefrigerators = data.at[respondent,'NUMFRIG'] 
        self.numFreezers = data.at[respondent,'NUMFREEZ']

        # lightbulbs
        proportion = [0.0,1.0,.75,.5,.25] # convert the RECS response codes to proportion of lighting
        numBulbs = data.at[respondent,'LGTINNUM']*20 + rng.integers(0,20)

        self.numLedBulbs = int(numBulbs*proportion[data.at[respondent,'LGTINLED']])
        self.numIncBulbs = min(numBulbs-self.numLedBulbs, int(numBulbs*proportion[data.at[respondent,'LGTINCAN']]))
        self.numCflBulbs = max(0,numBulbs-(self.numLedBulbs+self.numIncBulbs))

        # hvac
        self.electricAirConditioner = data.at[respondent,'AIRCOND']
        self.electricHeater = data.at[respondent,'FUELHEAT'] == 5
        
        # water heating
        self.electricWaterHeater = data.at[respondent,'FUELH2O'] == 5
        self.volumeWaterHeater = data.at[respondent,'WHEATSIZ']
        
        volumes = [(0,30),(30,50),(50,75),(30,50)]

        if self.volumeWaterHeater == -2:
            self.electricWaterHeater = False    
        else:
            bounds = volumes[self.volumeWaterHeater-1]
            self.volumeWaterHeater = rng.uniform(bounds[0],bounds[1]) * 3.8 # gallons to liters
        
        
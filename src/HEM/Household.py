from HEM.Lighting import Lighting
from HEM.Occupancy import Occupancy
from HEM.HVAC import HVAC
from HEM.ColdAppliances import ColdAppliances
from HEM.ApplianceStats import ApplianceStats
from HEM.WaterHeater import WaterHeater
from HEM.DirectAppliances import DirectAppliances

import numpy as np

class Household():

    def __init__(self, occupants, income, division, defaultAppliances=True):
        # inputs
        self.occupants = occupants
        self.income = income
        self.division = division
        self.defaultAppliances=defaultAppliances
        
        # get appliances
        self.appliances = ApplianceStats(income, len(occupants), division)
        self.appliances.sampleHousehold(len(occupants),defaultAppliances=defaultAppliances)

        # construct model features
        self.occupancyModel = Occupancy(occupants)
        self.hvac = HVAC(self.appliances.electricHeater,self.appliances.electricAirConditioner)
        self.coldAppliances = ColdAppliances(self.appliances.annualColdAppliancesConsumption,self.appliances.numRefrigerators,self.appliances.numFreezers)
        self.lighting = Lighting(self.appliances.numLedBulbs,self.appliances.numIncBulbs,self.appliances.numCflBulbs)
        self.waterHeater = WaterHeater(self.appliances.electricWaterHeater,self.appliances.volumeWaterHeater)
        self.directAppliances = DirectAppliances()

        # outputs
        self.P = None
        self.W = None

    def run(self,ambientTemperature,irradiance):

        self.ambientTemperature = ambientTemperature
        self.irradiance = irradiance
        self.timeStamps = ambientTemperature.index

        self.occupancyModel.run(self.timeStamps)
        self.hvac.run(self.ambientTemperature,self.occupancyModel.occupancy)
        self.coldAppliances.run(self.timeStamps)
        self.lighting.run(self.irradiance,self.occupancyModel.activity)
        #print(self.occupancyModel.activity)
        self.waterHeater.run(self.ambientTemperature,self.occupancyModel.activity)
        self.directAppliances.run(self.occupancyModel.activity)

        self.P = self.hvac.P + self.coldAppliances.P + self.lighting.P + self.waterHeater.P + self.directAppliances.P
        self.W = self.hvac.W + self.coldAppliances.W + self.lighting.W + self.waterHeater.W + self.directAppliances.W

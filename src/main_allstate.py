import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from HEM.Household import Household
from HEM.Occupancy import Occupant
from HEM.utility import utility

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

local_path = os.path.dirname(__file__)

def main():
    n = 100
    #state='CA'     state_code=6    
    #state='WA'     state_code=53
    #state='AK'        state_code=2
    #state='CO'    state_code=8        # state='MA'    # state_code=25
    #state='MN'    state_code=27       #state='OR'       state_code=41    
    #state='AL'       state_code=1     #state='AZ'       state_code=4     
    #state='AR'       state_code=5     #state='CT'       state_code=9     
    #state='DE'       state_code=10    #state='FL'       state_code=12    
    #state='GA'       state_code=13    #state='HI'       state_code=15    
    #state='ID'       state_code=16    #state='IL'       state_code=17    
    #state='IN'       state_code=18    #state='IA'       state_code=19    
    #state='KS'       state_code=20    #state='KY'       state_code=21    
    #state='LA'       state_code=22    #state='ME'       state_code=23    
    #state='MD'       state_code=24    #state='MA'       state_code=25    
    #state='MI'       state_code=26    #state='MS'       state_code=28    
    #state='MO'       state_code=29    #state='MT'       state_code=30    
    #state='NE'       state_code=31    #state='NV'       state_code=32    
    #state='NH'       state_code=33    #state='NJ'       state_code=34
    #state='NM'       state_code=35    #state='NY'       state_code=36
    #state='NC'       state_code=37    #state='ND'       state_code=38
    #state='OH'       state_code=39    #state='OK'       state_code=40
    #state='PA'       state_code=42    #state='RI'       state_code=44
    #state='SC'       state_code=45    #state='SD'       state_code=46
    #state='TN'       state_code=47    #state='TX'       state_code=48    
    #state='UT'       state_code=49
    #state='VT'       state_code=50    #state='VA'       state_code=51
    #state='WV'       state_code=54    #state='WI'       state_code=55
    #state='District of Columbia'       state_code=11
    state='WY'       
    state_code=56
    
    # output directory
    outputDirectory = os.path.join(local_path,'..','output-data','main-'+state)
    
    if os.path.exists(outputDirectory)==0:
    
        os.makedirs(outputDirectory, exist_ok=False)

    # use Austin, TX weather data
    # nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','austin-tx-2019-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Sacramento-ca-2023-5-min-nsrdb.csv')
    # nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','seattle-wa-2019-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Denver-co-2023-5-min-nsrdb.csv')
    # nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','raleigh-nc-2019-5-min-nsrdb.csv')    
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','SaintPaul-mn-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','salem-or-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','montgomery-al-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','phoenix-az-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','LittleRock-ar-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','hartford-ct-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Dover-de-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Tallahassee-fl-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Atlanta-ga-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Honolulu-hi-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Boise-id-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Springfield-il-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Indianapolis-in-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','DesMoines-ia-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Topeka-ks-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Frankfort-ky-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','BatonRouge-la-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Augusta-me-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Annapolis-md-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Boston-ma-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Lansing-mi-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Jackson-ms-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','JeffersonCity-mo-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Helena-mt-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Lincoln-ne-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','CarsonCity-nv-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Concord-nh-2023-5-min-nsrdb.csv')    
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Trenton-nj-2023-5-min-nsrdb.csv')       #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','SantaFe-nm-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Albany-ny-2023-5-min-nsrdb.csv')        #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Raleigh-nc-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Bismarck-nd-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Columbus-oh-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','OklahomaCity-ok-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Harrisburg-pa-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Providence-ri-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Columbia-sc-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Pierre-sd-2023-5-min-nsrdb.csv')        #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Nashville-tn-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Austin-tx-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','SaltLakeCity-ut-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Montpelier-vt-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Richmond-va-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Olympia-wa-2023-5-min-nsrdb.csv')    
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Charleston-wv-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Madison-wi-2023-5-min-nsrdb.csv')    
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Cheyenne-wy-2023-5-min-nsrdb.csv')    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Juneau-ak-2023-5-min-nsrdb.csv')
    #nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Washington-DC-2023-5-min-nsrdb.csv')
    nsrdbFilepath = os.path.join(local_path,'..','raw-data','nsrdb','Cheyenne-wy-2023-5-min-nsrdb.csv')

    print(nsrdbFilepath)
    nsrdb = utility.getNsrdbData(nsrdbFilepath)
    
    # extract ambient temperature and irradiance only
    ambientTemperature = nsrdb['Temperature']
    irradiance = nsrdb['GHI']


    # get households
    cpsDataFilepath = os.path.join(local_path,'..','processed-data','cps','processed-cps-2023.csv')#
    cpsData = pd.read_csv(cpsDataFilepath)
    
    # get california and texas households
    householdIds = pd.unique(cpsData[cpsData['state'] == state_code]['household'])[:n]
    
    state=[]
    for i in range(0,len(householdIds)):
        state.append(state)
        
    # get all household ids and save cps data
    
    # reorder to switch between california and texas households (in case of failure)
    householdIds = householdIds.reshape(2,-1).T.flatten()
    pd.DataFrame(householdIds).to_csv(outputDirectory+'//householdIds.csv')
    print(householdIds)
    # save cps data
    cpsData = cpsData[cpsData['household'].isin(householdIds)]
    cpsData.to_csv(os.path.join(outputDirectory,'output-cps-subset.csv'))
    Household_num=[]
    
    # iterate through households
    for i, householdId in enumerate(householdIds):

        print(i, householdId, datetime.now())

        outputFilepath = os.path.join(outputDirectory,'output-household-{}.csv'.format(householdId))

        if os.path.exists(outputFilepath):
            continue
        # print('Write')
        # get individuals in household
        subset = cpsData[cpsData['household'] == householdId]
        # household_num=len(subset)
        
        # construct occupant list
        occupants = list(subset.apply(lambda row: Occupant(row['age'],row['occupation status'],row['occupation category'],row['parental status']),axis=1))
        Household_num.append(len(occupants))
        
        #print(Household_num)
        # construct household object
        household = Household(occupants,subset['family income'].iloc[0],subset['census division'].iloc[0])
        
        # run

        household.run(ambientTemperature,irradiance)

        householdOutput = pd.DataFrame()
        householdOutput['total (kWh)'] = household.W / 1000
        householdOutput['space heating (kWh)'] = household.hvac.heater.W / 1000
        householdOutput['ac (kWh)'] = household.hvac.ac.W / 1000
        householdOutput['water heating (kWh)'] = household.waterHeater.W / 1000
        householdOutput['lighting (kWh)'] = household.lighting.W / 1000
        householdOutput['cold appliances (kWh)'] = household.coldAppliances.W / 1000
        householdOutput['other (kWh)'] = household.directAppliances.W / 1000

        # save household
        householdOutput.to_csv(outputFilepath)
        
if __name__ == '__main__':
    import time
    start = time.time()
    main()
    end = time.time()
    
    elapsed = end - start
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    print(f"\n✅ Total run time: {hours} hours {minutes} minutes {seconds} seconds")
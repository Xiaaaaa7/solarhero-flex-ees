import pandas as pd
import os

rawDataDirectory = os.path.join('..','raw-data','cps')
years = [2019]
months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

for year in years:
    for month in months:
        fileName = '{}{}pub'.format(month,str(year)[-2:])
        fileLocation = 'https://www2.census.gov/programs-surveys/cps/datasets/{}/basic/{}.zip'.format(year,fileName)
        tmp = pd.read_csv(fileLocation,compression='zip')
        tmp.to_csv(os.path.join(rawDataDirectory,'{}.dat'.format(fileName)),index=False)

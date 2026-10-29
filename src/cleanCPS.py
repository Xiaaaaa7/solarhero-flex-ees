import pandas as pd
import numpy as np
import os
from HEM.utility import utility

local_path = os.path.dirname(__file__)

class CPS:

    @staticmethod
    def getVariables(layoutFilename):
        '''getVariables(layoutFilename):
        Read the CPS layout file, which contains the variable names, descriptions, and column numbers 
        in the raw ASCII dat file. I (ijbd) made some edits to some of the files due to swapped column
        numbers (e.g. 2014-Jan. 2016 GEDIV variable).

        Returns:
        A list of variable tuples taking the following form:
        [(var 1), (var 2)...  (VARIABLE_NAME, VARIABLE_START_COL, VARIABLE_END_COL) ... (var n-1), var(n)]
        
        '''
        variables = []

        with open(layoutFilename) as f:
            i = 0
            for line in f:
                i += 1
                if line[0].isspace():
                    continue
                else:
                    # check for variable line
                    split = line.split()
                    if len(split) < 4:
                        continue
                    if split[0][0] not in ['F','G','P','H','O','Q']:
                        continue
                    if not split[1].isnumeric():
                        continue
                    if not split[-3].isnumeric():
                        continue
                    if not split[-2] == '-':
                        continue
                    if not split[-1].isnumeric():
                        continue

                    variables.append((split[0], int(split[-3])-1, int(split[-1])))

                    # check for failure 
                    if len(variables) > 1 and variables[-1][1] != variables[-2][2]:
                        print('missing variable at between {} and {} (around line number {})'.format(variables[-2][0],variables[-1][0],i))
            
        return variables

    # nested classes
    class Filepaths:
        rawDataDirectory = os.path.join(local_path,'..','raw-data')
        processedDataDirectory = os.path.join(local_path,'..','processed-data')
        
        def __init__(self):
            pass

    # static variables
    filepaths = Filepaths()

    # init
    def __init__(self,atusYears=[2015,2016,2017,2018,2019],populationYears=[2019]):
        print('cleaning CPS data ({})'.format('-'.join([str(year) for year in atusYears])))
        self.atusYears = atusYears
        self.populationYears = populationYears
        
        # data
        print('\t','...getting ATUS respondent data')
        demFilepath = os.path.join(CPS.filepaths.processedDataDirectory,'atus','processed-atus-dem-{}.csv'.format('-'.join([str(year) for year in atusYears])))
        self.dem = pd.read_csv(demFilepath,index_col=0)
        self.cpsYears = list(self.dem['HRYEAR4'].unique())
        
        # get CPS ASCII File variables and layout
        print('\t','...getting ASCII file layouts')
        self.variables14 = self.getVariables(os.path.join(CPS.filepaths.rawDataDirectory,'cps','January_2014_Record_Layout.txt'))
        self.variables15 = self.getVariables(os.path.join(CPS.filepaths.rawDataDirectory,'cps','January_2015_Record_Layout.txt'))
        self.variables16 = self.getVariables(os.path.join(CPS.filepaths.rawDataDirectory,'cps','February_2016_Record_Layout.txt'))
        self.variables17 = self.getVariables(os.path.join(CPS.filepaths.rawDataDirectory,'cps','January_2017_Record_Layout.txt'))

        # parse and convert monthly CPS files from .dat to .csv
        print('\t','...converting monthly ASCII files to CSV')
        self.months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
        for year in self.cpsYears:
            for month in self.months:
                self.getCpsDataMonth(month,year,save_only=True)

        # get combined CPS data
        print('\t','...combining monthly respondents and linking ATUS respondents')
        self.cpsDataAtus, self.cpsDataAll =self.getCombinedData()

        print('\t','...separating into households and labeling individuals')
        self.cpsDataAtusLabeled, self.cpsDataAllLabeled = self.label()

        print('\t','...done cleaning CPS data')

        print('\t','...compiling brief analysis')
        self.analysis()

    # member functions
    
    def getCpsDataMonth(self, month, year, save_only=False):
        '''getData(self, month, year, return_none):
        Use the ASCII layout (stored in 'self.variablesYY'), parse the monthly CPS datafile
        '''

        cpsDataMonthFilename = os.path.join(CPS.filepaths.processedDataDirectory,'cps','saved','monthly','saved-cps-{}{}pub.csv'.format(month,str(year)[-2:]))

        # check if file already exists
        if os.path.exists(cpsDataMonthFilename):   
            
            if not save_only:

                # load
                cpsDataMonth = pd.read_csv(cpsDataMonthFilename)
                return cpsDataMonth

        else:
            print('\t\t','...{}, {}'.format(month,year),flush=True)
            # get correct variable set
            if year == 2014:
                variables = self.variables14
            elif year == 2015 or (year == 2016 and month == 'jan'):
                variables = self.variables15
            elif year == 2016:
                variables = self.variables16
            elif year in [2017, 2018, 2019]: 
                variables = self.variables17
            else:
                raise RuntimeError('Invalid year!')

            # filename
            rawDataFilename = os.path.join(CPS.filepaths.rawDataDirectory,'cps','monthly','{}{}pub.dat'.format(month,str(year)[-2:]))
            
            # alter filler and padding duplicates
            names = [var[0] for var in variables]
            names = [names[i]+str(i) if names[i] in ['FILLER','PADDING'] else names[i] for i in range(len(names))]
            
            # open data
            cpsVariables = ['HRHHID',
                            'HRHHID2',
                            'HRYEAR4',
                            'HRMONTH', # for labeling and grouping households
                            'PULINENO', # for linking with CPS
                            'PRTAGE',
                            'PRPERTYP',
                            'PRWKSTAT',
                            'PRMJOCGR',
                            'PRNMCHLD',
                            'PWCMPWGT',
                            'HWHHWGT',
                            'PWFMWGT',
                            'PWSSWGT', # for classification
                            'GEREG',
                            'GEDIV',
                            'GESTFIPS',
                            'GTCBSA',
                            'GTCO',
                            'GTCBSAST',
                            'GTMETSTA',
                            'GTINDVPC',
                            'GTCSA', # for geography
                            'HEFAMINC',
                            'HRNUMHOU']

            cpsDataMonth = pd.read_fwf(rawDataFilename,
                                        names=names,
                                        colspecs=[(variable[1],variable[2]) for variable in variables],
                                        usecols=cpsVariables) # for validation/exploration

            cpsDataMonth = cpsDataMonth[cpsVariables] # reorder for human readable csv

            # remove filler and padding
            cpsDataMonth = cpsDataMonth[[col for col in cpsDataMonth.columns if col.find('FILLER') == -1]]
            cpsDataMonth = cpsDataMonth[[col for col in cpsDataMonth.columns if col.find('PADDING') == -1]]

            #save
            cpsDataMonth.to_csv(cpsDataMonthFilename,index=False)

            # return
            return cpsDataMonth
        
    def getCombinedData(self):
        '''getCombinedData(self):
        combine the monthly cps files.
        For ATUS respondents, all cps files will be combined.
        For non-ATUS respondents, cps files will be saved by year (as not to exceed memory).
        '''
        # construct new dataframe
        cpsDataAtus = pd.DataFrame()
        cpsDataAll = pd.DataFrame()

        cpsDataAtusFilepath = os.path.join(CPS.filepaths.processedDataDirectory,'cps','saved','saved-cps-atus-respondents-{}.csv'.format('-'.join([str(year) for year in self.populationYears])))
        cpsDataAllFilepath = os.path.join(CPS.filepaths.processedDataDirectory,'cps','saved','saved-cps-{}.csv'.format('-'.join([str(year) for year in self.populationYears])))
                
        if os.path.exists(cpsDataAtusFilepath) and os.path.exists(cpsDataAllFilepath):
            print('\t\t','...saved files found')
            cpsDataAtus = pd.read_csv(cpsDataAtusFilepath,index_col=0)
            cpsDataAll = pd.read_csv(cpsDataAllFilepath)
        else:
            # for filtering
            atusRespondents = pd.Series(zip(self.dem['HRHHID'],
                                            self.dem['HRHHID2'],
                                            self.dem['PULINENO'],
                                            self.dem['HRYEAR4'],
                                            self.dem['HRMONTH']))

            # get needed month, years (including 2019)
            desiredMonths = pd.unique(list(zip(self.dem['HRYEAR4'],self.dem['HRMONTH'])) + [(2019,m+1) for m in range(12)])
            desiredMonths.sort()

            for (year, month) in desiredMonths:
                print('\t\t','...{}, {}'.format(self.months[month-1],year))
                # open 
                cpsDataMonth = self.getCpsDataMonth(self.months[month-1],year)

                # atus respondent filter
                atusRespondentsFilter = pd.Series(zip(cpsDataMonth['HRHHID'],
                                                        cpsDataMonth['HRHHID2'],
                                                        cpsDataMonth['PULINENO'],
                                                        cpsDataMonth['HRYEAR4'],
                                                        cpsDataMonth['HRMONTH'])).isin(atusRespondents)

                # concat
                cpsDataAtus = pd.concat((cpsDataAtus,cpsDataMonth[atusRespondentsFilter]),ignore_index=True)
                
                # population data
                if year in self.populationYears:
                    cpsDataAll = pd.concat((cpsDataAll,cpsDataMonth),ignore_index=True)

            # drop duplicate households
            cpsDataAll.drop_duplicates(['HRHHID','HRHHID2','PULINENO'],keep='last',inplace=True)

            # assert all atus respondents accounted for properly
            cpsDataAtusRespondents = pd.Series(zip(cpsDataAtus['HRHHID'],
                                                    cpsDataAtus['HRHHID2'],
                                                    cpsDataAtus['PULINENO'],
                                                    cpsDataAtus['HRYEAR4'],
                                                    cpsDataAtus['HRMONTH']))

            print('\t\t','...checking that all ATUS respondents are included in ATUS CPS data')
            assert(atusRespondents.isin(cpsDataAtusRespondents).all())
            assert(cpsDataAtusRespondents.isin(atusRespondents).all())

            # add TUCASEID to ATUS respondents
            print('\t\t','...assigning ATUS Case ID to CPS ATUS subset')
            caseIds = pd.Series(self.dem.index.values, atusRespondents)
            cpsDataAtus['TUCASEID'] = cpsDataAtus.apply(lambda row: caseIds[(row['HRHHID'],row['HRHHID2'],row['PULINENO'],row['HRYEAR4'],row['HRMONTH'])],axis=1)

            print('\t\t','...saving CPS data')
            cpsDataAtus.to_csv(cpsDataAtusFilepath,index=False)
            cpsDataAll.to_csv(cpsDataAllFilepath,index=False)

        return cpsDataAtus, cpsDataAll

    def label(self):
        
        cpsDataAllLabeledFilepath = os.path.join(CPS.filepaths.processedDataDirectory,'cps','processed-cps-{}.csv'.format('-'.join([str(year) for year in self.atusYears])))
        cpsDataAtusLabeledFilepath = os.path.join(CPS.filepaths.processedDataDirectory,'cps','processed-cps-atus-respondents-{}.csv'.format('-'.join([str(year) for year in self.atusYears])))

        if os.path.exists(cpsDataAllLabeledFilepath) and os.path.exists(cpsDataAtusLabeledFilepath):
            print('\t\t','...saved files found')
            cpsDataAllLabeled = pd.read_csv(cpsDataAllLabeledFilepath)
            cpsDataAtusLabeled = pd.read_csv(cpsDataAtusLabeledFilepath)
            return cpsDataAtusLabeled, cpsDataAllLabeled

        # construct labeled outputs
        cpsDataAllLabeled = self.cpsDataAll
        cpsDataAtusLabeled = self.cpsDataAtus
        
        # weights
        cpsDataAllLabeled = cpsDataAllLabeled[cpsDataAllLabeled['HWHHWGT'] != -1]

        # get unique households
        households = pd.unique(pd.Series(zip(self.cpsDataAll['HRHHID'],
                                            self.cpsDataAll['HRHHID2'],
                                            self.cpsDataAll['HRYEAR4'],
                                            self.cpsDataAll['HRMONTH'])))
        households = pd.Series(range(len(households)),households)

        # get household label
        cpsDataAllLabeled['household'] = cpsDataAllLabeled.apply(lambda row: households[(row['HRHHID'],row['HRHHID2'],row['HRYEAR4'],row['HRMONTH'])],axis=1)  

        # get individual ATUS label
        cpsDataAtusLabeled['case id'] = cpsDataAtusLabeled['TUCASEID'].values

        # label and classify
        def labelAndClassify(data):
            # age label
            data['age_act']=data['PRTAGE']
            data['age'] = pd.cut(data['PRTAGE'],bins=[0,18,65,85],labels=[0,1,2],include_lowest=True)
            data['age'] = np.where(data['age'] == -1,pd.NA,data['age'])

            # work status
            data['occupation status'] = np.where(data['PRWKSTAT'].isin([1,5,10,11,12]),0,pd.NA) # Not in labor force
            data['occupation status'] = np.where(data['PRWKSTAT'].isin([2,8,9]),1,data['occupation status']) # full time
            data['occupation status'] = np.where(data['PRWKSTAT'].isin([3,4,6,7]),2,data['occupation status']) # part time

            # work category
            data['occupation category'] = np.where(data['PRMJOCGR'] == -1, pd.NA, data['PRMJOCGR'])

            # parental status
            data['parental status'] = np.where(data['PRNMCHLD'] > 0,1,0)

            # additional variables
            data['family income'] = data['HEFAMINC'].apply(utility.convert.cpsIncomeCode2income)            
            data['city code'] = data['GTCBSA'].values
            data['state'] = data['GESTFIPS'].values
            data['census division'] = data['GEDIV'].values
            return data

        cpsDataAtusLabeled = labelAndClassify(cpsDataAtusLabeled)
        cpsDataAllLabeled = labelAndClassify(cpsDataAllLabeled)

        # get weekday/weekend
        cpsDataAtusLabeled['weekday'] = np.where(self.dem.loc[cpsDataAtusLabeled['case id'],'TUWEEKDAY'],1,0)

        # get ATUS weight
        cpsDataAtusLabeled['representative weight'] = cpsDataAtusLabeled['HWHHWGT'].values

        # keep necessary variables
        cpsDataAllLabeled = cpsDataAllLabeled[['household','age','age_act','occupation status','occupation category','parental status','family income','state','city code','census division']]
        cpsDataAtusLabeled = cpsDataAtusLabeled[['case id','age','age_act','occupation status','occupation category','parental status','family income','state','city code','census division','representative weight','weekday']]
        
        # save
        print('\t\t','...saving final processed files')
        cpsDataAllLabeled.to_csv(cpsDataAllLabeledFilepath,index=False)
        cpsDataAtusLabeled.to_csv(cpsDataAtusLabeledFilepath,index=False)

        return cpsDataAtusLabeled, cpsDataAllLabeled

    def analysis(self):
        sample = self.cpsDataAtusLabeled
        population = self.cpsDataAllLabeled
        print('\t\t','...population size:',len(population))
        print('\t\t','...number of households:',population['household'].max())
        print('\t\t','...sample size:',len(sample))
        print('\t\t','...number of weekday respondents:',sample['weekday'].sum())
        '''
        # check sample size for each population classification  
        def findCaseIds(age,occupationStatus,occupationCategory,parentalStatus,weekday=True):
            # get classification
            subset = sample[sample['weekday'] == weekday]
            if not age is pd.NA:
                #print('filtering by age')
                subset = subset[subset['age'] == age]
            if not occupationStatus is pd.NA:
                #print('filtering by occupation status')
                subset = subset[subset['occupation status'] == occupationStatus]
            if not occupationCategory is pd.NA:
                #print('filtering by occupation category')
                subset = subset[subset['occupation category'] == occupationCategory]
            if not parentalStatus is pd.NA:
                #print('filtering by parental status')
                subset = subset[subset['parental status'] == parentalStatus]
            return subset['case id'].values

            for category in range(1,8):
                print(status,category,len(findCaseIds(pd.NA,status,category,pd.NA)))
            
        for category in range(1,8):
            print(category,len(findCaseIds(pd.NA,pd.NA,category,pd.NA)))

        print('')

        for status in range(3):
            print(status,len(findCaseIds(pd.NA,status,pd.NA,pd.NA)))

        print('')
        for parent in range(2):
            print(parent,len(findCaseIds(pd.NA,pd.NA,pd.NA,parent)))
        '''

if __name__ == '__main__':
    c = CPS()
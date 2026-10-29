import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import os, sys
from datetime import datetime, timedelta

local_path = os.path.dirname(__file__)

class ATUS:

    @staticmethod
    def parseDatetime(datetimeStr, nextDay):
            dt = datetime.strptime(datetimeStr,'%H:%M:%S')
            dt = datetime(2000,1,1,dt.hour,dt.minute,dt.second)
            if nextDay:
                dt += timedelta(days=1)
            return dt

    @staticmethod
    def getDatetimeRange(startDay,startHour,startMinute, endDay, endHour, endMinute, timeRes):
        return np.arange(datetime(2000,1,startDay,startHour,startMinute,0), # start
                        datetime(2000,1,endDay,endHour,endMinute,0), # end
                        timedelta(minutes=timeRes)).astype(datetime) # time steps

    # nested classes
    class Filepaths:
        rawDataDirectory = os.path.join(local_path,'..','raw-data','atus')
        processedDataDirectory = os.path.join(local_path,'..','processed-data','atus')
        savedDataDirectory = os.path.join(processedDataDirectory,'saved')

        def __init__(self):
            pass

    # static variables
    filepaths = Filepaths()

    # init
    def __init__(self,timeRes=10,years=[2015,2016,2017,2018,2019],overwrite=False):
        print('cleaning ATUS data ({}) at {} minute resolution:'.format(', '.join([str(year) for year in years]),timeRes))
        self.timeRes = timeRes
        self.years = years
        self.overwrite = overwrite
        
        # data
        print('\t','...getting raw data')
        self.caseIds, self.rawData = self.getRawData()
        self.timeStamps = ATUS.getDatetimeRange(1,4,0,2,4,0,self.timeRes)
        
        print('\t','...converting to coded schedules',flush=True)
        self.actCode, self.locCode = self.getCodeSchedules()

        # activity info
        self.activityStates, self.activitySecondTierCodes, self.activityCodes = self.getActivityInfo()
        
        # cleaned data
        print('\t','...getting activity, occupancy, and demographic data')
        self.occ = self.getOcc()
        self.act = self.getAct()
        self.dem = self.getDem()

        print('\t','...done cleaning ATUS data')
        self.save()

    # member functions
    
    def getRawData(self):
        # define dataset parameters
        keywords = ['resp','act','cps']
        keywordsToIndexByCaseId = ['resp','cps']

        # construct empty dataframes
        rawData = {keyword : pd.DataFrame() for keyword in keywords}

        # append remaining years of data
        for year in self.years: 
            for keyword in keywords:
                filepath = os.path.join(ATUS.filepaths.rawDataDirectory,'atus{}_{}.csv'.format(keyword,year))
                if keyword in keywordsToIndexByCaseId:
                    atusYear = pd.read_csv(filepath,index_col='TUCASEID')
                else:
                    atusYear = pd.read_csv(filepath)
                rawData[keyword] = pd.concat([rawData[keyword],atusYear])

        caseIds = pd.unique(rawData['act']['TUCASEID'])
        return caseIds, rawData

    def getCodeSchedules(self):
        
        # check for saved matrices
        savedActCodeFilename = os.path.join(ATUS.filepaths.savedDataDirectory,'saved-actCode-{}-{}-min-res.csv'.format('-'.join([str(year) for year in self.years]),str(self.timeRes)))
        savedLocCodeFilename = os.path.join(ATUS.filepaths.savedDataDirectory,'saved-locCode-{}-{}-min-res.csv'.format('-'.join([str(year) for year in self.years]),str(self.timeRes)))

        if os.path.exists(savedActCodeFilename) and os.path.exists(savedLocCodeFilename) and not self.overwrite:
            print('\t','...saved files found')
            actCode = pd.read_csv(savedActCodeFilename,index_col=0)
            locCode = pd.read_csv(savedLocCodeFilename,index_col=0)
        else:
            # construct empty dataframes for each time segment for each case ID
            actCode = pd.DataFrame(index=self.caseIds,columns=[t.time() for t in self.timeStamps])
            locCode = pd.DataFrame(index=self.caseIds,columns=[t.time() for t in self.timeStamps])

            # iterate through all caseIds to build schedule dataframe
            for caseId in self.caseIds:
                # get indices for caseId
                idx = self.rawData['act']['TUCASEID'] == caseId

                # get all activity details
                activities = self.rawData['act'][idx]['TRCODE']
                locations = self.rawData['act'][idx]['TEWHERE']
                startTimes = self.rawData['act'][idx]['TUSTARTTIM']
                stopTimes = self.rawData['act'][idx]['TUSTOPTIME']

                # start day
                currActivity = 0 # keep track of index of current activity
                lastActivity = len(activities)-1
                nextDay = False # keep track if the events have gone into the next day

                # get first activity times
                tStart = ATUS.parseDatetime(startTimes.iloc[currActivity],nextDay)
                tStop = ATUS.parseDatetime(stopTimes.iloc[currActivity],nextDay)

                if tStart.hour > tStop.hour: 
                    nextDay = True
                    tStop += timedelta(days=1)


                try:
                    # iterate through day
                    for t in self.timeStamps:

                        # iterate to current activity (until current time is before the next activity stop time)
                        while t > tStop: 

                            currActivity += 1 # go to next activity until t is before the stop time

                            if currActivity > lastActivity: # for incomplete responses
                                raise IndexError

                            # get new activity times
                            tStart = ATUS.parseDatetime(startTimes.iloc[currActivity],nextDay)
                            tStop = ATUS.parseDatetime(stopTimes.iloc[currActivity],nextDay)

                            if tStart.hour > tStop.hour:
                                nextDay = True
                                tStop += timedelta(days=1)

                        actCode.at[caseId,t.time()] = activities.iloc[currActivity]
                        locCode.at[caseId,t.time()] = locations.iloc[currActivity]

                except IndexError:
                    pass

            # remove incomplete surveys
            actCode.dropna(inplace=True)
            locCode.dropna(inplace=True)

            assert(np.array_equal(actCode.index.values,locCode.index.values))

            # start at midnight
            actCode = actCode[[t.time() for t in ATUS.getDatetimeRange(1,0,0,2,0,0,self.timeRes)]]
            locCode = locCode[[t.time() for t in ATUS.getDatetimeRange(1,0,0,2,0,0,self.timeRes)]]

            actCode.to_csv(savedActCodeFilename,index_label='TUCASEID')
            locCode.to_csv(savedLocCodeFilename,index_label='TUCASEID')

        # refilter based on complete surveys
        self.caseIds = actCode.index
        return actCode, locCode

    def getActivityInfo(self):
        activityStates = ['away',
                        'sleeping',
                        'grooming',
                        'cooking',
                        'dishwashing',
                        'cleaning',
                        'laundry',
                        'leisure',
                        'other']

        activitySecondTierCodes = [[], # away
                                [101], # sleeping
                                [102], # grooming
                                [], # cooking
                                [], # dishwashing
                                [], # cleaning
                                [], # laundry
                                [], # leisure
                                []] # other

        activityCodes = [[], # away
                        [], # sleeping
                        [], # grooming
                        [20201], # cooking 
                        [20203], # dishwashing
                        [20101,20401], # cleaning
                        [20102], # laundry
                        [120303,120304,120305,120306,120307,120308], # leisure
                        []] # other

        return activityStates, activitySecondTierCodes, activityCodes, 

    def getOcc(self):
        # convert locations to occupancy matrix (i.e. whether or not respondent is home)
        occ = pd.DataFrame(index=self.locCode.index,columns=self.locCode.columns)
        occ[(self.locCode == 1) | (self.locCode == -1)] = 1
        occ[(self.locCode != 1) & (self.locCode != -1)] = 0

        return occ

    def getAct(self):
        # convert ATUS activity codes to nine activity types & appliances
        # construct activity-type matrix
        act = pd.DataFrame(index=self.actCode.index,columns=self.actCode.columns)

        # get second tier activity codes
        actCodeSecondTier = self.actCode//100

        for state in range(len(self.activityStates)):
            act[actCodeSecondTier.isin(self.activitySecondTierCodes[state])] = state
            act[self.actCode.isin(self.activityCodes[state])] = state

        # fill remaining activities
        act[pd.isna(act)] = 8 

        # 0 - away... This will also remove all activities assigned above which are reported away from home
        act[self.occ == 0] = 0

        assert(pd.isna(self.occ).to_numpy().sum()==0)
        assert(pd.isna(act).to_numpy().sum()==0)

        return act

    def getDem(self):
        # New dataframe
        dem = pd.DataFrame(index=self.caseIds)

        # Only include respondent
        cps_sub = self.rawData['cps'][self.rawData['cps']['TULINENO'] == 1]

        # filter
        cps_sub = cps_sub.loc[self.caseIds]
        resp_sub = self.rawData['resp'].loc[self.caseIds]

        # populate dem file
        cpsVariables = ['HRHHID','HRHHID2','PULINENO','HRYEAR4','HRMONTH']
        respVariables = ['TUDIARYDAY']
        dem[cpsVariables] = cps_sub[cpsVariables]
        dem[respVariables] = resp_sub[respVariables]

        # add weekday flag
        dem['TUWEEKDAY'] = dem['TUDIARYDAY'].isin([2,3,4,5,6])

        return dem

    def getAppliances(self):
        app = self.act.applymap(lambda x: self.activityAppliances[x])
        power = self.act.applymap(lambda x: self.activityPowerRatings[x])

        return app, power

    def save(self):

        print('\t','...saving processed ATUS data')
        
        savedActFilename = os.path.join(ATUS.filepaths.processedDataDirectory,'processed-atus-act-{}-{}-min-res.csv'.format('-'.join([str(year) for year in self.years]),str(self.timeRes)))
        savedOccFilename = os.path.join(ATUS.filepaths.processedDataDirectory,'processed-atus-occ-{}-{}-min-res.csv'.format('-'.join([str(year) for year in self.years]),str(self.timeRes)))
        savedDemFilename = os.path.join(ATUS.filepaths.processedDataDirectory,'processed-atus-dem-{}.csv'.format('-'.join([str(year) for year in self.years])))
        
        self.act.to_csv(savedActFilename,index_label='TUCASEID')
        self.occ.to_csv(savedOccFilename,index_label='TUCASEID')
        self.dem.to_csv(savedDemFilename,index_label='TUCASEID')

    def activityPlot(self, ax, act, legend=True):
        
        numResp = float(len(act))
        numTS = len(self.timeStamps)
        numStates = len(self.activityStates)
        
        data = np.zeros((numStates,numTS))
        
        # find percentage of respondents engaging in each activity
        for state in range(numStates):
            data[state] = (act == state).sum()/numResp*100
        
        # aggregate
        for state in range(numStates):
            if state == 0:
                continue
            data[state] += data[state-1]
        
        # plot
        for state in range(numStates):
            if state == 0:
                ax.fill_between(self.timeStamps,0,data[state])
            else:
                ax.fill_between(self.timeStamps,data[state-1],data[state])
                
        #format
        if self.timeRes < 60:
            ax.set_xlim([datetime(2000,1,1,4,0,0),datetime(2000,1,2,3,60-self.timeRes,0)])
        ax.set_ylim([0,100])
        plt.gcf().autofmt_xdate()
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%H:%M:%S'))

        if legend:
            ax.legend([state for state in self.activityStates],loc=2, prop={'size': 6})
        ax.set_xlabel('Time of Day')
        ax.set_ylabel('% of Respondents Engaging in Activity')
        return ax

if __name__ == '__main__':
    a = ATUS()
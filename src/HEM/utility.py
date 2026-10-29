import pandas as pd
from datetime import datetime, timedelta

class utility():
    def __init__(self):
        pass
    
    @staticmethod
    def getNsrdbData(filepath):

        timeRes = 1

        data = pd.read_csv(filepath,skiprows=2,usecols=['Year',
                                                        'Month',
                                                        'Day',
                                                        'Hour',
                                                        'Minute',
                                                        'GHI',
                                                        'Temperature'])

        # set datetime index
        data['time'] = pd.to_datetime((data['Year']*int(1e10)+data['Month']*int(1e8)+data['Day']*int(1e6)+data['Hour']*int(1e4)+data['Minute']*int(1e2)).apply(str),
                                        format='%Y%m%d%H%M%S')
        data.drop(columns=['Year','Month','Day','Hour','Minute'],inplace=True)
        data.set_index('time',inplace=True)

        # resample
        data = data._append(pd.Series(name=datetime(data.index[0].year,12,31,23,59,0)))
        data = data.resample(timedelta(minutes=timeRes)).interpolate()  

        # fill na (necessary for last timestamp)
        data.pad(inplace=True)

        return data

    class convert():
        def __init__():
            pass 

        __incomeConversionTableC2I = [0, # 1
                                5000, # 2
                                7500, # 3
                                10000, # 4
                                12500, # 5
                                15000, # 6
                                20000, # 7
                                25000, # 8
                                30000, # 9
                                35000, # 10
                                40000, # 11
                                50000, # 12
                                60000, # 13
                                75000, # 14
                                100000, # 15
                                160000] # 16

        @staticmethod
        def cpsIncomeCode2income(cpsIncomeCode):
            '''map CPS 'hefaminc' variable code to household income ranges ($/year)'''
            return utility.convert.__incomeConversionTableC2I[cpsIncomeCode-1]

        @staticmethod
        def income2cpsIncomeCode(income):
            '''map income ($/year) to CPS 'hefaminc' variable code'''
            
            income = int(income)        

            for i in range(len(utility.convert.__incomeConversionTableC2I)-1):
                if income < utility.convert.__incomeConversionTableC2I[i+1]:
                    return i+1
            
            return len(utility.convert.__incomeConversionTableC2I)

        __incomeConversionTableI2R = [  0, # 1
                            20000, # 2
                            40000, # 3
                            60000, # 4
                            80000, # 5
                            100000, # 6
                            120000, # 7
                            150000] # 8

        @staticmethod
        def recsIncomeCode2income(recsIncomeCode):
            '''map CPS 'hefaminc' variable code to household income ranges ($/year)'''
            return utility.convert.__incomeConversionTableI2R[recsIncomeCode-1]


        @staticmethod
        def income2recsIncomeCode(income):
            '''map household income ($/year) to RECS 'moneypy' variable code'''
            
            income = int(income)        

            for i in range(len(utility.convert.__incomeConversionTableI2R)-1):
                if income < utility.convert.__incomeConversionTableI2R[i+1]:
                    return i+1
            
            return len(utility.convert.__incomeConversionTableI2R)

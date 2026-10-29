import numpy as np
import pandas as pd
import os, sys

localPath = os.path.dirname(__file__)

rng = np.random.default_rng()

# get cps data
cpsData = None

def getDemographics(households):
    cpsSubset = cpsData[cpsData['household'].isin(households)]
    populationSize = len(cpsSubset)
    
    demographics = pd.Series(dtype=np.float64)

    percent = lambda key,val: np.count_nonzero(cpsSubset[key] == val)/populationSize

    #age
    demographics['0-18'] = percent('age',0)
    demographics['19-64'] = percent('age',1)
    demographics['65+'] = percent('age',2)

    # occupation status
    demographics['Not in Labor Force'] = percent('occupation status',0) + percent('occupation status',pd.NA)
    demographics['Full Time'] = percent('occupation status',1)
    demographics['Part Time'] = percent('occupation status',2)
    
    # occupation category
    demographics['Management'] = percent('occupation category',1)
    demographics['Service'] = percent('occupation category',2)
    demographics['Sales'] = percent('occupation category',3)
    demographics['Farming/Fishing'] = percent('occupation category',4)
    demographics['Construction/Maintenance'] = percent('occupation category',5)
    demographics['Production/Transportation'] = percent('occupation category',6)
    demographics['Armed Forces'] = percent('occupation category',7)

    # parental status
    demographics['Parent'] = percent('parental status',1)
    demographics['Nonparent'] = percent('parental status',0)

    return demographics

def getStatistics(loc,householdsLoc):
    
    demographicsFilepath = os.path.join(outputDirectory,'analysis-demographics.csv')
    
    if not os.path.exists(demographicsFilepath):
        demographics = pd.DataFrame()

        demographics['{} sample'.format(loc)] = getDemographics(householdsLoc)
        #demographics['{} sample'.format(loc2)] = getDemographics(householdsLoc2)

        demographics.T.to_csv(demographicsFilepath)

def most_common(lst):

    return max(set(lst), key=lst.count)

def aggregate(households,incomes,household_num,ages,occup_status,occup_cat,City):

    # output dataFrames
    summary = pd.DataFrame()
    aggregate = 0
    incomeGroups = [0 for i in range(len(incomes))]
    incomeGroupCounts = [0 for i in range(len(incomes))]
    houseSizeGroups = [0 for i in range(len(household_num))]
    houseSizeGroupCounts = [0 for i in range(len(household_num))]
    ageGroups = [0 for i in range(len(ages))]
    ageGroupsCounts = [0 for i in range(len(ages))]
    Age_avg=[]
    
    OccupStatusGroups = [0 for i in range(len(occup_status))]
    OccupStatusGroupCounts = [0 for i in range(len(occup_status))]
    OccupStatus_avg=[]
    OccupCatGroups = [0 for i in range(len(occup_cat))]
    OccupCatGroupCounts = [0 for i in range(len(occup_cat))]    
    OccupCat_avg=[]
    CityGroups = [0 for i in range(len(City))]
    CityGroupCounts = [0 for i in range(len(City))]    
    City_avg=[]
    
    
    # iterate through households 
    for i,household in enumerate(households):

        print(i, household)

        # get output
        try:
            outputHousehold = pd.read_csv(os.path.join(outputDirectory,'output-household-{}.csv'.format(household)),index_col=0)
        except:
            continue 

        aggregate += outputHousehold.values

        # get summary
        subset = cpsData[cpsData['household'] == household]
        summaryHousehold = pd.Series(name=household,dtype=object)
        summaryHousehold['num occupants'] = len(subset)
        summaryHousehold['income'] = subset['family income'].iloc[0]
        summaryHousehold['AvgAge'] = np.mean(subset['age_act'])
        Age_avg.append(np.mean(subset['age_act']))
        summaryHousehold['OccupStatus'] = most_common(subset['occupation status'].tolist())
        OccupStatus_avg.append(most_common(subset['occupation status'].tolist()))
        summaryHousehold['OccupCategory'] = most_common(subset['occupation category'].tolist())
        OccupCat_avg.append(most_common(subset['occupation category'].tolist()))
        
        summaryHousehold['City'] = most_common(subset['city code'].tolist())
        if summaryHousehold['City'] in City:
            City_avg.append(most_common(subset['city code'].tolist()))
        #print(City_avg)

        for key in ['total (kWh)','space heating (kWh)','ac (kWh)','water heating (kWh)','lighting (kWh)','cold appliances (kWh)','other (kWh)']:
            summaryHousehold[key] = outputHousehold[key].sum()

        summary = summary.append(summaryHousehold)

        # add to demographic groups
        incomeGroupIdx = np.digitize(summaryHousehold['income'],incomes)-1
        incomeGroups[incomeGroupIdx] += outputHousehold.values
        incomeGroupCounts[incomeGroupIdx] += 1

        houseSizeIdx = int(max(min(summaryHousehold['num occupants'],5),1))-1
        houseSizeGroups[houseSizeIdx] += outputHousehold.values
        houseSizeGroupCounts[houseSizeIdx] += 1
 
        ageGroupIdx = np.digitize(summaryHousehold['AvgAge'],ages)-1
        ageGroups[ageGroupIdx] += outputHousehold.values
        ageGroupsCounts[ageGroupIdx] += 1 
        #householdNum=int(min(summaryHousehold['num occupants'],5))

        OccupStatusIdx = int(summaryHousehold['OccupStatus'])
        OccupStatusGroups[OccupStatusIdx] += outputHousehold.values
        OccupStatusGroupCounts[OccupStatusIdx] += 1
        
        OccupCatIdx = int(summaryHousehold['OccupCategory'])
        OccupCatGroups[OccupCatIdx] += outputHousehold.values
        OccupCatGroupCounts[OccupCatIdx] += 1
        
        if summaryHousehold['City'] in City:
            #print(np.digitize(summaryHousehold['City'],City))
            #print(summaryHousehold['City'])
            #print(City)
            print(np.digitize(summaryHousehold['City'],City))
            CityIdx = np.digitize(int(summaryHousehold['City']),City)-1
            print(CityIdx)
            CityGroups[CityIdx] += outputHousehold.values
            print(CityGroups[CityIdx])
            CityGroupCounts[CityIdx] += 1
        
    # convert to dataframe
    aggregate = pd.DataFrame(aggregate,outputHousehold.index,outputHousehold.columns)
    
    for i in range(len(incomeGroups)):
        incomeGroups[i] = pd.DataFrame(incomeGroups[i]/max(1,incomeGroupCounts[i]),outputHousehold.index,outputHousehold.columns)
        
    for i in range(len(houseSizeGroups)):
        houseSizeGroups[i] = pd.DataFrame(houseSizeGroups[i]/max(1,houseSizeGroupCounts[i]),outputHousehold.index,outputHousehold.columns)
        
    for i in range(len(ageGroups)):
        ageGroups[i] = pd.DataFrame(ageGroups[i]/max(1,ageGroupsCounts[i]),outputHousehold.index,outputHousehold.columns)
        
    for i in range(len(OccupStatusGroups)):
        OccupStatusGroups[i] = pd.DataFrame(OccupStatusGroups[i]/max(1,OccupStatusGroupCounts[i]),outputHousehold.index,outputHousehold.columns)

    for i in range(len(OccupCatGroups)):
        OccupCatGroups[i] = pd.DataFrame(OccupCatGroups[i]/max(1,OccupCatGroupCounts[i]),outputHousehold.index,outputHousehold.columns)
        
    for i in range(len(CityGroups)):
        CityGroups[i] = pd.DataFrame(CityGroups[i]/max(1,CityGroupCounts[i]),outputHousehold.index,outputHousehold.columns)

    return summary, aggregate, incomeGroups, houseSizeGroups,ageGroups ,Age_avg,OccupStatusGroups,OccupStatus_avg,OccupCatGroups,OccupCat_avg,CityGroups,City_avg

def main(analysis):
    
    #loc1 = 'CA'
    #loc2 = 'TX'
    #loc1Code = 6
    #loc2Code = 48
    
    #loc1='CA'
    #locCode=6
    #City_loc=[31080,41860, 41940]
    
    #loc1='WA'
    #locCode=53
    #City_loc=[28420,42660,44060] #Richland,Seattle,Spokane
    
    loc1='NC'
    locCode=37
    City_loc=[16740,39580,49180] #Charlotte,Raleigh,Winston-Salem

    global outputDirectory
    if analysis == 1:
        outputDirectory = os.path.join(localPath,'..','output-data','main-'+loc1)
    elif analysis == 2:
        outputDirectory = os.path.join(localPath,'..','output-data','main-CA'+loc1+'-house-size-2')
        
    

    global cpsData
    cpsData = pd.read_csv(os.path.join(outputDirectory,'output-cps-subset.csv'))
    
    # get california and texas households

    householdsLoc=pd.unique(cpsData['household'][cpsData['state'] == locCode])

    # get sample statistics
    #getStatistics(loc1,loc2, householdsLoc1,householdsLoc2)
    getStatistics(loc1, householdsLoc)

    # setup
    incomes = [0,25000,50000,75000,100000]
    household_num=[1,2,3,4,5]
    ages=[0,20,35,50,65]
    occup_status=[0,1,2,3]
    occup_cat=[0,1,2,3,4,5,6,7]
    #City_TX=[12420,19100, 26420] #Austin-Round Rock, TX 8,Dallas-Fort Worth-Arlington, TX 31, Houston-Baytown-Sugar Land, TX 23
    #City_CA=[31080,41860, 41940] #Los Angeles-Long Beach-Anaheim, CA 30, San Francisco-Oakland-Fremont, CA 16, San Jose-Sunnyvale-Santa Clara, CA 15

    # aggregate
    for loc, households in [(loc1,householdsLoc)]:

        City=City_loc

            
        summary, aggregated, incomeGroups, houseSizeGroups,ageGroups,Age_avg,OccupStatusGroups,OccupStatus_avg,OccupCatGroups,OccupCat_avg,CityGroups,City_avg = aggregate(households,incomes,household_num,ages,occup_status,occup_cat,City)
        # save Loc1
        summary.to_csv(os.path.join(outputDirectory,'analysis-summary-{}.csv'.format(loc)))
        aggregated.to_csv(os.path.join(outputDirectory,'analysis-aggregate-{}.csv'.format(loc)))
        for i,group in enumerate(incomeGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-income-{}-{}.csv'.format(incomes[i],loc)))
        for i,group in enumerate(houseSizeGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-house-size-{}-{}.csv'.format(i+1,loc)))
        for i,group in enumerate(ageGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-age-{}-{}.csv'.format(ages[i],loc)))
        for i,group in enumerate(OccupStatusGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-Occup-Status-{}-{}.csv'.format(occup_status[i],loc)))
        for i,group in enumerate(OccupCatGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-Occup-Category-{}-{}.csv'.format(occup_cat[i],loc))) 
        for i,group in enumerate(CityGroups):
            group.to_csv(os.path.join(outputDirectory,'analysis-City-{}-{}.csv'.format(City[i],loc))) 
 
        pd.DataFrame(Age_avg).to_csv(os.path.join(outputDirectory,'analysis-averageage-{}.csv'.format(loc)))
        pd.DataFrame(OccupStatus_avg).to_csv(os.path.join(outputDirectory,'analysis-averageoccupstatus-{}.csv'.format(loc)))
        pd.DataFrame(OccupCat_avg).to_csv(os.path.join(outputDirectory,'analysis-averageoccupcategory-{}.csv'.format(loc)))
        pd.DataFrame(City_avg).to_csv(os.path.join(outputDirectory,'analysis-averagecity-{}.csv'.format(loc)))
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        pass
    elif sys.argv[1] == '--analysis1':
        main(1)
    elif sys.argv[1] == '--analysis2':
        main(2)
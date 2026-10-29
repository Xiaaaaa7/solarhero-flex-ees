# -*- coding: utf-8 -*-
"""
Created on Fri May  9 17:10:15 2025
@author: jwang4
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import scipy.io
import time
from datetime import datetime, timedelta

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

start_time = time.time()   # 记录开始时间

#State='MN' CA TX  FL TX NY
State='PA'

#Dire=r'D:\AIM_Project\SULI_Isaac_Summer2021\SULI_Isaac_Summer2021\output-data\main-'+State+'\\'
Dire=r'F:\E PhD\Heat map(2025)\main-'+State+'_winter\\'

#Dire_temp=r'D:\AIM_Project\SULI_Isaac_Summer2021\SULI_Isaac_Summer2021\raw-data\nsrdb\\minnesota-'+State.lower()+'-2019-5-min-nsrdb.csv'
#Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\SaintPaul-'+State.lower()+'-2023-5-min-nsrdb.csv'
#Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\Sacramento-'+State.lower()+'-2023-5-min-nsrdb.csv'
#Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\Austin-'+State.lower()+'-2023-5-min-nsrdb.csv'
#Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\Tallahassee-'+State.lower()+'-2023-5-min-nsrdb.csv'
#Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\Albany-'+State.lower()+'-2023-5-min-nsrdb.csv'
Dire_temp=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb\\Harrisburg-'+State.lower()+'-2023-5-min-nsrdb.csv'

#Dire_output=r'D:\Solarhero\Survey\Flexibility_plot\Output\\'
Dire_output=r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\Flexibility_plot\\'

cps_info=pd.read_csv(Dire+'output-cps-subset-'+State+'.csv')

month=12 #6 8

temp_5min=pd.read_csv(Dire_temp,skiprows=2)

temp_hour=np.zeros(8760)

for i in range(0,8760):
    
    temp_hour[i]=np.mean(temp_5min['Temperature'][i*12:(i+1)*12])


house_list=cps_info['household'].unique()

print(datetime.now())

house_profiles=pd.DataFrame()

for i in range(0,len(house_list)):
    
    if i%10==0:
        print(i)
        
        print(datetime.now())
    
    house_data=pd.read_csv(Dire+'output-household-'+str(house_list[i])+'.csv')
    
    house_1min=np.array(house_data['total (kWh)'])*60
    
    house_1min[-9:]=0.2
    
    house_15min=np.zeros(35040)
    
    for j in range(0,35040):
        
        house_15min[j]=np.mean(house_1min[j*15:(j+1)*15])
        
    house_profiles[i]=house_15min
    

utility_input=np.zeros((len(house_list),24,30))  #########
original_load=np.zeros((len(house_list),24))

for i in range(0,len(house_list)):
    
    test_mid=np.zeros((24,30))
    
    ls_mid=house_profiles[i]
    
    for j in range(0,30):
        
        if j!=29:
        
            for t in range(0,24):
                test_mid[t][j]=np.mean(ls_mid[(month-1)*96*30+j*96+t*4:(month-1)*96*30+j*96+t*4+4])
                
                
        else:
            
            for t in range(0,24):
                test_mid[t][j]=temp_hour[(month-1)*24*30+j*24+t]
                original_load[i,t]=np.mean(ls_mid[(month-1)*96*30+j*96+t*4:(month-1)*96*30+j*96+t*4+4])
                
            
            
    utility_input[i]=test_mid    
    
print(datetime.now())
        # tt=tt+1

# house_profiles.to_csv('P_total_synthetic.csv')    

from tensorflow.keras.models import load_model
#model = load_model(r"E:\PhD\2025heat map\SULI_Isaac_Summer2021\Flexibility_Envelope_Code\lstm_model_synthetic_state.keras")
model = load_model(r"E:\PhD\2025heat map\SULI_Isaac_Summer2021\Flexibility_Envelope_Code\lstm_model_synthetic_state_winter.keras")
#model = load_model("lstm_model_synthetic_state.keras")

utilityPredict = model.predict(utility_input)

upper_rec=pd.DataFrame()
lower_rec=pd.DataFrame()

flag=0

for i in range(0,len(utility_input)):

# upper_rec[i]+original_load[i]
    upper_rec[i]=utilityPredict[i][:,0]
    lower_rec[i]=utilityPredict[i][:,1]
    
    upper_rec[i][upper_rec[i]<0]=0
    lower_rec[i][lower_rec[i]<0]=0
    
    upper_rec[i]=upper_rec[i]+original_load[i]
    
    
for i in range(0,len(utility_input)):
    
    for j in range(0,24):
        
        if upper_rec[i][j]-lower_rec[i][j]<0:
            
            upper_rec[i][j]=lower_rec[i][j]
            
        # if upper_rec[i][j]<original_load[i][j]:
            
        #     upper_rec[i][j]=original_load[i][j]
        
            
        if lower_rec[i][j]>original_load[i][j]:
            
            lower_rec[i][j]=original_load[i][j]

# for i in range(0,100):
#     plt.rcParams.update({'font.size': 60}) 
#     fig, ax = plt.subplots(1,1,figsize=(32,16))
#     plt.plot(upper_rec[i],'r',linewidth=10)
#     plt.plot(lower_rec[i],'r',linewidth=10)   
#     # plt.plot(Load_total,'r',linewidth=10)  
#     plt.plot(original_load[i],'b',linewidth=10) 
#     plt.legend()
#     plt.xlabel('Hour')
#     plt.ylabel('Load [kW]') 
#     # plt.title('Total Flexibility '+State1)
#     plt.grid(True, linewidth=3)
#     plt.show()            

pd.DataFrame(lower_rec).to_csv(Dire_output+'Output_lower_bound_'+State+'_12.csv')
pd.DataFrame(upper_rec).to_csv(Dire_output+'Output_upper_bound_'+State+'_12.csv')
pd.DataFrame(original_load.T).to_csv(Dire_output+'Original_load_'+State+'_12.csv')

end_time = time.time()     # 记录结束时间
print("运行时间: {:.2f} 秒".format(end_time - start_time))


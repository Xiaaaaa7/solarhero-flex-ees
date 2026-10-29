# -*- coding: utf-8 -*-
"""
原始核心计算保持不变；仅修改：
- 文件读取：按50州自动定位目录与温度CSV
- 文件存储：写入 Dire_output/<month>/ 子目录，文件名带月份
- 批量循环：遍历全部50州（缺文件跳过）
- 统计总运行时间
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import scipy.io
from datetime import datetime, timedelta
import time  # 新增：运行时间
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# ========================= 基础配置（保持与原版一致的变量名） =========================
# 仅用于构造路径的“模板根目录”；真正的 State 会在循环中逐一赋值
Dire_output = r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\Flexibility_plot\\'
base_main_dir = r'F:\E PhD\Heat map(2025)'
base_temp_dir = r'E:\PhD\2025heat map\SULI_Isaac_Summer2021\raw-data\nsrdb'

# 月份（保持你的原逻辑，按 30 天处理）
month = 6  # 例如 8 月

# 50州：州缩写 -> 城市（与温度CSV命名一致）
state_to_city = {
    "AL":"Montgomery","AK":"Juneau","AZ":"Phoenix","AR":"LittleRock","CA":"Sacramento",
    "CO":"Denver","CT":"Hartford","DE":"Dover","FL":"Tallahassee","GA":"Atlanta",
    "HI":"Honolulu","ID":"Boise","IL":"Springfield","IN":"Indianapolis","IA":"DesMoines",
    "KS":"Topeka","KY":"Frankfort","LA":"BatonRouge","ME":"Augusta","MD":"Annapolis",
    "MA":"Boston","MI":"Lansing","MN":"SaintPaul","MS":"Jackson","MO":"JeffersonCity",
    "MT":"Helena","NE":"Lincoln","NV":"CarsonCity","NH":"Concord","NJ":"Trenton",
    "NM":"SantaFe","NY":"Albany","NC":"Raleigh","ND":"Bismarck","OH":"Columbus",
    "OK":"OklahomaCity","OR":"Salem","PA":"Harrisburg","RI":"Providence","SC":"Columbia",
    "SD":"Pierre","TN":"Nashville","TX":"Austin","UT":"SaltLakeCity","VT":"Montpelier",
    "VA":"Richmond","WA":"Olympia","WV":"Charleston","WI":"Madison","WY":"Cheyenne"  #AK HI / WI WV WY
}

# 输出子目录：按月份创建
month_str = str(month)
output_dir = os.path.join(Dire_output, month_str)
os.makedirs(output_dir, exist_ok=True)

# 计时（总）
start_time = time.time()

# ========================= 遍历全部 50 州 =========================
for State in state_to_city.keys():
    try:
        state_code = State  # 保持原变量名语义
        state_lower = State.lower()
        city = state_to_city[State]

        # ------- 构造输入路径（仅修改读取部分；核心计算不变） -------
        Dire = rf'{base_main_dir}\main-{state_code}_winter\\'
        Dire_temp = os.path.join(base_temp_dir, f'{city}-{state_lower}-2023-5-min-nsrdb.csv')

        cps_path = os.path.join(Dire, f'output-cps-subset-{state_code}.csv')
        if not os.path.isfile(cps_path):
            print(f"[跳过] 缺少 {cps_path}")
            continue
        if not os.path.isfile(Dire_temp):
            print(f"[跳过] 缺少温度文件 {Dire_temp}")
            continue

        # ========================= 以下为“原始核心计算”，未改动 =========================
        cps_info = pd.read_csv(cps_path)

        temp_5min = pd.read_csv(Dire_temp, skiprows=2)

        temp_hour = np.zeros(8760)
        for i in range(0, 8760):
            temp_hour[i] = np.mean(temp_5min['Temperature'][i*12:(i+1)*12])

        house_list = cps_info['household'].unique()

        print(f"\n=== {state_code} 开始: {datetime.now()} ===")

        house_profiles = pd.DataFrame()

        for i in range(0, len(house_list)):

            if i % 10 == 0:
                print(i)
                print(datetime.now())

            house_data = pd.read_csv(os.path.join(Dire, f'output-household-{str(house_list[i])}.csv'))

            house_1min = np.array(house_data['total (kWh)']) * 60

            house_1min[-9:] = 0.2

            house_15min = np.zeros(35040)

            for j in range(0, 35040):
                house_15min[j] = np.mean(house_1min[j*15:(j+1)*15])

            house_profiles[i] = house_15min

        utility_input = np.zeros((len(house_list), 24, 30))
        original_load = np.zeros((len(house_list), 24))

        for i in range(0, len(house_list)):

            test_mid = np.zeros((24, 30))

            ls_mid = house_profiles[i]

            for j in range(0, 30):

                if j != 29:

                    for t in range(0, 24):
                        test_mid[t][j] = np.mean(ls_mid[(month-1)*96*30 + j*96 + t*4:(month-1)*96*30 + j*96 + t*4 + 4])

                else:

                    for t in range(0, 24):
                        test_mid[t][j] = temp_hour[(month-1)*24*30 + j*24 + t]
                        original_load[i, t] = np.mean(ls_mid[(month-1)*96*30 + j*96 + t*4:(month-1)*96*30 + j*96 + t*4 + 4])

            utility_input[i] = test_mid

        print(datetime.now())

        from tensorflow.keras.models import load_model
        model = load_model(r"E:\PhD\2025heat map\SULI_Isaac_Summer2021\Flexibility_Envelope_Code\lstm_model_synthetic_state.keras")

        utilityPredict = model.predict(utility_input)

        upper_rec = pd.DataFrame()
        lower_rec = pd.DataFrame()

        flag = 0

        for i in range(0, len(utility_input)):

            # upper_rec[i]+original_load[i]
            upper_rec[i] = utilityPredict[i][:, 0]
            lower_rec[i] = utilityPredict[i][:, 1]

            upper_rec[i][upper_rec[i] < 0] = 0
            lower_rec[i][lower_rec[i] < 0] = 0

            upper_rec[i] = upper_rec[i] + original_load[i]

        for i in range(0, len(utility_input)):

            for j in range(0, 24):

                if upper_rec[i][j] - lower_rec[i][j] < 0:
                    upper_rec[i][j] = lower_rec[i][j]

                if lower_rec[i][j] > original_load[i][j]:
                    lower_rec[i][j] = original_load[i][j]

        # ========================= 以上为“原始核心计算”，未改动 =========================

        # ------- 存储部分（仅修改输出路径与文件名） -------
        out_lower = os.path.join(output_dir, f'Output_lower_bound_{state_code}_{month_str}.csv')
        out_upper = os.path.join(output_dir, f'Output_upper_bound_{state_code}_{month_str}.csv')
        out_orig  = os.path.join(output_dir, f'Original_load_{state_code}_{month_str}.csv')

        pd.DataFrame(lower_rec).to_csv(out_lower, index=False)
        pd.DataFrame(upper_rec).to_csv(out_upper, index=False)
        pd.DataFrame(original_load.T).to_csv(out_orig, index=False)

        print(f"[保存] {out_lower}")
        print(f"[保存] {out_upper}")
        print(f"[保存] {out_orig}")

    except Exception as e:
        print(f"[错误] 处理 {State} 时失败：{e}")

# 计时（总）
end_time = time.time()
print("\n全部州处理完成。")
print(f"总运行时间: {end_time - start_time:.2f} 秒 （约 {int((end_time-start_time)//60)} 分 {((end_time-start_time)%60):.1f} 秒）")

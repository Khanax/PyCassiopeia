#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 13:32:40 2019

@author: stergios
"""

import os
import time
import statistics as stats

import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from matplotlib import cm

from .utils import windowUnits,EPS,ACC_THRESHOLD
import include.network.net_constants as netco


def cycleWindow(_data_df,features_list,window_settings,model_path):
    begin = time.time()

    #exit setting
    w_size = window_settings[0]
    w_step = window_settings[1]
    print(50*"-")
    print("~$> Initializing Window Making Processing for Engine Cycles")
    print(50*"-")
    print("~$> Window size",w_size,"seconds.")
    print("~$> Window step",w_step,"seconds.")
    print(50*"-")
    fit_df = pd.DataFrame(columns=features_list)
    # [Finding maximum count of correct length windows]
    w_count = windowUnits(len(_data_df),w_size,w_step)

    print("~$> Total Windows Progression")
    for cycle in _data_df:
        cycle_df = _data_df[cycle]
        w_start = 0
        w_end = w_size
        Cycle_Final = pd.DataFrame()
        with tqdm(total = w_count,desc = "~$> ",unit="win") as pbar:
            for window in range(cycle_df.index.min(),cycle_df.index.max(),w_step):
                window_df = cycle_df[w_start:w_end]
                if len(window_df)!=w_size:
                    continue
                window_df = window_df.reset_index(drop=True)
                # Checking for values below EPS and making them zero.
                window_df = window_df.apply(lambda x: x if x > EPS else 0)
                # Initializing the counters
                acc_list = []
                dec_list = []
                counter_P_N_030 = 0
                counter_P_N_3050 = 0
                counter_P_N_5070 = 0
                counter_P_N_70100 = 0
                counter_P_D_12 = 0
                counter_P_D_23 = 0
                for time_step in window_df.index:
                    if window_df[time_step]<=0.30:
                        counter_P_N_030+=1
                    elif 0.30<window_df[time_step] and window_df[time_step]<0.50:
                        counter_P_N_3050+=1
                    elif 0.50<window_df[time_step] and window_df[time_step]<0.70:
                        counter_P_N_5070+=1
                    else:
                        counter_P_N_70100+=1
                    if time_step==0:
                        pass
                    else:
                        acc = window_df[time_step]-window_df[time_step-1]
                        if acc > 0:
                            acc_list.append(acc)
                        else:
                            dec_list.append(acc)
                            if acc<-0.05:
                                counter_P_D_12+=1
                            if -0.05<acc<-0.01:
                                counter_P_D_23+=1
                if len(dec_list) == 0:
                    ave_win_dec = 0
                    max_win_dec = 0
                else:
                    ave_win_dec = stats.mean(dec_list)
                    max_win_dec = min(dec_list)

                if len(acc_list) == 0:
                    ave_win_acc = 0
                    max_win_acc = 0
                    std_win_acc = 0
                elif len(acc_list) == 1:
                    std_win_acc == 0
                else:
                    ave_win_acc = stats.mean(acc_list)
                    max_win_acc = max(acc_list)
                    std_win_acc = stats.stdev(acc_list)
                Cycle_Final = Cycle_Final.append({
                'LABEL': cycle,
                'N_MAX': round(window_df.max(),4),
                'N_AVE': round(window_df.mean(),4),
                'A_MAX': round(max_win_acc,4),
                'A_AVE': round(ave_win_acc,4),
                'A_STD': round(std_win_acc,4),
                'D_MAX': round(max_win_dec,4),
                'D_AVE': round(ave_win_dec,4),
                'P_N_030': round(counter_P_N_030/len(window_df),4),
                'P_N_3050': round(counter_P_N_3050/len(window_df),4),
                'P_N_5070': round(counter_P_N_5070/len(window_df),4),
                'P_N_70100':round(counter_P_N_70100/len(window_df),4)
                #'P_D_12':1,
                #'P_D_23':1
                },ignore_index=True)
                prev_cycle = cycle
                w_start+=w_step
                w_end+=w_step
                pbar.update(n=1)
            Cycle_Final = Cycle_Final.astype({'LABEL': int})
        fit_df = fit_df.append(Cycle_Final,sort=False,ignore_index=True)

    print(50*"-")    
    print("~$> Plotting Pearson Correlation Matrix")

    correlations = fit_df[fit_df.columns].corr(method='pearson')
    heat_ax = sns.heatmap(correlations, cmap="YlGnBu", annot = True)
    plt.show(block=False)
    if not os.path.exists(model_path): os.makedirs(model_path)
    fit_df.to_csv(model_path+"/"+netco.TRAINING+".csv",index=False)

    finish = time.time()
    print(50*"-")
    print("~$> Time for data process was",round(finish-begin,2),"seconds.")
    print(50*"-")

def trendWindow(_data_df,features_list,measurements,window_settings,model_path):
    begin = time.time()

    #exit setting
    w_size = window_settings[0]
    w_step = window_settings[1]
    print(50*"-")
    print("~$> Initializing Window Making Processing for Speed Trend Prediction")
    print(50*"-")
    print("~$> Window size",w_size,"seconds.")
    print("~$> Window step",w_step,"seconds.")
    print(50*"-")
    
    # [Finding maximum count of correct length windows]
    w_count = windowUnits(len(_data_df),w_size,w_step)
    fit_df = pd.DataFrame(columns=features_list)
    w_start = 0
    w_end = w_size
    print("~$> Total Windows Progression")
    with tqdm(total = w_count,desc = "~$> ",unit="win") as pbar:
        for window in range(_data_df.index.min(),_data_df.index.max(),w_step):
            window_df = _data_df[w_start:w_end]
            if len(window_df)!=w_size:
                continue
            window_df = window_df.reset_index(drop=True)
            win_accs = []
            for time_step in window_df.index:
                if time_step==0:
                    pass
                else:
                    acc = window_df[measurements[0]][time_step]-window_df[measurements[0]][time_step-1]
                    win_accs.append(acc)
            ave_win_acc = round(stats.mean(win_accs),4)
            max_win_revs = round(window_df[measurements[0]].max(),4)
            min_win_revs = round(window_df[measurements[0]].min(),4)
            ave_win_revs = round(window_df[measurements[0]].mean(),4)
            in_win_revs = round(window_df[measurements[0]][window_df.index.min()],4)
            out_win_revs = round(window_df[measurements[0]][window_df.index.max()],4)
            if w_start == 0:
                label = 1 #Starting with Steady
                prev_label = label
            else:
                if (ave_win_revs==0 and max_win_revs==0 and min_win_revs==0):
                    label = 0 #Dead Stop
                elif (ave_win_revs<0.5 and ave_win_acc<ACC_THRESHOLD and ave_win_acc>-ACC_THRESHOLD):
                    label = 1 #Low Speed Steady
                elif (ave_win_revs>0.5 and ave_win_acc<ACC_THRESHOLD and ave_win_acc>-ACC_THRESHOLD):
                    label = 2 #High Speed Steady
                elif (ave_win_acc>=ACC_THRESHOLD):
                    label = 3 #Acceleration
                elif (ave_win_acc<=-ACC_THRESHOLD):
                    label = 4 #Deceleration
            fit_df = fit_df.append({
                'LABEL': prev_label,
                'N_MAX': max_win_revs,
                'N_MIN': min_win_revs,
                'N_AVE': ave_win_revs,
                'N_IN' : in_win_revs,
                'N_OUT': out_win_revs,
                'A_AVE': ave_win_acc
                },ignore_index=True)
            w_start+=w_step
            w_end+=w_step
            prev_label = label
            pbar.update(n=1)  
    print(50*"-")    
    print("~$> Plotting Pearson Correlation Matrix")
    correlations = fit_df[fit_df.columns].corr(method='pearson')
    heat_ax = sns.heatmap(correlations, cmap="YlGnBu", annot = True)
    plt.show(block=False)
    if not os.path.exists(model_path): os.makedirs(model_path)
    fit_df.to_csv(model_path+"/"+netco.TRAINING+".csv",index=False)

    finish = time.time()
    print(50*"-")
    print("~$> Time for data process was",round(finish-begin,2),"seconds.")
    print(50*"-")
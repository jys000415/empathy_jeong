# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 15:51:09 2021

@author: jacobdahan
"""

import os
import time
import operator
import datetime
import numpy as np
import pandas as pd
import seaborn as sns 
from scipy import stats
from handler import grab_files
from annotator import annotate
import matplotlib.pyplot as plt
from classes import Statistics, InterpolatedAnalysis
from statsmodels.stats.multicomp import pairwise_tukeyhsd

class AnalysisStruct():
    
    def __init__(self,**kwargs):
        self.Set(**kwargs)
        
    def Set(self,**kwargs):
        self.__dict__.update(kwargs)
        
    def SetAttr(self,lab,val):
        self.__dict__[lab] = val

def gen_stats(df,mousetype):
    statistics    = dict()
    for cue_status in set(df.index):
        anova        = stats.f_oneway(*[df.loc[cue_status,cue_type].values for cue_type in df.columns])
        df_melt      = pd.melt(df.loc[cue_status].reset_index(),id_vars=['CueStatus'],value_vars=df.columns)
        tukeyhsd     = pairwise_tukeyhsd(endog=df_melt.value,groups=df_melt.variable,alpha=0.05)
        tukeyhsd_df  = pd.DataFrame(data=tukeyhsd._results_table.data[1:],\
                                    columns=tukeyhsd._results_table.data[0]) 
        statistics[cue_status] = Statistics(mousetype,anova.statistic,anova.pvalue,tukeyhsd_df) 
    return statistics

def label_trials(df,cue_duration=30):
    df['TrialNumber'] = np.nan
    non_nan_df        = df[~df.CueStatus.isnull()].copy()
    trial_endings     = np.array(list(np.where(non_nan_df.CueStatus.diff() < 0))).flatten()
    trial_endings     = np.append(trial_endings,len(non_nan_df.index))
    previous_end      = 0
    for trial,end in enumerate(trial_endings):
        non_nan_df['TrialNumber'].iloc[previous_end:end] = trial
        previous_end = end
    df.loc[~df.CueStatus.isnull()] = non_nan_df
    return df
       
def slice_df_by_cue(df,cue_id,cue_duration=30):
    epoch_size    = int((cue_duration / 2) / 0.001)
    cue_idxs      = np.where(df.Cue==cue_id)[0]
    pre_cue_idxs  = np.setdiff1d((cue_idxs - epoch_size), cue_idxs)
    post_cue_idxs = np.setdiff1d((cue_idxs + epoch_size), cue_idxs)
    slice_idx     = np.concatenate((pre_cue_idxs,cue_idxs,post_cue_idxs))
    cue_df        = df.iloc[slice_idx].sort_index(inplace=False)
    return cue_df

def freezing_by_cue_status(df,baseline_freezing,normalization):
    if normalization == 'baseline':
        pre_cue_freezing  = df[df.CueStatus==-1].Freezing.mean() - baseline_freezing
        cue_freezing      = df[df.CueStatus==0].Freezing.mean() - baseline_freezing
        post_cue_freezing = df[df.CueStatus==1].Freezing.mean() - baseline_freezing
    elif normalization == 'pre':
        pre_cue_df                 = df[df.CueStatus==-1].copy()
        pre_cue_freezing_by_trial  = pre_cue_df.groupby(['TrialNumber'])['Freezing'].mean()
        pre_cue_freezing           = np.mean(pre_cue_freezing_by_trial - pre_cue_freezing_by_trial)
        cue_df                     = df[df.CueStatus==0].copy()
        cue_freezing_by_trial      = cue_df.groupby(['TrialNumber'])['Freezing'].mean()
        cue_freezing               = np.mean(cue_freezing_by_trial - pre_cue_freezing_by_trial)
        post_cue_df                = df[df.CueStatus==1].copy()
        post_cue_freezing_by_trial = post_cue_df.groupby(['TrialNumber'])['Freezing'].mean()
        post_cue_freezing          = np.mean(post_cue_freezing_by_trial - pre_cue_freezing_by_trial)
    else:
        pre_cue_freezing  = df[df.CueStatus==-1].Freezing.mean()
        cue_freezing      = df[df.CueStatus==0].Freezing.mean()
        post_cue_freezing = df[df.CueStatus==1].Freezing.mean()

    return {'Pre':pre_cue_freezing,
            'Cue':cue_freezing,
            'Post':post_cue_freezing}

def interpolate_data(cue_csv,anymaze_csv,normalization):
    cue_df                    = pd.read_csv(cue_csv,header=None).transpose()
    cue_df.columns            = ['Cue','Time']
    max_time                  = cue_df.Time.max() + 60
    cue_df                    = pd.concat([pd.DataFrame({'Cue':np.nan,'Time':0.000},index=[0]), 
                                           cue_df,
                                           pd.DataFrame({'Cue':np.nan,'Time':max_time},
                                                        index=[-1])]).reset_index(drop = True)
    cue_df.Time               = cue_df.Time.apply(lambda x:time.strftime('%H:%M:%S.{}'.format(("%.3f" % x).split('.')[1]), time.gmtime(x)))
    cue_df.Time               = pd.to_datetime(cue_df.Time)
    cue_df                    = cue_df.set_index(cue_df.Time, inplace=False)
    interp_cue_df             = cue_df.resample('L').asfreq().Cue.rename_axis('Time').reset_index(level=0, inplace=False)
    cue_duration              = 30
    nans_to_fill              = int(cue_duration / 0.001 - 1)
    epoch_size                = int((cue_duration / 2) / 0.001)
    interp_cue_df.Cue         = interp_cue_df.Cue.interpolate(method='pad',limit=nans_to_fill)
    cue_status                = np.full_like(interp_cue_df.Cue, np.nan, dtype=np.double)
    cue_idxs                  = np.where(interp_cue_df.Cue.notnull())[0]
    pre_cue_idxs              = np.setdiff1d((cue_idxs - epoch_size), cue_idxs)
    post_cue_idxs             = np.setdiff1d((cue_idxs + epoch_size), cue_idxs)
    cue_status[cue_idxs]      = 0
    cue_status[pre_cue_idxs]  = -1
    cue_status[post_cue_idxs] = 1
    interp_cue_df['CueStatus']= cue_status
    anymaze_df                = pd.read_csv(anymaze_csv)
    anymaze_df                = pd.concat([anymaze_df,
                                           pd.DataFrame({'Time':cue_df.Time.max(),
                                                         'Freezing':anymaze_df.Freezing.iloc[-1],
                                                         'Not freezing':anymaze_df['Not freezing'].iloc[-1]},
                                                          index=[-1])]).reset_index(drop = True)
    anymaze_df.Time           = pd.to_datetime(anymaze_df.Time)
    anymaze_df                = anymaze_df[(anymaze_df.Time <= cue_df.Time.max())].reset_index(level=0, inplace=False)
    anymaze_df                = anymaze_df.set_index(anymaze_df.Time, inplace=False)
    interp_anymaze_df         = anymaze_df.resample('L').pad().Freezing.rename_axis('Time').reset_index(level=0, inplace=False)
    interp_concat_df          = pd.merge(interp_cue_df, interp_anymaze_df, on='Time')
    interp_concat_df          = interp_concat_df.drop(interp_concat_df.tail(1).index,inplace=False)
    interp_concat_df          = label_trials(interp_concat_df.copy())
    baseline_end              = pd.to_datetime('{}:{}:{}.{}'.format('00','05','00','00')) - datetime.timedelta(seconds=15)
    baseline_df               = interp_concat_df[interp_concat_df.Time < baseline_end]
    baseline_freezing         = baseline_df.Freezing.mean()
    cs_minus_df               = slice_df_by_cue(interp_concat_df,0)
    cs_one_df                 = slice_df_by_cue(interp_concat_df,1)
    cs_two_df                 = slice_df_by_cue(interp_concat_df,2)
    cs_minus_freezing         = freezing_by_cue_status(cs_minus_df,baseline_freezing,normalization)
    cs_one_freezing           = freezing_by_cue_status(cs_one_df,baseline_freezing,normalization)
    cs_two_freezing           = freezing_by_cue_status(cs_two_df,baseline_freezing,normalization)
    mousetype                 = 'Experienced' if 'Experienced' in cue_csv else 'Naive'
    return InterpolatedAnalysis(mousetype,
                                pd.DataFrame({'CS-':cs_minus_freezing,'CS+1':cs_one_freezing,'CS+2':cs_two_freezing}))

def plot_and_store(interpolated_data,virus,normalization,savepath):
    palette = {'CS-'  : 'black',
               'CS+1' : 'fuchsia',
               'CS+2' : 'gold'}
    # try:
    #     experienced_data            = list(map(operator.attrgetter('data'),\
    #                                        filter(lambda x: x.mousetype == 'Experienced',\
    #                                        interpolated_data)))
    #     experienced_data            = pd.concat(experienced_data)
    #     experienced_data.index.name = 'CueStatus'
    #     if normalization == '':
    #         experienced_data            = experienced_data.multiply(100)
    #     experienced_stats           = gen_stats(experienced_data,'Experienced')
    #     experienced_melt            = pd.melt(experienced_data.reset_index(),id_vars=['CueStatus'],\
    #                                           value_vars=experienced_data.columns)
    #     experienced_melt.columns    = ['CueStatus','CueType','Value']
    #     fig, ax = plt.subplots()
    #     sns.barplot(x='CueStatus',y='Value',hue='CueType',data=experienced_melt,\
    #                 hue_order=['CS-','CS+1','CS+2'],order=['Pre','Cue','Post'],\
    #                 palette=palette,ax=ax,ci=68)
    #     sns.swarmplot(x='CueStatus',y='Value',hue='CueType',data=experienced_melt,\
    #                 hue_order=['CS-','CS+1','CS+2'],order=['Pre','Cue','Post'],\
    #                 color='black',edgecolor='black',dodge=True)
    #     annotate(ax,experienced_melt,experienced_stats)
    #     if normalization == '':
    #         ax.set(xlabel='Cue Status',ylabel='% Freezing')
    #         ax.set(ylim=(0,140))
    #         ax.set(yticks=[0,20,40,60,80,100])
    #     else:
    #         ax.set(xlabel='Cue Status',ylabel='Time Freezing (norm.)')
    #         ax.set(ylim=(-2,20))
    #         ax.set(yticks=[0,4,8,12,16,20])
    #     if savepath == '':
    #         plt.savefig('./experienced_{}.svg'.format(virus))
    #     else:
    #         plt.savefig(os.path.join(savepath,'experienced_{}.svg'.format(virus)))
    # except:
    #     experienced_data = None
    # try:
    naive_data            = list(map(operator.attrgetter('data'),\
                                 filter(lambda x: x.mousetype == 'Naive',\
                                        interpolated_data)))
    naive_data            = pd.concat(naive_data)
    print(naive_data)
    naive_data.index.name = 'CueStatus'
    if normalization == '':
        naive_data            = naive_data.multiply(100)
    naive_melt            = pd.melt(naive_data.reset_index(),id_vars=['CueStatus'],\
                                          value_vars=naive_data.columns)
    naive_melt.columns    = ['CueStatus','CueType','Value']
    fig, ax = plt.subplots()
    sns.barplot(x='CueStatus',y='Value',hue='CueType',data=naive_melt,\
                hue_order=['CS-','CS+1','CS+2'],order=['Pre','Cue','Post'],\
                palette=palette,ax=ax,ci=68)
    sns.swarmplot(x='CueStatus',y='Value',hue='CueType',data=naive_melt,\
                hue_order=['CS-','CS+1','CS+2'],order=['Pre','Cue','Post'],\
                color='black',edgecolor='black',dodge=True)
    if len(interpolated_data) > 1:
        naive_stats  = gen_stats(naive_data,'Experienced')
        annotate(ax,naive_melt,naive_stats)
    if normalization == '':
        ax.set(xlabel='Cue Status',ylabel='% Freezing')
        ax.set(ylim=(0,140))
        ax.set(yticks=[0,20,40,60,80,100])
    else:
        ax.set(xlabel='Cue Status',ylabel='Time Freezing (norm.)')
        ax.set(ylim=(-0.5,1))
        ax.set(yticks=list(np.linspace(-0.5,1,7)))
    if savepath == '':
        plt.savefig('./naive_{}.svg'.format(virus))
    else:
        plt.savefig(os.path.join(savepath,'naive_{}.svg'.format(virus)))
    # except:
    #     naive_data = None
    
def analyze_anymaze(virus='',normalization='',savepath=''):
    cue_csvs, anymaze_csvs = grab_files()
    interpolated_data    = list()
    for cue_csv,anymaze_csv in zip(cue_csvs,anymaze_csvs):
        interpolated_data.append(interpolate_data(cue_csv,anymaze_csv,normalization))
    plot_and_store(interpolated_data,virus,normalization,savepath)
    
analyze_anymaze('test','pre','J:\\Jacob Dahan\\Lab Meeting\\PR2\\Data\\Plots')
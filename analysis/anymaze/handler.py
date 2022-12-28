# -*- coding: utf-8 -*-

import os
import re
import glob
import operator
import numpy as np
import PySimpleGUI as sg
from pathlib import Path
from classes import File

def open_window(title,layout,w,h):
    sg.theme('BlueMono')  
    window = sg.Window(title,layout,finalize=True,size=(w,h), 
                       element_justification='center')
    return window

def match_csvs(cue_csvs, anymaze_csvs):
    # cue_timing_files = list(map(File,cue_csvs,list(map(lambda x: os.path.basename(os.path.dirname(x)),cue_csvs))))
    cue_timing_files = list(map(File,cue_csvs,list(map(lambda x: os.path.basename(x).split('-')[1],cue_csvs))))
    anymaze_files    = list(map(File,anymaze_csvs,list(map(lambda x: re.split('_',Path(x).stem)[-1],anymaze_csvs))))
    ca, c_fis, a_fis = np.intersect1d(list(map(operator.attrgetter('mouse_id'),cue_timing_files)),\
                                      list(map(operator.attrgetter('mouse_id'),anymaze_files)),\
                                      return_indices=True)
    if len(ca) > 1:
        return list(map(operator.attrgetter('filepath'),list(operator.itemgetter(*c_fis)(cue_timing_files)))),\
               list(map(operator.attrgetter('filepath'),list(operator.itemgetter(*a_fis)(anymaze_files))))
    else:
        return list(map(operator.attrgetter('filepath'),cue_timing_files)),\
               list(map(operator.attrgetter('filepath'),anymaze_files))

def grab_files():
    w, h      = sg.Window.get_screen_size()
    load_title= 'Loading'
    load_text = [[sg.Text('Loading file selector...')]]
    load      = open_window(load_title,load_text,int(w/3),int(h/3))
    w, h      = int(w/2.5), int(h/8)
    title     = 'Select Cue Timing and AnyMaze Analysis Files'
    layout    = [[sg.Text('Cue Timing Directory:',size=(18,1),justification='right'),
                  sg.In(default_text='{}'.format(os.getcwd()),\
                        enable_events=True,key='CUEFILES'),
                  sg.FolderBrowse('Select Directory',target='CUEFILES')],
                 [sg.Text('AnyMaze Analysis Directory:',size=(18,1),justification='right'),
                  sg.In(default_text='{}'.format(os.getcwd()),\
                        enable_events=True,key='FREEZEFILES'),
                  sg.FolderBrowse('Select Directory',target='FREEZEFILES')],
                 [sg.OK()]]
    load.close()
    main = open_window(title,layout,w,h)
    main.BringToFront()
    while True:
        event, values = main.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            main.close()
            return None, None
        if event == 'OK':
            cue_csvs               = glob.glob(values['CUEFILES']+"/**/day3*{}".format('.csv'),recursive=True)
            cue_csvs               = sorted(cue_csvs, key = lambda x: re.split('_',os.path.basename(os.path.dirname(x)))[-1])
            anymaze_csvs           = glob.glob(values['FREEZEFILES']+"/**/*{}".format('.csv'),recursive=True)
            anymaze_csvs           = sorted(anymaze_csvs, key = lambda x: re.split('_',Path(x).stem)[-1])
            cue_csvs, anymaze_csvs = match_csvs(cue_csvs, anymaze_csvs)
            main.close()
            return cue_csvs, anymaze_csvs
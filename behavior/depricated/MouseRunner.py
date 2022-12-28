import os
import glob
import time
import shutil
import pygame
import operator
import datetime
import itertools
import tkinter as tk
import PySimpleGUI as sg
from tester import run
from itertools import compress
from operator import itemgetter
from nanpy import (ArduinoApi, SerialManager)

### TODO
# 1. Create mouse class to store mouse info
# 2. Select mouse *object* via 'run' window
# 3. Create TrialParams class for 'run' window output
# 3. Create run function using mouse and TrialParams data
# 4. Add running panel on table (check 'temp' folder for data)
# 5. Push data to save directory (from storage)
# 6. DeepLabCut live
# 7. Display DeepLabCut live


# SET UP RUN MOUSE PROPERLY
# SET UP SAVE VS HOME DIR (CHECK SAVE FOR DAYS, HOME FOR ISRUN)
# SET UP PUSH 2 SAVE DIR
# ADD RUNNING PANEL ON TABLE ('temp' folder in home dir for video)
# add class TrialParams()
# fix re-running arduino glitch!!! clear com 3
# mouse class to store mouse info + path

# %% def

def init_arduino(cameraPin=12,shockerPin=11,ledPin=10):
    ## Establish CTRL Arduino connection
    connection = SerialManager(device = "COM3")
    a          = ArduinoApi(connection=connection)
    pygame.mixer.quit()                                                            # ensure that pygame.mixer is not running to enable setting of sound params
    pygame.mixer.pre_init(44100, -16, 1, 2048)                                     # frequency, bit depth, channels, cache
    a.pinMode(shockerPin, a.OUTPUT)
    a.digitalWrite(shockerPin, a.LOW)
    a.pinMode(ledPin, a.OUTPUT)
    a.digitalWrite(ledPin, a.LOW)
    return a,connection

def open_window(title,layout,w,h):
    sg.theme('BlueMono')
    window = sg.Window(title,layout,finalize=True,size=(w,h),
                       element_justification='center')
    return window

def open_error_window(error_message):
    title  = 'Error'
    w, h   = sg.Window.get_screen_size()
    w, h   = int(w/4), int(h/8)
    layout = [[sg.Text('Could not perform requested operation.')],
              [sg.Text(error_message)],
              [],
              [sg.OK(size=(15,1))]]
    error  = open_window(title,layout,w,h)
    while True:
        event, values = error.read()
        print(event)
        if event in (sg.WINDOW_CLOSED, 'Exit', 'OK'):
            error.close()
            break

def update_table(values,window):
    time.sleep(0.5)
    try:
        path      = values['HOMEPATH']
        data      = fetch_data(path)
        ran_today = list(map(itemgetter(-1), data))
        window.find_element('ROWSELECTED_NOTRUN').Update(values=list(compress(data, map(operator.not_, ran_today))))
        window.find_element('ROWSELECTED_RUN').Update(values=list(compress(data, ran_today)))
    except:
        data      = ['']
        window.find_element('ROWSELECTED_NOTRUN').Update(values=data)
        window.find_element('ROWSELECTED_RUN').Update(values=data)
    return data

def save_params(data_to_save,filepath):
    with open(filepath,'w') as f:
        for data in data_to_save:
            f.write("%s\n" % data)

def read_params(fis_to_read):
    data = []
    for fi in fis_to_read:
        with open(fi) as f:
            data.append(f.read().split('\n'))
    return data

def key_to_value(key_id):
    k_to_v_dict = {'FAVORITE_HOME':'HOMEPATH',\
                   'FAVORITE_STORAGE':'STORAGEPATH',\
                   'FAVORITE_CSMINUS':'CSMINUSPATH',\
                   'FAVORITE_PIP':'PIPPATH',\
                   'FAVORITE_SWEEP':'SWEEPPATH'}
    return k_to_v_dict[key_id]

def save_favorites(values,favorite_id):
    favorite_type = key_to_value(favorite_id)
    favorite      = values[favorite_type]
    favorite_dir  = os.path.join(values['HOMEPATH'],'fav')
    try:
        os.makedirs(favorite_dir)
    except:
        pass
    filepath = os.path.join(favorite_dir,'{}.txt'.format(favorite_type))
    with open(filepath,'w') as f:
        f.write("%s" % favorite)
    return

def load_favorites(favorite_id):
    favorite_type = key_to_value(favorite_id)
    try:
        with open(os.path.join(os.getcwd(),'previous_homepath.txt')) as f:
            previous_homepath = f.read()
        favorite_dir          = os.path.join(previous_homepath,'fav')
        with open(os.path.join(favorite_dir,'{}.txt'.format(favorite_type))) as f:
            favorite          = f.read()
        return favorite
    except:
        return os.getcwd()

def is_run_today(mousedata,recordings):
    today                = datetime.datetime.now().date()
    try:
        latest_recording = max(recordings, key=os.path.getmtime)
        filedate         = datetime.datetime.fromtimestamp(
                           os.path.getmtime(latest_recording)).date()
        mousedata.append(True) if filedate == today else mousedata.append(False)
    except: # mice with no recording yet
        mousedata.append(False)
    return mousedata

def update_days_completed(fis_to_read,data,recording_format=['mp4','avi']):
    for mousenum,fi in enumerate(fis_to_read):
        mouse_dir           = os.path.dirname(fi)
        recording_days      = []
        recordings          = []
        for rf in recording_format:
            records_of_rf   = list(map(os.path.basename,
                                       glob.glob('{}\\*.{}'.format(mouse_dir,rf))))
            unique_days     = set(list(map(lambda x: x.split('-')[0], records_of_rf)))
            recording_days.extend(unique_days)
            recordings.extend(glob.glob('{}\\*.{}'.format(mouse_dir,rf)))
        data[mousenum][-1]  = str(len(recording_days))
        data[mousenum]      = is_run_today(data[mousenum].copy(),recordings)
    return data

def fetch_data(path=os.getcwd()):
    beh              = os.path.join(path,'beh')
    successful_fetch = os.path.isdir(beh)
    if successful_fetch:
        fis_to_read  = glob.glob(beh+"/**/*.txt",recursive=True)
        data         = read_params(fis_to_read)
        final_data   = update_days_completed(fis_to_read,data)
        return final_data
    else:
        return False

def move_to_mouse_dir(mice_run,tmp_path,path):
    for mouse in mice_run:
        beh       = os.path.join(path,'beh')
        mouse_dir = glob.glob(beh+"/**/{}/".format(mouse),recursive=True)[0]
        #shutil.copytree(tmp_path, mouse_dir, dirs_exist_ok=True)
    #shutil.rmtree(tmp_path)

def save_mouse_params(save_output,homepath):
    cohort         = save_output['COHORT']
    mouseid        = save_output['MOUSEID']
    observer       = save_output['OBSERVEREXPERIENCED'] or save_output['OBSERVERNAIVE']
    holepunchleft  = save_output['HOLEPUNCHL']
    cs1pip         = save_output['CS1PIP']
    cs2pip         = save_output['CS2PIP']
    mousetype      = ('Observer (Naive)' if save_output['OBSERVERNAIVE'] else\
                      'Observer (Experienced)') if observer else 'Demonstrator'
    holepunch      = 'Left' if holepunchleft else 'Right'
    cs1            = 'Pip' if cs1pip else 'Sweep'
    cs2            = 'Pip' if cs2pip else 'Sweep'
    beh            = os.path.join(homepath,'beh')
    cohortpath     = os.path.join(beh,'Cohort_{}'.format(cohort))
    mousetypepath  = os.path.join(cohortpath,mousetype.replace(' ','_').replace('(','').replace(')',''))
    mousepath      = os.path.join(mousetypepath,mouseid)
    filepath       = os.path.join(mousepath,'params.txt')
    savedata       = [cohort,mouseid,mousetype,holepunch,cs1,cs2]
    try:
        os.makedirs(mousepath)
    except FileExistsError:
        pass
    save_params(savedata,filepath)
    return

def new_mouse(values):
    title  = 'New Mouse'
    w, h   = sg.Window.get_screen_size()
    w, h   = int(w/4), int(h/4)
    path   = values['HOMEPATH']
    layout = [[sg.Text('Cohort:'),\
               sg.In(default_text='1',size=(3,1),key='COHORT'),\
               sg.Text('Mouse ID:'),\
               sg.In(size=(10,1),key='MOUSEID')],
              [sg.Radio('Observer (Experienced)','MOUSETYPE',default=True,\
                        key='OBSERVEREXPERIENCED'),
               sg.Radio('Observer (Naive)','MOUSETYPE',default=False,\
                        key='OBSERVERNAIVE'),
               sg.Radio('Demonstrator','MOUSETYPE',default=False,\
                        key='DEMONSTRATOR')],
              [sg.Text('Holepunch:'),
               sg.Radio('Left','HOLEPUNCH',default=True,\
                        key='HOLEPUNCHL'),
               sg.Radio('Right','HOLEPUNCH',default=False,\
                        key='HOLEPUNCHR')],
              [sg.Text('CS+1:'),
               sg.Radio('pip','CUETYPE1',default=True,\
                        key='CS1PIP'),
               sg.Radio('sweep','CUETYPE1',default=False,\
                        key='CS1SWEEP')],
              [sg.Text('CS+2:'),
               sg.Radio('pip','CUETYPE2',default=False,\
                        key='CS2PIP'),
               sg.Radio('sweep','CUETYPE2',default=True,\
                        key='CS2SWEEP')],
             [sg.OK(),sg.Cancel()]]
    newmouse = open_window(title,layout,w,h)
    while True:
        event, values = newmouse.read()
        if values['CS1PIP'] == values['CS2PIP']:
            open_error_window('Same stimuli selected for CS+1 and CS+2.')
            continue
        if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
            newmouse.close()
            break
        if event == 'OK':
            newmouse.close()
            save_mouse_params(values,path)
            break

def edit_mouse(data,path=os.getcwd()):
    for mouse_data in data:
        cohort,mouseid,mousetype,holepunch,cs1,cs2,days_ran,ran_today = mouse_data
        title        = 'Edit Mouse'
        w, h         = sg.Window.get_screen_size()
        w, h         = int(w/4), int(h/4)
        layout       = [[sg.Text('Cohort:'),\
                         sg.In(default_text='{}'.format(cohort),size=(3,1),\
                               key='COHORT'),\
                         sg.Text('Mouse ID:'),\
                         sg.In(default_text='{}'.format(mouseid),size=(10,1),\
                               key='MOUSEID')],
                        [sg.Radio('Observer','MOUSETYPE',\
                                  default=True if mousetype=='Observer' else False,\
                                  key='OBSERVER'),
                         sg.Radio('Demonstrator','MOUSETYPE',\
                                  default=False if mousetype=='Observer' else True,\
                                  key='DEMONSTRATOR')],
                        [sg.Text('Holepunch:'),
                         sg.Radio('Left','HOLEPUNCH',\
                                  default=True if holepunch=='Left' else False,\
                                  key='HOLEPUNCHL'),
                         sg.Radio('Right','HOLEPUNCH',\
                                  default=False if holepunch=='Left' else True,\
                                  key='HOLEPUNCHR')],
                        [sg.Text('CS+1:'),
                         sg.Radio('pip','CUETYPE1',\
                                  default=True if cs1=='Pip' else False,\
                                  key='CS1PIP'),
                         sg.Radio('sweep','CUETYPE1',\
                                  default=False if cs1=='Pip' else True,\
                                  key='CS1SWEEP')],
                       [sg.Text('CS+2:'),
                         sg.Radio('pip','CUETYPE2',\
                                  default=True if cs2=='Pip' else False,\
                                  key='CS2PIP'),
                         sg.Radio('sweep','CUETYPE2',\
                                  default=False if cs2=='Pip' else True,\
                                  key='CS2SWEEP')],
                       [sg.OK(),sg.Cancel()]]
        editmouse = open_window(title,layout,w,h)
        while True:
            event, values = editmouse.read()
            print(event)
            print(values)
            if values['CS1PIP'] == values['CS2PIP']:
                open_error_window('Same stimuli selected for CS+1 and CS+2.')
                continue
            if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                editmouse.close()
                break
            if event == 'OK':
                editmouse.close()
                save_mouse_params(values,path)
                break

def delete_mouse(data_selected,path=os.getcwd(),
                 recording_format=['mp4','avi','jpg']):

    for mouse_data in data_selected:
        mouse_id  = mouse_data[1]
        beh       = os.path.join(path,'beh')
        mouse_dir = glob.glob(beh+"/**/{}/".format(mouse_id),recursive=True)
        for m in mouse_dir:
            recordings = []
            for rf in recording_format:
                recordings.extend(glob.glob('{}\\*.{}'.format(mouse_dir,rf)))
            if len(recordings) == 0:
                shutil.rmtree(m)
            else:
                open_error_window('Clould not delete mouse files: Videos Exist')

def retire_mouse(data_selected,values):
    path = values['HOMEPATH']
    for mouse_data in data_selected:
        mouse_id    = mouse_data[1]
        beh         = os.path.join(path,'beh\\')
        retired_dir = os.path.join(path,'retired')
        mouse_dir   = glob.glob(beh+"/**/{}/".format(mouse_id),recursive=True)
        for m in mouse_dir:
            mouse_retired_dir = os.path.join(retired_dir,m.replace(beh,''))
            os.makedirs(os.path.split(mouse_retired_dir.replace(mouse_id,''))[0],
                        exist_ok=True)
            shutil.move(m,mouse_retired_dir)
            print('Retired %s: Mouse data moved from %s to %s' % (mouse_id,
                                                                  m,
                                                                  mouse_retired_dir))

def run_mouse(data_selected,values):
    # try:
        if len(data_selected) == 1:
            mouse_data = data_selected[0]
            mice_run   = [mouse_data[1]]
            title      = 'Run Mouse'
            w, h       = sg.Window.get_screen_size()
            w, h       = int(w/4), int(h/4)
            path       = values['HOMEPATH']
            layout = [[sg.Text('Mouse ID: {}'.format(mouse_data[1]))],
                      [sg.Text('Session type:'),\
                       sg.Radio('Habituation','SESSIONTYPE',default=True,\
                            key='HABITUATION'),
                       sg.Radio('Conditioning','SESSIONTYPE',default=False,\
                            key='CONDITIONING'),
                       sg.Radio('Recall','SESSIONTYPE',default=False,\
                            key='RECALL')],
                      [sg.OK(),sg.Cancel()]]

        elif len(data_selected) > 1:
            if all(['Observer' in '\t'.join(li[:-2]) for li in data_selected]) or\
               all(['Demonstrator' in '\t'.join(li[:-2]) for li in data_selected]):
                   open_error_window('If multiple mice are selected, they cannot be of the same type.')
                   return
            mousetype_bool    = ['Observer' in '\t'.join(li[:-2]) for li in data_selected]
            observer_data     = list(itertools.chain.from_iterable(\
                                list(compress(data_selected,mousetype_bool))))
            demonstrator_data = list(itertools.chain.from_iterable(\
                                list(compress(data_selected,map(operator.not_, mousetype_bool)))))
            mice_run          = [observer_data[1],demonstrator_data[1]]
            if (observer_data[4] != demonstrator_data[4] or\
                observer_data[5] != demonstrator_data[5]):
                   open_error_window('Non-matching CS designations for selected mice.')
                   return
            title      = 'Run Mouse'
            w, h       = sg.Window.get_screen_size()
            w, h       = int(w/4), int(h/4)
            path       = values['HOMEPATH']
            layout = [[sg.Text('Demonstrator ID: {}'.format(\
                               demonstrator_data[1])),
                       sg.Text('Observer ID: {}'.format(\
                               observer_data[1]))],
                      [sg.Text('Session type:'),\
                       sg.Radio('Habituation','SESSIONTYPE',default=True,\
                            key='HABITUATION'),
                       sg.Radio('Conditioning','SESSIONTYPE',default=False,\
                            key='CONDITIONING'),
                       sg.Radio('Recall','SESSIONTYPE',default=False,\
                            key='RECALL')],
                      [sg.OK(),sg.Cancel()]]
        runmice       = open_window(title,layout,w,h)
        path          = values['HOMEPATH']
        tmp_path      = os.path.join(path,'tmp')
        try:
            os.mkdir(tmp_path)
        except:
            pass
        a,connection  = init_arduino()
        while True:
            #a,connection  = init_arduino()
            event, values = runmice.read()
            print(event)
            print(values)
            if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                runmice.close()
                break
            if event == 'OK':
                if len(data_selected) == 1:
                    runmice.close()
                    run(tmp_path,a,connection)
                    #move_to_mouse_dir(mice_run,tmp_path,path)
                elif len(data_selected) > 1:
                    if (values['HABITUATION'] or values['RECALL']):
                        open_error_window('Improper session type for multiple mice.')
                    runmice.close()
                    run(tmp_path,a,connection)
                    #move_to_mouse_dir(mice_run,tmp_path,path)
    # except:
    #     open_error_window('No mice selected for running')

def store_previous_homepath(values):
    filepath = os.path.join(os.getcwd(),'previous_homepath.txt')
    homepath = values['HOMEPATH']
    with open(filepath,'w') as f:
        f.write("%s" % homepath)
    return

def mouse_runner():
    w, h      = sg.Window.get_screen_size()
    load_title= 'Loading'
    load_text = [[sg.Text('Loading Mouse Runner...')]]
    load      = open_window(load_title,load_text,int(w/3),int(h/3))
    title     ='Mouse Runner'
    w, h      = int(w/1.5), int(h/1.5)
    print('Fetching data...')
    path      = load_favorites('FAVORITE_HOME')
    olddata   = fetch_data(path)
    data      = olddata if (olddata != False) else [['']]
    ran_today = list(map(itemgetter(-1), data))
    headings  = ['Cohort','Mouse ID', 'Mouse Type',\
                 'Hole Punch','CS+1','CS+2','Days Completed']
    layout    = [[sg.Text('Home Folder:',size=(15,1),justification='right'),
                  sg.In(default_text='{}'.format(load_favorites('FAVORITE_HOME')),\
                        enable_events=True,key='HOMEPATH'),
                  sg.FolderBrowse('Select Folder',target='HOMEPATH'),
                  sg.Button('Save favorite',key='FAVORITE_HOME')],
                 [sg.Text('Storage Folder:',size=(15,1),justification='right'),
                  sg.In(default_text='{}'.format(load_favorites('FAVORITE_STORAGE')),\
                        enable_events=True,key='STORAGEPATH'),
                  sg.FolderBrowse('Select Folder',target='STORAGEPATH'),
                  sg.Button('Save favorite',key='FAVORITE_STORAGE')],
                 [sg.Text('To run',font='Arial 10',justification='center')],
                 [sg.Table(values=list(compress(data, map(operator.not_, ran_today))),\
                           headings=headings,auto_size_columns=False,\
                           col_widths=[18 for i in range(len(headings))],\
                           justification='center',\
                           right_click_menu=['&Right',['Delete','Edit']],\
                           enable_events=True,key='ROWSELECTED_NOTRUN')],
                 [sg.Text('Ran today',font='Arial 10',justification='center')],
                 [sg.Table(values=list(compress(data, ran_today)),\
                           headings=headings,auto_size_columns=False,\
                           col_widths=[18 for i in range(len(headings))],\
                           justification='center',key='ROWSELECTED_RUN')],
                 [sg.Text('CS- File:',size=(15,1),justification='right'),
                  sg.In(default_text='{}'.format(load_favorites('FAVORITE_CSMINUS')),\
                        enable_events=True,key='CSMINUSPATH'),
                  sg.FileBrowse('Select File',target='CSMINUSPATH'),
                  sg.Button('Save favorite',key='FAVORITE_CSMINUS')],
                 [sg.Text('Pip File:',size=(15,1),justification='right'),
                  sg.In(default_text='{}'.format(load_favorites('FAVORITE_PIP')),\
                        enable_events=True,key='PIPPATH'),
                  sg.FileBrowse('Select File',target='PIPPATH'),
                  sg.Button('Save favorite',key='FAVORITE_PIP')],
                 [sg.Text('Sweep File:',size=(15,1),justification='right'),
                  sg.In(default_text='{}'.format(load_favorites('FAVORITE_SWEEP')),\
                        enable_events=True,key='SWEEPPATH'),
                  sg.FileBrowse('Select File',target='SWEEPPATH'),
                  sg.Button('Save favorite',key='FAVORITE_SWEEP')],
                 [sg.Button('New mouse',key='NEWMOUSE',size=(12,1))],
                 [sg.Button('Retire mouse',key='RETIREMOUSE',size=(12,1))],
                 [sg.Button('Run mouse',key='RUNMOUSE',size=(12,1))]]
    load.close()
    main = open_window(title,layout,w,h)
    main.BringToFront()
    while True:
        event, values = main.read()
        print(event)
        print(values)
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            break
        if event  == 'HOMEPATH':
            data = update_table(values, main)
        if event  == 'ROWSELECTED_NOTRUN':
            ran_today     = list(map(itemgetter(-1), data))
            data_selected = [list(compress(data, map(operator.not_, ran_today)))[row] for row in values[event]]
        if event  == 'Delete':
            #try:
                path = values['HOMEPATH']
                delete_mouse(data_selected,path)
                data_selected = None
                data = update_table(values,main)
            #except:
                #open_error_window('No mouse selected for deletion')
        if event  == 'Edit':
            try:
                path          = values['HOMEPATH']
                edit_mouse(data_selected,path)
                data_selected = None
                data = update_table(values,main)
            except:
                open_error_window('No mouse selected for editing')
        if 'FAVORITE' in event:
            try:
                save_favorites(values,event)
            except:
                open_error_window('Invalid favorite selection.')
        if event  == 'NEWMOUSE':
            new_mouse(values)
            data = update_table(values,main)
        if event  == 'RETIREMOUSE':
            retire_mouse(data_selected,values)
            data = update_table(values,main)
        if event  == 'RUNMOUSE':
            run_mouse(data_selected,values)
            data = update_table(values,main)
        store_previous_homepath(values)

# %% run
root = tk.Tk()
root.withdraw()
mouse_runner()


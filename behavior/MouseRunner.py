#!C:\Users\jacobdahan\Anaconda3\envs\MouseRunner\python.exe

import os
import sys
import glob
import time
import pickle
import shutil
import pygame
import serial
import yagmail
import operator
import datetime
import threading
import PySimpleGUI as sg
import serial.tools.list_ports
from Run import main
from queue import Queue
from operator import attrgetter
from collections import namedtuple
from itertools import compress, groupby
from nanpy import (ArduinoApi, SerialManager)

# %% Spinner Class
class Spinner:
    """
    Adapted from https://stackoverflow.com/questions/4995733/how-to-create-a-spinning-command-line-cursor
    This class yields a spinning cursor for friendly UI when called using a
    'with' block.
    """
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        time.sleep(0.1)
        while 1:
            for cursor in '|/-\\': yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): self.delay = delay

    def spinner_task(self):
        while self.busy:
            #self.print_lock.acquire()
            print("\b\b\b\r{}".format(next(self.spinner_generator)),end="")
            #self.print_lock.release()
            # sys.stdout.write(next(self.spinner_generator))
            # sys.stdout.flush()
            time.sleep(self.delay)
            # sys.stdout.write('\b')
            # sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        sys.stdout.write('\b')
        if exception is not None:
            return False

# %% Itertools all equal recipe
def all_equal(iterable):
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

# %% Mapped Method class
class MappedMethod:
    """
    This class maps a single method to all elements of an iterable, with both
    *args and **kwargs compatibility.
    :param elements: Elements onto which the method should be applied.
    :type elements: iterable
    :param *args: Any args applicabale to the method (will be applied uniformly to all elements).
    :type *args: any (method-dependent)
    :param **kwargs: Any kwargs applicable to the method (will be applied unformly to all elements).
    :type **kwargs: any (method-dependent)
    """
    def __init__(self, elements):
        self.elements = elements
    def __getattr__(self, attr):
        def apply_to_all(*args, **kwargs):
            for obj in self.elements:
                getattr(obj, attr)(*args, **kwargs)
        return apply_to_all

# %% NamedMouse class
class NamedMouse(namedtuple('Mouse','id MouseObject')):

    __slots__ = ()
    @property
    def identity(self):
        return self.id
    def __hash__(self):
        return hash(self.id)
    def __eq__(self,other):
        return self.id == other.id

# %% Email class
class Email:

    def __init__(self,DATA,FROM,TO=None,SUBJECT=None,CONTENTS=None,PW=None,SEND=False):
        self.mouse     = next(iter(DATA)) if len(DATA) == 1 else DATA
        self.sender    = FROM
        self.recipient = TO if TO else FROM
        self.subject   = SUBJECT if SUBJECT else 'MouseRunner Session Completed'
        self.contents  = CONTENTS
        self.pw        = PW
        self.to_send   = SEND

    def generate_contents(self):
        if type(self.mouse) == Mouse:
            self.contents = self.contents if self.contents else\
                           'Notice of completion of behavioral session for mouse\
                            {} (type: {}) at time {} on {}.'.format(self.mouse.mouse_id,\
                            self.mouse.mouse_type,datetime.datetime.now().strftime('%H:%M:%S'),\
                            datetime.datetime.now().strftime('%D'))
        else:
            self.contents = self.contents if self.contents else\
                           'Notice of completion of behavioral session for mice\
                            {} and {} at time {} on {}.'.format(self.mouse[0].mouse_id,\
                            self.mouse[1].mouse_id,datetime.datetime.now().strftime('%H:%M:%S'),\
                            datetime.datetime.now().strftime('%D'))
    def init_mail(self):
        self.email = yagmail.SMTP(self.sender, self.pw)

    def send(self):
        try:
            if self.to_send:
                self.generate_contents()
                self.init_mail()
                self.email.send(to=self.recipient,subject=self.subject,contents=self.contents)
                print('\b\b\bSending email notification of behavior completion to %s...' % (self.recipient))
        except:
            print('\b\b\bUnable to send email notification of behavior completion to %s...' % (self.recipient))

# %% Mouse class
class Mouse:

    def __init__(self,params_path,cohort,mouse_id,mouse_type,holepunch,cs1,cs2):
        self.params_path    = params_path
        self.cohort         = cohort
        self.mouse_id       = mouse_id
        self.mouse_type     = mouse_type
        self.holepunch      = holepunch
        self.cs1            = cs1
        self.cs2            = cs2
        self.update_days_completed()
        self.is_run_today()
        self.is_naive()

    def return_parameters(self):
        return [self.cohort,self.mouse_id,self.mouse_type,self.holepunch,\
                self.cs1,self.cs2,self.days_completed]

    def update_days_completed(self,recording_format=['mp4','avi'],file_splitter='_'):
        self.recording_days = []
        self.recordings     = []
        for rf in recording_format:
            records_of_rf   = list(map(os.path.basename,
                                       glob.glob('{}\\*.{}'.format(self.params_path,rf))))
            unique_days     = set(list(map(lambda x: x.split(file_splitter)[0], records_of_rf)))
            self.recording_days.extend(unique_days)
            self.recordings.extend(glob.glob('{}\\*.{}'.format(self.params_path,rf)))
        self.days_completed = str(len(self.recording_days))

    def is_run_today(self):
        today                = datetime.datetime.now().date()
        try:
            latest_recording = max(self.recordings, key=os.path.getmtime)
            filedate         = datetime.datetime.fromtimestamp(
                               os.path.getmtime(latest_recording)).date()
            self.ran_today   = True if filedate == today else False
        except: # mice with no recording yet
            self.ran_today   = False

    def is_naive(self):
        try:
            self.naive = True if 'Naive' in self.mouse_type else False
        except TypeError:
            self.naive = False

    def save(self):
        with open(os.path.join(self.params_path,'params.pickle'), 'wb') as fi:
            pickle.dump(self,fi,protocol=pickle.HIGHEST_PROTOCOL)

# %% Session Parameters class
class SessionParams:

    def __init__(self,tmp_path,run_values,mice_running,tones):
        self.tmp_path       = tmp_path
        self.running        = mice_running
        self.session_type   = 'Habituation' if run_values['HABITUATION'] else \
                              'Conditioning' if run_values['CONDITIONING'] else \
                              'OFC' if run_values['OFC'] else\
                              'Recall' if run_values['RECALL'] else 'Re-recall'
        self.days_completed = 0 if run_values['HABITUATION'] else \
                              1 if run_values['CONDITIONING'] else \
                              2 if run_values['OFC'] else \
                              3 if run_values['RECALL'] else 4
        self.shock          = False if True in list(map(attrgetter('naive'),self.running)) else True
        self.cs_minus, self.pip, self.sweep = tones

    def package(self):
        self.tone_params = {'cs1'      : self.pip if 'Pip' in list(map(attrgetter('cs1'),self.running)) else self.sweep,
                            'cs2'      : self.pip if 'Pip' in list(map(attrgetter('cs2'),self.running)) else self.sweep,
                            'cs_minus' : self.cs_minus}
        self.save_params = {'tmp_path' : self.tmp_path,
                            'day'      : self.days_completed,
                            'mice'     : list(map(attrgetter('mouse_id'),self.running))}

# %% App class
class App:

    def __init__(self,homepath=os.getcwd(),recording_format=['mp4','avi']):
        self.w, self.h        = sg.Window.get_screen_size()
        self.running          = [Mouse(None,None,None,None,None,None,None)]
        self.arduino_isrun    = False
        self.recording_format = recording_format
        self.k_to_v_dict      = {'FAVORITE_EMAIL'  :'EMAIL_INPUT',\
                                 'FAVORITE_PW'     :'PASSWORD_INPUT',\
                                 'FAVORITE_HOME'   :'HOMEPATH',\
                                 'FAVORITE_STORAGE':'STORAGEPATH',\
                                 'FAVORITE_CSMINUS':'CSMINUSPATH',\
                                 'FAVORITE_PIP'    :'PIPPATH',\
                                 'FAVORITE_SWEEP'  :'SWEEPPATH'}
        self.load_window()
        self.load_favorites('FAVORITE_HOME')

    def find_arduino(self):
        self.com_port = [p.device for p in serial.tools.list_ports.comports()\
                         if 'Arduino' in p.description].pop()

    def init_arduino(self,laserPin=4,shockerPin=7,ledPin=8):
        if not self.arduino_isrun:
            self.find_arduino()
            self.connection = SerialManager(device = self.com_port)
            self.a          = ArduinoApi(connection=self.connection)
            pygame.mixer.quit()                                                            # ensure that pygame.mixer is not running to enable setting of sound params
            pygame.mixer.pre_init(44100, -16, 1, 2048)                                     # frequency, bit depth, channels, cache
            self.a.pinMode(laserPin, self.a.OUTPUT)
            self.a.digitalWrite(laserPin, self.a.LOW)
            self.a.pinMode(shockerPin, self.a.OUTPUT)
            self.a.digitalWrite(shockerPin, self.a.LOW)
            self.a.pinMode(ledPin, self.a.OUTPUT)
            self.a.digitalWrite(ledPin, self.a.LOW)
            self.arduino_isrun = True
        else:
            pygame.mixer.quit()                                                            # ensure that pygame.mixer is not running to enable setting of sound params
            pygame.mixer.pre_init(44100, -16, 1, 2048)                                     # frequency, bit depth, channels, cache
            self.a.pinMode(laserPin, self.a.OUTPUT)
            self.a.digitalWrite(laserPin, self.a.LOW)
            self.a.pinMode(shockerPin, self.a.OUTPUT)
            self.a.digitalWrite(shockerPin, self.a.LOW)
            self.a.pinMode(ledPin, self.a.OUTPUT)
            self.a.digitalWrite(ledPin, self.a.LOW)

    def key_to_value(self,key_id):
        return self.k_to_v_dict[key_id]

    def save_favorites(self,favorite_id):
        favorite_type = self.key_to_value(favorite_id)
        favorite      = self.values[favorite_type]
        if self.favorite_dir:
            try:
                os.makedirs(self.favorite_dir)
            except FileExistsError:
                pass
        else:
            self.favorite_dir = os.path.join(self.homepath,'favorites')
            try:
                os.makedirs(self.favorite_dir)
            except FileExistsError:
                pass
        filepath = os.path.join(self.favorite_dir,'{}.txt'.format(favorite_type))
        with open(filepath,'w') as f:
            f.write("%s" % favorite)

    def load_favorites(self,favorite_id):
        favorite_type = self.key_to_value(favorite_id)
        try:
            with open(os.path.join(os.getcwd(),'previous_homepath.txt')) as f:
                self.homepath = f.read()
                self.favorite_dir = os.path.join(self.homepath,'favorites')
                with open(os.path.join(self.favorite_dir,'{}.txt'.format(favorite_type))) as f:
                    favorite          = f.read()
            with open(os.path.join(self.favorite_dir,'{}.txt'.format(favorite_type))) as f:
                favorite = f.read()
            return favorite
        except:
            self.homepath = os.getcwd()
            try:
                with open(os.path.join(os.getcwd(),'previous_homepath.txt')) as f:
                    self.homepath = f.read()
                    self.favorite_dir = os.path.join(self.homepath,'favorites')
                    with open(os.path.join(self.favorite_dir,'{}.txt'.format(favorite_type))) as f:
                        favorite          = f.read()
                with open(os.path.join(self.favorite_dir,'{}.txt'.format(favorite_type))) as f:
                    favorite = f.read()
                return favorite
            except:
                pass


    def open_window(self,title,layout,w_multiplier,h_multiplier):
        sg.theme('BlueMono')
        window = sg.Window(title,layout,finalize=True,\
                           size=(int(self.w*w_multiplier),int(self.h*h_multiplier)),\
                           element_justification='center')
        return window

    def open_error_window(self,error_message):
        title  = 'Error'
        layout = [[sg.Text('Could not perform requested operation.')],
                  [sg.Text(error_message)],
                  [],
                  [sg.OK(size=(15,1))]]
        error  = self.open_window(title,layout,1/4,1/7)
        while True:
            event, values = error.read()
            print(event)
            if event in (sg.WINDOW_CLOSED, 'Exit', 'OK'):
                error.close()
                break

    def generate_layout(self):
        self.title     = 'Mouse Runner'
        self.headings  = ['Cohort','Mouse ID', 'Mouse Type',\
                          'Hole Punch','CS+1','CS+2','Days Completed']
        self.layout    = [[sg.Checkbox('Email Updates',default=True,\
                                       enable_events=False,key='SEND_EMAIL')],
                          [sg.Text('Email:',size=(15,1),justification='right'),\
                           sg.InputText(default_text='{}'.format(self.load_favorites('FAVORITE_EMAIL')),\
                                        enable_events=False,key='EMAIL_INPUT'),\
                           sg.Button('Save favorite',key='FAVORITE_EMAIL',size=(21,1))],
                          [sg.Text('Password:',size=(15,1),justification='right'),\
                           sg.InputText(default_text='{}'.format(self.load_favorites('FAVORITE_PW')),\
                                        enable_events=False,key='PASSWORD_INPUT',\
                                        password_char='*'),\
                           sg.Button('Save favorite',key='FAVORITE_PW',size=(21,1))],
                          [sg.Text('Home Folder:',size=(15,1),justification='right'),
                           sg.In(default_text='{}'.format(self.load_favorites('FAVORITE_HOME')),\
                                 enable_events=True,key='HOMEPATH'),
                           sg.FolderBrowse('Select Folder',target='HOMEPATH'),
                           sg.Button('Save favorite',key='FAVORITE_HOME')],
                          [sg.Text('Storage Folder:',size=(15,1),justification='right'),
                           sg.In(default_text='{}'.format(self.load_favorites('FAVORITE_STORAGE')),\
                                 enable_events=True,key='STORAGEPATH'),
                           sg.FolderBrowse('Select Folder',target='STORAGEPATH'),
                           sg.Button('Save favorite',key='FAVORITE_STORAGE')],

                          [sg.Text('To run',font='Arial 10',justification='center')],
                          [sg.Table(values=list(compress(self.fetched_data, map(operator.not_,self.ran_today))),\
                                    headings=self.headings,auto_size_columns=False,\
                                    col_widths=[18 for i in range(len(self.headings))],\
                                    justification='center',\
                                    right_click_menu=['&Right',['Delete','Edit']],\
                                    enable_events=True,key='ROWSELECTED_NOTRUN')],
                          [sg.Text('Running',font='Arial 10',justification='center')],
                          [sg.Table(values=list(),num_rows=3,\
                                    headings=self.headings,auto_size_columns=False,\
                                    col_widths=[18 for i in range(len(self.headings))],\
                                    justification='center',key='ROWSELECTED_RUNNING')],
                          [sg.Text('Ran today',font='Arial 10',justification='center')],
                          [sg.Table(values=list(compress(self.fetched_data,self.ran_today)),\
                                    headings=self.headings,auto_size_columns=False,\
                                    col_widths=[18 for i in range(len(self.headings))],\
                                    justification='center',key='ROWSELECTED_RUN')],
                          [sg.Text('CS- File:',size=(15,1),justification='right'),
                           sg.In(default_text='{}'.format(self.load_favorites('FAVORITE_CSMINUS')),\
                                 enable_events=True,key='CSMINUSPATH'),
                           sg.FileBrowse('Select File',target='CSMINUSPATH'),
                           sg.Button('Save favorite',key='FAVORITE_CSMINUS')],
                          [sg.Text('Pip File:',size=(15,1),justification='right'),
                           sg.In(default_text='{}'.format(self.load_favorites('FAVORITE_PIP')),\
                                 enable_events=True,key='PIPPATH'),
                           sg.FileBrowse('Select File',target='PIPPATH'),
                           sg.Button('Save favorite',key='FAVORITE_PIP')],
                          [sg.Text('Sweep File:',size=(15,1),justification='right'),
                           sg.In(default_text='{}'.format(self.load_favorites('FAVORITE_SWEEP')),\
                                 enable_events=True,key='SWEEPPATH'),
                           sg.FileBrowse('Select File',target='SWEEPPATH'),
                           sg.Button('Save favorite',key='FAVORITE_SWEEP')],
                          [sg.Button('New mouse',key='NEWMOUSE',size=(14,1))],
                          [sg.Button('Retire mouse',key='RETIREMOUSE',size=(14,1))],
                          [sg.Button('Run mouse',key='RUNMOUSE',size=(14,1))],
                          [sg.Button('Move to storage',key='STORAGEPUSH',size=(14,1))]]

    def load_window(self):
        load_title  = 'Loading'
        load_layout = [[sg.Text('Loading Mouse Runner...')]]
        scale       = 1/3
        self.load   = self.open_window(load_title,load_layout,scale,scale)

    def read_files(self):
        self.mice       = []
        for fi in self.fetched_files:
            with open(fi, 'rb') as f:
                mouse = pickle.load(f)
                mouse.update_days_completed()
                mouse.is_run_today()
                mouse.is_naive()
                self.mice.append(mouse)

    def store_previous_homepath(self):
        filepath = os.path.join(os.getcwd(),'previous_homepath.txt')
        homepath = self.values['HOMEPATH']
        with open(filepath,'w') as f:
            f.write("%s" % homepath)

    def load_previous_homepath(self):
        filepath = os.path.join(os.getcwd(),'previous_homepath.txt')
        try:
            with open(filepath,'r') as f:
                self.homepath = f.readline()
        except:
            self.homepath = os.getcwd()

    def fetch_data(self):
        self.behavior_path = os.path.join(self.homepath,'behavior')
        successful_fetch   = os.path.isdir(self.behavior_path)
        if successful_fetch:
            self.fetched_files = glob.glob(self.behavior_path+"/**/params.pickle",recursive=True)
            self.read_files()
            self.not_running  = [mouse for mouse in self.mice if mouse.mouse_id not in list(map(attrgetter('mouse_id'),self.running))]
            self.running      = [mouse for mouse in self.mice if mouse.mouse_id in list(map(attrgetter('mouse_id'),self.running))]
            self.fetched_data = list(map(lambda mouse:mouse.return_parameters(),self.not_running))
            self.ran_today    = list(map(attrgetter('ran_today'),self.not_running))
        else:
            self.fetched_data = [['']]
            self.ran_today    = ['']

    def update_table(self):
        time.sleep(0.1)
        self.fetch_data()
        self.main.find_element('ROWSELECTED_NOTRUN').Update(values=list(compress(self.fetched_data, map(operator.not_, self.ran_today))))
        self.main.find_element('ROWSELECTED_RUNNING').Update(values=list(map(lambda mouse:mouse.return_parameters(),self.running)))
        self.main.find_element('ROWSELECTED_RUN').Update(values=list(compress(self.fetched_data, self.ran_today)))
        self.main.refresh()

    def move_to_mouse_dir(self):
        for mouse in self.running:
            print('\b\b\bTransfering files from %s to %s...' % (self.tmp_path,
                                                                mouse.params_path))
            time.sleep(60)
            shutil.copytree(self.tmp_path, mouse.params_path, dirs_exist_ok=True)

    def save_mouse_object(self,mouse_values,old_mouse=None):
        cohort         = mouse_values['COHORT']
        mouseid        = mouse_values['MOUSEID']
        observer       = mouse_values['OBSERVEREXPERIENCED'] or mouse_values['OBSERVERNAIVE']
        holepunchleft  = mouse_values['HOLEPUNCHL']
        cs1pip         = mouse_values['CS1PIP']
        cs2pip         = mouse_values['CS2PIP']
        mousetype      = ('Observer (Naive)' if mouse_values['OBSERVERNAIVE'] else\
                          'Observer (Experienced)') if observer else 'Demonstrator'
        holepunch      = 'Left' if holepunchleft else 'Right'
        cs1            = 'Pip' if cs1pip else 'Sweep'
        cs2            = 'Pip' if cs2pip else 'Sweep'
        cohortpath     = os.path.join(self.behavior_path,'Cohort_{}'.format(cohort))
        mousetypepath  = os.path.join(cohortpath,mousetype.replace(' ','_').replace('(','').replace(')',''))
        mousepath      = os.path.join(mousetypepath,mouseid)
        mouse          = Mouse(mousepath,cohort,mouseid,mousetype,holepunch,cs1,cs2)
        try:
            os.makedirs(mouse.params_path)
        except FileExistsError:
            pass
        if old_mouse and (old_mouse.params_path != mouse.params_path):
            shutil.copytree(old_mouse.params_path,mouse.params_path,\
                            copy_function=shutil.move,dirs_exist_ok=True,\
                            ignore=shutil.ignore_patterns('*.pickle'))
            shutil.rmtree(old_mouse.params_path)
        mouse.save()
        return

    def new_mouse(self):
        title  = 'New Mouse'
        scale  = 1/4
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
        newmouse = self.open_window(title,layout,scale,scale)
        while True:
            event, mouse_values = newmouse.read()
            if mouse_values['CS1PIP'] == mouse_values['CS2PIP']:
                self.open_error_window('Same stimuli selected for CS+1 and CS+2.')
                continue
            if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                newmouse.close()
                break
            if event == 'OK':
                newmouse.close()
                self.save_mouse_object(mouse_values)
                break

    def edit_mouse(self):
        for mouse in self.data_selected:
            title  = 'Edit Mouse'
            scale  = 1/4
            layout = [[sg.Text('Cohort:'),\
                       sg.In(default_text='{}'.format(mouse.cohort),size=(3,1),\
                             key='COHORT'),\
                       sg.Text('Mouse ID:'),\
                       sg.In(default_text='{}'.format(mouse.mouse_id),size=(10,1),\
                             key='MOUSEID')],
                      [sg.Radio('Observer (Experienced)','MOUSETYPE',\
                                default=True if mouse.mouse_type == 'Observer (Experienced)' else False,\
                                key='OBSERVEREXPERIENCED'),
                       sg.Radio('Observer (Naive)','MOUSETYPE',\
                                default=True if mouse.mouse_type == 'Observer (Naive)' else False,\
                                key='OBSERVERNAIVE'),
                       sg.Radio('Demonstrator','MOUSETYPE',\
                                default=True if mouse.mouse_type == 'Demonstrator' else False,\
                                key='DEMONSTRATOR')],
                      [sg.Text('Holepunch:'),
                       sg.Radio('Left','HOLEPUNCH',\
                                default=True if mouse.holepunch=='Left' else False,\
                                key='HOLEPUNCHL'),
                       sg.Radio('Right','HOLEPUNCH',\
                                default=False if mouse.holepunch=='Left' else True,\
                                key='HOLEPUNCHR')],
                      [sg.Text('CS+1:'),
                       sg.Radio('pip','CUETYPE1',\
                                default=True if mouse.cs1=='Pip' else False,\
                                key='CS1PIP'),
                       sg.Radio('sweep','CUETYPE1',\
                                default=False if mouse.cs1=='Pip' else True,\
                                key='CS1SWEEP')],
                      [sg.Text('CS+2:'),
                       sg.Radio('pip','CUETYPE2',\
                                default=True if mouse.cs2=='Pip' else False,\
                                key='CS2PIP'),
                       sg.Radio('sweep','CUETYPE2',\
                                default=False if mouse.cs2=='Pip' else True,\
                                key='CS2SWEEP')],
                      [sg.OK(),sg.Cancel()]]
            editmouse = self.open_window(title,layout,scale,scale)
            while True:
                event, mouse_values = editmouse.read()
                print('\b\b\b',event)
                print('\b\b\b',mouse_values)
                if mouse_values['CS1PIP'] == mouse_values['CS2PIP']:
                    self.open_error_window('Same stimuli selected for CS+1 and CS+2.')
                    continue
                if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                    editmouse.close()
                    break
                if event == 'OK':
                    editmouse.close()
                    self.save_mouse_object(mouse_values,mouse)
                    break

    def delete_mouse(self):
        for mouse in self.data_selected:
            recordings = []
            for rf in self.recording_format:
                recordings.extend(glob.glob('{}\\*.{}'.format(mouse.params_path,rf)))
            if len(recordings) == 0:
                shutil.rmtree(mouse.params_path)
            else:
                self.open_error_window('Clould not delete mouse files: Videos Exist')

    def retire_mouse(self):
        self.retired_path = os.path.join(self.homepath,'retired')
        for mouse in self.data_selected:
            mouse_retired_path = os.path.join(self.retired_path,\
                                              os.path.relpath(mouse.params_path,self.behavior_path))
            os.makedirs(os.path.dirname(mouse_retired_path),exist_ok=True)
            shutil.move(mouse.params_path,os.path.dirname(mouse_retired_path))
            print('Retired Mouse %s: \nMouse data moved from \n\t%s to \n\t%s' % (mouse.mouse_id,
                                                                                  mouse.params_path,
                                                                                  mouse_retired_path))

    def run_mouse(self):
        title  = 'Run Mouse'
        wscale = 1/3
        hscale = 1/8
        print(self.data_selected)
        if len(self.data_selected) == 1:
            mouse  = next(iter(self.data_selected))
            layout = [[sg.Text('Mouse ID: {}'.format(mouse.mouse_id))],
                      [sg.Text('Session type:'),\
                       sg.Radio('Habituation','SESSIONTYPE',default=True,\
                                key='HABITUATION'),
                       sg.Radio('Conditioning','SESSIONTYPE',default=False,\
                                key='CONDITIONING'),
                       sg.Radio('OFC','SESSIONTYPE',default=False,\
                                key='OFC'),
                       sg.Radio('Recall','SESSIONTYPE',default=False,\
                                key='RECALL'),
                       sg.Radio('Re-recall','SESSIONTYPE',default=False,\
                                key='RERECALL')],
                      [sg.OK(),sg.Cancel()]]
        elif len(self.data_selected) == 2:
            if all('Observer' in mouse_type for mouse_type in list(map(attrgetter('mouse_type'),self.data_selected))) or\
                all('Demonstrator' in mouse_type for mouse_type in list(map(attrgetter('mouse_type'),self.data_selected))):
                    self.open_error_window('If multiple mice are selected, they cannot be of the same type.')
                    return
            elif not all_equal(list(map(attrgetter('cs1'),self.data_selected))) or\
                not all_equal(list(map(attrgetter('cs2'),self.data_selected))):
                    self.open_error_window('Non-matching CS designations for selected mice.')
                    return
            else:
                observer_mouse     = next((mouse for mouse in self.data_selected if 'Observer' in mouse.mouse_type))
                demonstrator_mouse = next((mouse for mouse in self.data_selected if 'Demonstrator' in mouse.mouse_type))
                layout = [[sg.Text('Demonstrator ID: {}'.format(\
                                    demonstrator_mouse.mouse_id)),
                            sg.Text('Observer ID: {}'.format(\
                                    observer_mouse.mouse_id))],
                          [sg.Text('Session type:'),\
                            sg.Radio('Habituation','SESSIONTYPE',default=True,\
                                key='HABITUATION'),
                            sg.Radio('Conditioning','SESSIONTYPE',default=False,\
                                key='CONDITIONING'),
                            sg.Radio('OFC','SESSIONTYPE',default=False,\
                                key='OFC'),
                            sg.Radio('Recall','SESSIONTYPE',default=False,\
                                key='RECALL'),
                            sg.Radio('Re-recall','SESSIONTYPE',default=False,\
                                key='RERECALL')],
                          [sg.OK(),sg.Cancel()]]
        else:
            self.open_error_window('No mice selected for running')
        runmice = self.open_window(title,layout,wscale,hscale)
        self.tmp_path = os.path.join(self.homepath,'temporary')
        try:
            os.mkdir(self.tmp_path)
        except:
            shutil.rmtree(self.tmp_path)
            os.mkdir(self.tmp_path)
        self.init_arduino()
        while True:
            event, values = runmice.read()
            if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                runmice.close()
                return
            if event == 'OK':
                if len(self.data_selected) == 1:
                    runmice.close()
                    break
                elif len(self.data_selected) > 1:
                    if (values['HABITUATION'] or values['CONDITIONING'] or values['RECALL']):
                        self.open_error_window('Improper session type for multiple mice.')
                        continue
                    else:
                        runmice.close()
                        break
        self.email = Email(self.data_selected,FROM=self.values['EMAIL_INPUT'],\
                           PW=self.values['PASSWORD_INPUT'],SEND=self.values['SEND_EMAIL'])
        self.running     = self.data_selected
        self.plot_queue  = Queue()
        self.session_params = SessionParams(self.tmp_path,values,self.running,self.tones)
        self.session_params.package()
        self.update_table()
        self.run_thread = threading.Thread(target=main,args=(self.a,self.connection,\
                                                             self.session_params,self.plot_queue))
        self.run_thread.start()
        self.plot = self.plot_queue.get()
        self.plot.plot()
        self.run_thread.join()
        self.email.send()
        with Spinner():
            self.move_to_mouse_dir()
        self.running = [Mouse(None,None,None,None,None,None,None)]
        self.update_table()
        return

    def move_to_storage(self):
        dirs_to_move = [root for root,subdirs,files in os.walk(self.retired_path) if not subdirs]
        for d in dirs_to_move:
            new_dir  = os.path.join(self.storage_path,os.path.relpath(d,self.homepath))
            old_fis  = [os.path.basename(f) for f in glob.glob(os.path.join(new_dir,'*.*'))]
            for f in glob.glob(os.path.join(d,'*.*')):
                if os.path.basename(f) not in old_fis:
                    shutil.copy(f,new_dir)
                    print('Stored data: Moved file \n\t%s to \n\t%s' % (f,new_dir))
        print('Storage transfer completed...')

    def main_app(self):
        self.load_previous_homepath()
        self.fetch_data()
        self.generate_layout()
        self.load.close()
        self.wscale = 1/1.5
        self.hscale = 1/1.15
        self.main   = self.open_window(self.title,self.layout,self.wscale,self.hscale)
        self.main.BringToFront()
        while True:
            self.event, self.values = self.main.read()
            print(self.event)
            print(self.values)
            if self.event in (sg.WINDOW_CLOSED, 'Exit'):
                break
            elif self.event  == 'HOMEPATH':
                self.homepath = self.values['HOMEPATH']
                self.update_table()
            elif self.event  == 'ROWSELECTED_NOTRUN':
                self.data_selected = [list(compress(self.not_running, map(operator.not_, self.ran_today)))[row] for row in self.values[self.event]]
            elif self.event  == 'Delete':
                try:
                    self.homepath = self.values['HOMEPATH']
                    self.delete_mouse()
                    self.data_selected = None
                    self.update_table()
                except:
                    self.open_error_window('No mouse selected for deletion')
                    continue
            elif self.event  == 'Edit':
                try:
                    self.homepath = self.values['HOMEPATH']
                    self.edit_mouse()
                    self.data_selected = None
                    self.update_table()
                except:
                    self.open_error_window('No mouse selected for editing')
            elif 'FAVORITE' in self.event:
                try:
                    self.save_favorites(self.event)
                except:
                    self.open_error_window('Invalid favorite selection.')
            elif self.event  == 'NEWMOUSE':
                self.new_mouse()
                self.update_table()
            elif self.event  == 'RETIREMOUSE':
                self.retire_mouse()
                self.update_table()
            elif self.event  == 'RUNMOUSE':
                try:
                    self.tones = (self.values['CSMINUSPATH'],
                                  self.values['PIPPATH'],
                                  self.values['SWEEPPATH'])
                except:
                    self.open_error_window('Must select tones prior to running behavior.')
                    continue
                # try:
                self.run_mouse()
                # except:
                    # self.open_error_window('No mouse selected for running')
            elif self.event == 'STORAGEPUSH':
                self.storage_path = self.values['STORAGEPATH']
                self.retired_path = os.path.join(self.homepath,'retired')
                self.move_to_storage()
            self.store_previous_homepath()
            try:
                print('\b\b\bMice selected:',[m.mouse_id for m in self.data_selected])
            except:
                None

if __name__ == "__main__":
    a=App()
    a.main_app()
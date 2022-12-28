# -*- coding: utf-8 -*-

# %% Import toolboxes
from nanpy import (ArduinoApi, SerialManager)
from itertools import groupby
from datetime import datetime
import PySpinController
import numpy as np
import threading
import pygame
import time
import random
import os

# %% Default Parameters class
class DefaultParams:

    def __init__(self,session_type):
        self.params = self.habituation() if session_type == 'Habituation' else\
                      self.conditioning() if session_type == 'Conditioning' else\
                      self.ofc() if session_type == 'OFC' else self.recall()
        self.trial_generator()
        self.isi_generator()
        self.trialize()

    def trial_generator(self):
        trials_nonrandom = list(iter(self.params['cs_ids'])) * self.params['stim_num']
        while True:
            self.trials = random.sample(trials_nonrandom,len(trials_nonrandom))                    # random sample without replacement of all trials for randomized tone presentation
            max_consecutive = max([sum(1 for _ in group) for _, group in groupby(self.trials)])
            if max_consecutive > 2:
                self.iter_trials = iter(self.trials)
                continue
            else:
                return

    def isi_generator(self):
        while True:
            self.isis = np.random.normal(self.params['avg_isi'],
                                         self.params['std_isi'],
                                         len(self.trials) - 1)
            if any (isi < (self.params['avg_isi'] / 2) for isi in self.isis):
                continue
            else:
                return

    def trialize(self):
        self.trial_duration    = self.isis + self.params['cs_duration']
        self.iter_duration     = iter(self.trial_duration)
        self.trial_start_times = np.array([self.params['baseline'],*self.trial_duration])
        self.trial_start_times = list(self.trial_start_times.cumsum())

    def save(self,save_params):
        np.savetxt(os.path.join(save_params['tmp_path'],"day{}-timing.csv".format(save_params['day'])),
                               [self.trials,self.trial_start_times],
                                delimiter =", ",
                                fmt ='% s')

    def habituation(self):
        return {'stim_num'       : 4,
                'baseline'       : 180,
                'avg_isi'        : 60,
                'std_isi'        : 15,
                'cs_duration'    : 30,
                'cs_ids'         : (0,1,2),
                'shock_duration' : 1.0,
                'shock_id'       : None,
                'shock'          : False}

    def conditioning(self):
        return {'stim_num'       : 5,
                'baseline'       : 180,
                'avg_isi'        : 60,
                'std_isi'        : 15,
                'cs_duration'    : 30,
                'cs_ids'         : (0,1),
                'shock_duration' : 1.0,
                'shock_id'       : 1,
                'shock'          : True}

    def ofc(self):
        return {'stim_num'       : 5,
                'baseline'       : 180,
                'avg_isi'        : 60,
                'std_isi'        : 15,
                'cs_duration'    : 30,
                'cs_ids'         : (0,2),
                'shock_duration' : 1.0,
                'shock_id'       : 2,
                'shock'          : True}

    def recall(self):
        return {'stim_num'       : 5,
                'baseline'       : 180,
                'avg_isi'        : 60,
                'std_isi'        : 15,
                'cs_duration'    : 30,
                'cs_ids'         : (0,1,2),
                'shock_duration' : 1.0,
                'shock_id'       : None,
                'shock'          : False}

class MainApp:

    def __init__(self,a,connection,session_params,cameraPin,shockerPin,ledPin):
        self.a = a
        self.connection = connection
        self.params = session_params
        self.cameraPin = cameraPin
        self.shockerPin = shockerPin
        self.ledPin = ledPin

    def fetch_defaults(self):
        self.default_params = DefaultParams(self.params.session_type)
        self.default_params.save(self.params.save_params)
        print(self.default_params.trials)
        print(self.default_params.trial_start_times)

    def pause(self,pause):
        time.sleep(pause)

    def num2type(self,trial_type):
        trial_type = 'cs1' if trial_type == 1 else \
                     'cs2' if trial_type == 2 else 'cs_minus'
        return trial_type

    def session(self):
        for trial_num in range(len(self.trials)):
            trial_type     = next(self.iter_trials)
            trial_duration = next(self.iter_duration) 
            self.print_lock.acquire()
            print("\r\b\b\b========================")
            print("Trial: {}, Type: {}".format(trial_num,trial_type))
            self.print_lock.release()
            self.trial_start = time.time()
            threading.Thread(target=self.ledCtrl).start()
            pygame.mixer.init()
            pygame.mixer.music.load(self.session_params.tone_params[self.num2type(trial_type)])
            pygame.mixer.music.play()
            if trial_type == self.default_params.params['shock_id']:
                threading.Timer((self.default_params.params['cs_duration'] - self.default_params.params['shock_duration']),\
                                 self.shockCtrl).start()
            self.pause(self.trial_duration[trial_num])
            self.print_lock.acquire()
            print("\r\b\b\b========================")
            self.print_lock.release()
        self.terminate.set()
        self.print_lock.acquire()
        print("\bEnd Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.print_lock.release()
        SerialManager.close(self.connection)
        pygame.mixer.quit()

    def run(self):
        self.ready      = threading.Event()
        self.terminate  = threading.Event()
        self.print_lock = threading.Lock()
        self.cam_thread = threading.Thread(target=PySpinController.controller,args=(self.ready,self.terminate,self.print_lock))
        self.cam_thread.setDaemon(True)
        self.cam_thread.start()
        self.ready.wait()
        self.print_lock.acquire()
        print("\bStart Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.print_lock.release()
        self.start_time = time.time()
        self.pause(self.params['baseline'])
        self.session()

    def ledCtrl(self):
        import time
        self.print_lock.acquire()
        print("\bledON", time.time() - self.trial_start)
        self.print_lock.release()
        self.a.digitalWrite(self.ledPin, self.a.HIGH)
        self.pause(self.default_params.params['cs_duration'])
        self.a.digitalWrite(self.ledPin, self.a.LOW)
        self.print_lock.acquire()
        print("\bledOFF", time.time() - self.trial_start)
        self.print_lock.release()

    def shockCtrl(self):
        import time
        self.print_lock.acquire()
        print("\bshockON", time.time() - self.trial_start)
        self.print_lock.release()
        self.a.digitalWrite(self.shockerPin, self.a.HIGH)
        self.pause(self.default_params.params['shock_duration'])
        self.a.digitalWrite(self.shockerPin, self.a.LOW)
        self.print_lock.acquire()
        print("\bshockOFF", time.time() - self.trial_start)
        self.print_lock.release()

def main(a,connection,session_params,cameraPin=12,shockerPin=11,ledPin=10):
    main_app = MainApp(a,connection,session_params,cameraPin,shockerPin,ledPin)
    main_app.fetch_defaults()
    main_app.run()
# -*- coding: utf-8 -*-

# %% Import toolboxes
import os
import uuid
import time
import random
import pickle
import pygame
import threading
import matplotlib
import numpy as np
import PySpinController
matplotlib.use("Qt5Agg")
from PyQt5 import QtCore
from itertools import groupby
from datetime import datetime
import matplotlib.pyplot as plt
from screeninfo import get_monitors
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

# %% Default Parameters class
class DefaultParams:
    """
    This class generates and stores session-type specific parameters and
    randomizes trial and ISI structure for each session. Parameters and
    randomized trial timing (i.e., trial start times) are saved to the temporary
    working directory using day-by-day naming conventions.
    :param session_type: Type of session requested for generation by MouseRunner.
    :type session_type: str
    :param shock: Determines whether shocks are delivered on conditioning days (equivalent to NOT mouse.naive).
    :type shock: bool
    """
    def __init__(self,session_type,shock):
        self.params = self.habituation() if session_type == 'Habituation' else\
                      self.conditioning(shock) if session_type == 'Conditioning' else\
                      self.ofc() if session_type == 'OFC' else\
                      self.recall() if session_type == 'Recall' else self.rerecall()
        print(self.params)
        self.trial_generator()
        self.isi_generator()
        self.trialize()

    def trial_generator(self):
        """
        This function generates pseudo-random trials of equal numbers of each
        trial type listed in class attribute PARAMS. Trial generation is repeated
        until no more than two back-to-back trials of a single trial-type are
        present.
        """
        trials_nonrandom = np.repeat(self.params['cs_ids'],self.params['cs_repeats']).tolist()
        while True:
            if self.params['random']:
                self.trials = random.sample(trials_nonrandom,len(trials_nonrandom))                    # random sample without replacement of all trials for randomized tone presentation
                max_consecutive = max([sum(1 for _ in group) for _, group in groupby(self.trials)])
                if max_consecutive > 2 or len(np.unique(trials_nonrandom) == 1):
                    continue
            else:
                self.trials = self.params['order']
            self.iter_trials = iter(self.trials)
            return

    def isi_generator(self):
        """
        This function generates pseudo-random ISIs for each trial, drawing from
        a normal distribution around the average ISI listed in class attribute
        PARAMS with a standard deviation listed in the same attribute. ISI
        generation is repeated until no ISI less than one-half the average
        ISI is present.
        """
        while True:
            if self.params['random']:
                self.isis = np.random.normal(self.params['avg_isi'],
                                             self.params['std_isi'],
                                             len(self.trials))
                if any (isi < (self.params['avg_isi'] / 2) for isi in self.isis):
                    continue
            else:
                self.isis = self.params['timing']
            return

    def trialize(self):
        """
        This function generates an array of trial start times from previously
        generated trial types and ISIs. By definition, the first trial start
        time is equivalent to the baseline period listed in class attribute
        PARAMS.
        """
        self.trial_duration    = self.isis + self.params['cs_duration']
        self.iter_duration     = iter(self.trial_duration)
        self.trial_start_times = np.array([self.params['baseline'],*self.trial_duration[:-1]])
        self.trial_start_times = list(self.trial_start_times.cumsum())

    def save(self,save_params,mice):
        """
        This function stores previously generated trial timing data and session
        parameters to the temporary working directory using day-by-day naming
        conventions.
        :param save_params: Packaged parameters for saving to appropriate directory using appropriate naming conventions.
        :type save_params: dict
        :param mice: Mouse name(s) formatted for saving conventions.
        :type mice: str
        """
        np.savetxt(os.path.join(save_params['tmp_path'],"day{}-{}-timing.csv".format(save_params['day'],mice)),
                               [self.trials,self.trial_start_times],
                                delimiter =", ",
                                fmt ='% s')
        with open(os.path.join(save_params['tmp_path'],"day{}-{}-params.pickle".format(save_params['day'],mice)),'wb') as fi:
                               pickle.dump(self.params,fi,protocol=pickle.HIGHEST_PROTOCOL)

    def habituation(self):
        """
        This function returns easily editable session parameters for
        HABITUATION sessions to fill out DEFAULT PARAMS class. All parameters
        are stored for future analyses. Shock ID must match a single CS ID or
        be none-type. Stimulus number refers to iterations of EACH CS ID.
        All times are in seconds.
        """
        return {'session_type'        : 'Habituation',
                'baseline'            : 180,
                'avg_isi'             : 60,
                'std_isi'             : 15,
                'cs_duration'         : 30,
                'cs_ids'              : (0,1,2),
                'cs_repeats'          : (8,4,4),
                'shock_duration'      : 1.0,
                'shock_id'            : None,
                'shock'               : False,
                'laser'               : False,
                'laser_addl_duration' : 10,
                'random'              : False,
                'order'               : [0, 0, 2, 0, 1, 2, 1, 0, 2, 0, 1, 1, 0, 2, 0, 0],
                'timing'              : np.array([ 74.82176945, 55.41945447, 61.75785047, 47.52070435,
                                                   54.23889192, 45.71200062, 57.34069709, 59.77877237,
                                                   74.32395161, 57.81340795, 53.45014845, 75.49022935,
                                                   59.69082781, 66.50032699, 60.45184117, 44.26133661])}

    def conditioning(self,shock):
        """
        This function returns easily editable session parameters for
        CONDITIONING sessions to fill out DEFAULT PARAMS class. All parameters
        are stored for future analyses. Shock ID must match a single CS ID or
        be none-type. Stimulus number refers to iterations of EACH CS ID.
        All times are in seconds.
        """
        return {'session_type'        : 'Conditioning',
                'baseline'            : 300,
                'avg_isi'             : 120,
                'std_isi'             : 15,
                'cs_duration'         : 30,
                'cs_ids'              : (1,),
                'cs_repeats'          : (5,),
                'shock_duration'      : 1.0,
                'shock_id'            : 1,
                'shock'               : True if shock else False,
                'laser'               : False,
                'laser_addl_duration' : 10,
                'random'              : False,
                'order'               : [1, 1, 1, 1, 1],
                'timing'              : np.array([ 138.59428872,  99.48363471, 111.33151715,
                                                   103.11090328, 102.50545536])}

    def ofc(self):
        """
        This function returns easily editable session parameters for
        OFC sessions to fill out DEFAULT PARAMS class. All parameters
        are stored for future analyses. Shock ID must match a single CS ID or
        be none-type. Stimulus number refers to iterations of EACH CS ID.
        All times are in seconds.
        """
        return {'session_type'        : 'OFC',
                'baseline'            : 300,
                'avg_isi'             : 120,
                'std_isi'             : 15,
                'cs_duration'         : 30,
                'cs_ids'              : (2,),
                'cs_repeats'          : (10,),
                'shock_duration'      : 1.0,
                'shock_id'            : 2,
                'shock'               : True,
                'laser'               : False,
                'laser_addl_duration' : 10,
                'random'              : False,
                'order'               : [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
                'timing'              : np.array([ 136.549197  , 118.39688651,  95.44064276, 138.42647164,
                                                   100.0653403 , 114.56076754, 112.07743622, 102.34976023,
                                                   112.15625473, 129.26775207])}

    def recall(self):
        """
        This function returns easily editable session parameters for
        RECALL sessions to fill out DEFAULT PARAMS class. All parameters
        are stored for future analyses. Shock ID must match a single CS ID or
        be none-type. Stimulus number refers to iterations of EACH CS ID.
        All times are in seconds.
        """
        return {'session_type'        : 'Recall',
                'baseline'            : 300,
                'avg_isi'             : 120,
                'std_isi'             : 15,
                'cs_duration'         : 30,
                'cs_ids'              : (0,1,2),
                'cs_repeats'          : (5,5,5),
                'shock_duration'      : 1.0,
                'shock_id'            : None,
                'shock'               : False,
                'laser'               : False,
                'laser_addl_duration' : 10,
                'random'              : False,
                'order'               : [0, 1, 2, 2, 0, 1, 0, 2, 1, 1, 0, 2, 2, 1, 0],
                'timing'              : np.array([ 106.15497496, 130.30779892, 123.2206702 , 126.98051646,
                                                   118.87659538, 137.89354629, 122.39318269, 118.42617231,
                                                   153.93937124, 124.51276133, 120.82135785, 120.17697217,
                                                   143.93220819, 120.35970326, 119.84290389])}

    def rerecall(self):
        """
        This function returns easily editable session parameters for
        RERECALL sessions to fill out DEFAULT PARAMS class. All parameters
        are stored for future analyses. Shock ID must match a single CS ID or
        be none-type. Stimulus number refers to iterations of EACH CS ID.
        All times are in seconds.
        """
        return {'session_type'        : 'Re-recall',
                'baseline'            : 300,
                'avg_isi'             : 120,
                'std_isi'             : 15,
                'cs_duration'         : 30,
                'cs_ids'              : (0,2),
                'cs_repeats'          : (5,5),
                'shock_duration'      : 1.0,
                'shock_id'            : None,
                'shock'               : False,
                'laser'               : False,
                'laser_addl_duration' : 10,
                'random'              : False,
                'order'               : [2, 0, 2, 0, 0, 2, 0, 2, 2, 0],
                'timing'              : np.array([ 122.36021167, 139.0579861 , 131.38335911, 112.62238674,
                                                   113.06786161, 115.37928829, 113.20774832, 108.72449678,
                                                   110.91079537, 124.25052878])}

class Plot:

    def __init__(self,params):
        self.trials       = np.array(params.trials)
        self.intervals    = params.trial_duration
        self.baseline     = params.params['baseline']
        self.shock_id     = params.params['shock_id']
        self.title        = params.params['session_type']
        self.shock_trials = np.where(self.shock_id == self.trials, 1, 0)
        self.x_array      = [trial + 1 for trial in range(len(self.trials))]
        self.norm_trials  = (self.trials - np.min(self.trials))\
                          / (np.max(self.trials) - np.min(self.trials)) if\
                            len(np.unique(self.trials)) > 1 else self.trials
        self.colors       = plt.cm.rainbow(self.norm_trials)
        self.edgecolors   = ['black' if is_shock else 'None' for is_shock in self.shock_trials]
        self.scatter_left = None
        self.scatter      = None

    def init_plot(self,monitor=get_monitors(),display_w=1200,display_h=450):
        plt.ion()
        self.monitor_w = next(iter(monitor)).width
        self.geometry = (self.monitor_w - display_w + 8, display_h + 15) + (display_w, int(display_h / 2))
        self.fig       = plt.figure(figsize=(12,2),dpi=100)
        self.ax        = self.fig.add_subplot(111)
        self.window    = plt.get_current_fig_manager().window
        self.window.setGeometry(*self.geometry)

    def start_baseline(self):
        self.scatter  = plt.scatter(x=self.x_array,\
                                    y=self.trials,s=500,\
                                    facecolors=self.edgecolors,\
                                    linewidth=3,edgecolor=self.colors)
        plt.title('%s' % self.title)
        plt.ylim([-1,3])
        plt.xlim([min(self.x_array) - 1, max(self.x_array) + 1])
        plt.yticks(ticks=[0,1,2],labels=['CS Minus','CS Plus One','CS Plus Two'])
        plt.xticks([])
        plt.show(block=False)
        plt.pause(self.baseline)

    def plot(self):
        self.init_plot()
        self.window.setWindowFlags(self.window.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.window.show()
        self.window.setWindowFlags(self.window.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.window.show()
        self.start_baseline()
        for (counter,trial_num) in enumerate(self.x_array):
            try:
                while len(self.ax.lines) > 0:
                    self.ax.lines.pop()
                    self.scatter_left.set_visible = False
                    self.scatter.set_visible = False
            except:
                pass
            plt.axvline(x=trial_num,ymin=0,ymax=1,color='black',zorder=0)
            self.scatter_left = plt.scatter(x=self.x_array[0:trial_num],\
                                            y=self.trials[0:trial_num],s=500,\
                                            c=self.colors[0:trial_num],
                                            marker='o',linewidth=3,\
                                            edgecolor=self.edgecolors[0:trial_num])
            self.this_scatter = plt.scatter(x=self.x_array[trial_num:],\
                                            y=self.trials[trial_num:],s=500,\
                                            facecolors=self.edgecolors[trial_num:],\
                                            linewidth=3,edgecolor=self.colors[trial_num:])
            plt.title('%s' % self.title)
            plt.ylim([-1,3])
            plt.xlim([min(self.x_array) - 1, max(self.x_array) + 1])
            plt.yticks(ticks=[0,1,2],labels=['CS Minus','CS Plus One','CS Plus Two'])
            plt.xticks([])
            plt.show(block=False)
            plt.pause(self.intervals[counter])
        plt.close()

class MainApp:
    """
    This class initializes the session log, generates and saves session
    parameters and trial structure, manages audio, laser, shocker, and LED
    output, and oversees all behavioral operations.
    :param a: Previously initialized Arduino API.
    :type a: class nanpy.arduinoapi.ArduinoApi
    :param connection: Serial port connection to previously assigned device.
    :type connection: class nanpy.serialmanager.SerialManager
    :param session_params: Tone, save, and session-specific parameters packaged for ease of access.
    :type session_params: class __main__.SessionParams
    :param laserPin: Arduino pin designated for laser output trigger.
    :type laserPin: int
    :param shockerPin: Arduino pin designated for shocker output trigger.
    :type shockerPin: int
    :param ledPin: Arduino pin designated for LED output trigger.
    :type ledPin: int
    """
    def __init__(self,a,connection,session_params,plot_queue,laserPin,shockerPin,ledPin):
        self.a            = a
        self.connection   = connection
        self.params       = session_params
        self.plot_queue   = plot_queue
        self.laserPin     = laserPin
        self.shockerPin   = shockerPin
        self.ledPin       = ledPin
        self.rig          = str(uuid.UUID(int=uuid.getnode()))
        self.mice = next(iter(self.params.save_params['mice'])) if len(self.params.save_params['mice']) == 1 else\
                    '+'.join(self.params.save_params['mice'])
        self.log  = open(os.path.join(self.params.save_params['tmp_path'],"day{}-{}-log.txt".format(self.params.save_params['day'],self.mice)),"a")
        self.balance_audio()

    def balance_audio(self):
        if self.rig in {'00000000-0000-0000-0000-7085c259e003'}: # rig 1
            self.audio_params = {0: 1.0, 1: 0.90, 2: 0.65}
        elif self.rig in {'00000000-0000-0000-0000-908d6e5d0a5e'}: # rig 2
            self.audio_params = {0: 1.0, 1: 0.85, 2: 0.55}
        else: # any other computer
            self.audio_params = {0: 1.0, 1: 1.0 , 2: 1.0 }

    def fetch_defaults(self):
        """
        This function initializes and saves a DefaultParams object to generate
        all session parameters according to previously defined class attribute
        SESSION_PARAMS.
        """
        self.default_params = DefaultParams(self.params.session_type,self.params.shock)
        self.default_params.save(self.params.save_params,self.mice)
        print(self.default_params.trials)
        print(self.default_params.trial_start_times)

    def generate_liveplot(self):
        """
        This function generates a plot object using information from previously
        defined class attribute DEFAULT_PARAMS.
        """
        self.plot = Plot(self.default_params)

    def pause(self,pause):
        """
        This function is a prettier version of time.sleep with (currently)
        no additional functionality.
        """
        time.sleep(pause)

    def num2type(self,trial_type):
        """
        This function converts int-type trial assignment to string-type trial
        names for generation of trial-type specific tone generation appropriate
        to specific mouse tone assignments.
        """
        trial_type = 'cs1' if trial_type == 1 else \
                     'cs2' if trial_type == 2 else 'cs_minus'
        return trial_type

    def session(self):
        """
        This function oversees all session operations, controlling and logging
        audio, laser, shocker, and LED outputs according to data assigned to
        class attributes DEFAULT_PARAMS and PARAMS. Actual trial start times
        (t=(Cue Start - Pre-Laser Cue Duration)) are recorded and saved, along
        with shocker status and trial type.
        """
        actual_cs_start=[]
        cue=[]
        shock=[]
        for trial_num in range(len(self.default_params.trials)):
            trial_type     = next(self.default_params.iter_trials)
            trial_duration = next(self.default_params.iter_duration)
            self.print_lock.acquire()
            print("========================", file=self.log)
            print("Trial: {}, Type: {}".format(trial_num,trial_type), file=self.log)
            print("\r\b\b\b========================")
            print("Trial: {}, Type: {}".format(trial_num,trial_type))
            self.print_lock.release()
            self.trial_start = time.time()
            if self.default_params.params['laser']:
                threading.Thread(target=self.laserCtrl).start()
            self.pause(self.default_params.params['laser_addl_duration'])
            threading.Thread(target=self.ledCtrl).start()
            pygame.mixer.init()
            tone   = pygame.mixer.Sound(self.params.tone_params[self.num2type(trial_type)])
            volume = self.audio_params[trial_type]
            tone.set_volume(volume)
            tone.play()
            actual_cs_start.append(time.time() - self.start_time)
            cue.append(trial_type)
            if trial_type == self.default_params.params['shock_id'] and self.default_params.params['shock']:
                threading.Timer((self.default_params.params['cs_duration'] - self.default_params.params['shock_duration']),\
                                  self.shockCtrl).start()
                shock.append(1)
            else:
                shock.append(0)
            self.pause(trial_duration - self.default_params.params['laser_addl_duration'])
            self.print_lock.acquire()
            print("========================", file=self.log)
            print("\r\b\b\b========================")
            self.print_lock.release()
        np.savetxt(os.path.join(self.params.save_params['tmp_path'],"day{}-{}-actualtiming.csv".format(self.params.save_params['day'],self.mice)),
                               [cue,shock,actual_cs_start],
                                delimiter =", ",
                                fmt ='% s')
        self.terminate.set()
        self.print_lock.acquire()
        print("End Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file=self.log)
        print("\bEnd Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.print_lock.release()
        pygame.mixer.quit()

    def run(self):
        """
        This function initializes all Spinnaker Camera devices in separate threads
        and holds all behavioral operations until receiving a change of state
        event from the camera threads signaling that the device parameters have
        been adjusted and that the cameras are ready for image acquisition.
        Following a baseline period previously defined in class attribute
        DEFAULT_PARAMS, behavior is initiated and completed, after which the
        logger is elegantly closed.
        """
        self.ready      = threading.Event()
        self.terminate  = threading.Event()
        self.print_lock = threading.Lock()
        self.cam_thread = threading.Thread(target=PySpinController.controller,args=(self.ready,self.terminate,self.print_lock,self.params))
        self.cam_thread.setDaemon(True)
        self.cam_thread.start()
        self.ready.wait()
        self.print_lock.acquire()
        print("Start Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file=self.log)
        print("\bStart Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.print_lock.release()
        self.start_time = time.time()
        self.plot_queue.put(self.plot)
        self.pause(self.default_params.params['baseline'] - self.default_params.params['laser_addl_duration'])
        self.session()
        self.log.close()

    def laserCtrl(self):
        """
        This function controls the Arduino output pin designated for laser
        trigger control, turning the laser on and off according to parameters
        assigned in class attribute DEFAULT_PARAMS and logging all operations.
        """
        import time
        # self.print_lock.acquire()
        print("laserON", time.time() - self.trial_start, file=self.log)
        print("\blaserON", time.time() - self.trial_start)
        # self.print_lock.release()
        self.a.digitalWrite(self.laserPin, self.a.HIGH)
        self.pause(self.default_params.params['laser_addl_duration'])
        self.pause(self.default_params.params['cs_duration'])
        self.pause(self.default_params.params['laser_addl_duration'])
        self.a.digitalWrite(self.laserPin, self.a.LOW)
        # self.print_lock.acquire()
        print("laserOFF", time.time() - self.trial_start, file=self.log)
        print("\blaserOFF", time.time() - self.trial_start)
        # self.print_lock.release()

    def shockCtrl(self):
        """
        This function controls the Arduino output pin designated for shocker
        trigger control, turning the shocker on and off according to parameters
        assigned in class attribute DEFAULT_PARAMS and logging all operations.
        """
        import time
        # self.print_lock.acquire()
        print("shockON", time.time() - self.trial_start, file=self.log)
        print("\bshockON", time.time() - self.trial_start)
        # self.print_lock.release()
        self.a.digitalWrite(self.shockerPin, self.a.HIGH)
        self.pause(self.default_params.params['shock_duration'])
        self.a.digitalWrite(self.shockerPin, self.a.LOW)
        # self.print_lock.acquire()
        print("shockOFF", time.time() - self.trial_start, file=self.log)
        print("\bshockOFF", time.time() - self.trial_start)
        # self.print_lock.release()

    def ledCtrl(self):
        """
        This function controls the Arduino output pin designated for LED
        trigger control, turning the LED on and off according to parameters
        assigned in class attribute DEFAULT_PARAMS and logging all operations.
        """
        import time
        # self.print_lock.acquire()
        print("ledON", time.time() - self.trial_start, file=self.log)
        print("\bledON", time.time() - self.trial_start)
        # self.print_lock.release()
        self.a.digitalWrite(self.ledPin, self.a.HIGH)
        self.pause(self.default_params.params['cs_duration'])
        self.a.digitalWrite(self.ledPin, self.a.LOW)
        # self.print_lock.acquire()
        print("ledOFF", time.time() - self.trial_start, file=self.log)
        print("\bledOFF", time.time() - self.trial_start)
        # self.print_lock.release()

def main(a,connection,session_params,plot_queue,laserPin=4,shockerPin=7,ledPin=8):
    """
    This function is the highest level behavioral controller, initializing the
    behavior app MainApp, fetching default parameters, and starting the session.
    :param a: Previously initialized Arduino API.
    :type a: class nanpy.arduinoapi.ArduinoApi
    :param connection: Serial port connection to previously assigned device.
    :type connection: class nanpy.serialmanager.SerialManager
    :param session_params: Tone, save, and session-specific parameters packaged for ease of access.
    :type session_params: class __main__.SessionParams
    :param laserPin: Arduino pin designated for laser output trigger.
    :type laserPin: int
    :param shockerPin: Arduino pin designated for shocker output trigger.
    :type shockerPin: int
    :param ledPin: Arduino pin designated for LED output trigger.
    :type ledPin: int
    """
    main_app = MainApp(a,connection,session_params,plot_queue,laserPin,shockerPin,ledPin)
    main_app.fetch_defaults()
    main_app.generate_liveplot()
    main_app.run()
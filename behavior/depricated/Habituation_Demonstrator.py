# -*- coding: utf-8 -*-

# %% Import toolboxes
from nanpy import (ArduinoApi, SerialManager)
from itertools import groupby
from datetime import datetime
from PySpinMeta import meta
import numpy as np
import threading
import pygame
import time
import random
import os

# %% LED
def ledCtrl(startTime,a,ledPin,csDuration):
    import time
    print("ledON", time.time() - startTime)
    a.digitalWrite(ledPin, a.HIGH)
    time.sleep(csDuration)
    a.digitalWrite(ledPin, a.LOW)
    print("ledOFF", time.time() - startTime)

# %% Trial Generator
def trial_generator(allTrials,stimNum):
    while True:    
        trialType       = random.sample(allTrials,stimNum*3)                       # random sample without replacement of all trials for randomized tone presentation
        max_consecutive = max([sum(1 for _ in group) for _, group in groupby(trialType)])
        if max_consecutive > 2:
            continue
        else:
            return trialType

# %% ISI Generator
def isi_generator(avgIsi,stdIsi,stimNum):
    while True:    
        isiDuration = np.random.normal(avgIsi,stdIsi,stimNum*3)
        if any (isi < (avgIsi/2) for isi in isiDuration):
            continue
        else:
            return isiDuration

def run(tmp_path,a,connection,cameraPin=12,shockerPin=11,ledPin=10):
    # %% Assign parameters
    ## Randomly assign stimulus order for given # of trials
    ready            = threading.Event()
    terminate        = threading.Event()
    stimNum          = 4                                                           # set the number of tone presentations
    baselineDuration = 180                                                         # set the duration of baseline (AKA ISI to first CS start) (s)
    avgIsi           = 60
    stdIsi           = 15
    csDuration       = 30
    shockDuration    = 1.0
    
    ## Assign stimulus tone files
    csPlusOne = 'E:\\Experiments\\tones\\pips_7500Hz_2Hz_30s.wav'
    csPlusTwo = 'E:\\Experiments\\tones\\upsweeps_2Hz_30s_4-16kHz.wav'
    csMinus   = 'E:\\Experiments\\tones\\White_noise_30s.wav'
    
    # %% Assign pseudo-random trial structure and timing
    ## Assign pseudo-random trial order with balanced CS exposure
    allTrials = [*[0 for i in range(stimNum)],*[1 for i in range(stimNum)],\
                 *[2 for i in range(stimNum)]]                                     # equal number of 0, 1, 2 trial types where 0 is CS-, 1 is CS +1, 2is CS+2
    trialType = trial_generator(allTrials,stimNum)
    

    ## Assign trial timing
    isiDuration   = isi_generator(avgIsi,stdIsi,stimNum)
    trialDuration = isiDuration + csDuration
    csTimePoint   = np.array([baselineDuration,*trialDuration])
    csTimePoint   = list(csTimePoint.cumsum())
    
    ## Save ideal CS timing
    print(trialType)
    print(csTimePoint)
    print(isiDuration)
    np.savetxt(os.path.join(tmp_path,"day1-timing.csv"), 
               [trialType,csTimePoint[0:-1]],
               delimiter =", ", 
               fmt ='% s')
    
    # %% Arduino
    ## Establish CTRL Arduino connection
    pygame.mixer.quit()                                                            # ensure that pygame.mixer is not running to enable setting of sound params
    pygame.mixer.pre_init(44100, -16, 1, 2048)                                     # frequency, bit depth, channels, cache
    # a.pinMode(cameraPin, a.OUTPUT)
    # a.digitalWrite(cameraPin, a.LOW)
    
    # %% Trials
    ## Start trials
    threading.Thread(target=meta,args=(ready,terminate)).start()
    ready.wait()
    print("start " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    expStartTime = time.time()
    
    # a.digitalWrite(cameraPin, a.HIGH)
    
    #a.digitalWrite(cameraPin, a.LOW)
    time.sleep(baselineDuration - 2.0) 
    nowTime = time.time()
    while (nowTime - expStartTime) < (baselineDuration):
        nowTime = time.time()
    
    
    for i in range(stimNum*3):
        print(i,":",trialType[i])
        if trialType[i] == 0:
            startTime = time.time()
            nowTime = time.time()
            print(time.time()-expStartTime)
            pygame.mixer.init()
            pygame.mixer.music.load(csMinus)
            pygame.mixer.music.play()
            threading.Timer(0, ledCtrl, [startTime,a,ledPin,csDuration]).start()
            print(time.time()-expStartTime)
            time.sleep(csDuration - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < csDuration:
                nowTime = time.time()

            time.sleep(isiDuration[i] - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < trialDuration[i]:
                nowTime = time.time()
        elif trialType[i] == 1:
            startTime = time.time()
            nowTime = time.time()
            print(time.time()-expStartTime)
            pygame.mixer.init()
            pygame.mixer.music.load(csPlusOne)
            pygame.mixer.music.play()
            threading.Timer(0, ledCtrl, [startTime,a,ledPin,csDuration]).start()
            print(time.time()-expStartTime)
            time.sleep(csDuration - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < csDuration:
                nowTime = time.time()

            time.sleep(isiDuration[i] - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < trialDuration[i]:
                nowTime = time.time()
        else: 
            startTime = time.time()
            nowTime = time.time()
            print(time.time()-expStartTime)
            pygame.mixer.init()
            pygame.mixer.music.load(csPlusTwo)
            pygame.mixer.music.play()
            threading.Timer(0, ledCtrl, [startTime,a,ledPin,csDuration]).start()
            print(time.time()-expStartTime)
            time.sleep(csDuration - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < csDuration:
                nowTime = time.time()

            time.sleep(isiDuration[i] - 2.0)
            nowTime = time.time()
            while (nowTime - startTime) < trialDuration[i]:
                nowTime = time.time()
    
    #a.digitalWrite(cameraPin, a.LOW)
    
    terminate.set()
    #SerialManager.flush_input(connection)
    #SerialManager.close(connection)
    # pygame.mixer.quit()
    print("end " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("difference", (time.time() - expStartTime) - (csTimePoint[-1]))
    
    time.sleep(5) 

        
    SerialManager.close(connection)
    
    pygame.mixer.quit()
    
    
    


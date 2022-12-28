"""
Code adapted from: https://github.com/SondreKindem/PySimpleGUI-video-player-with-OpenCV/blob/master/VideoPlayer.py
and https://github.com/israel-dryer/Media-Player
"""

import pdb
import os
import re
import vlc
import glob
import pickle
import operator
import itertools
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
from os import listdir
from scipy import stats
from pathlib import Path
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from collections import namedtuple
from sys import platform as PLATFORM
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')

### TODO
# Set save method
# Analyze data output
# Make 'Stop' meaningful

def open_window(title,layout,w,h,icon=None):
    sg.theme('BlueMono')  
    window = sg.Window(title,layout,finalize=True,size=(w,h), 
                       element_justification='center',icon=icon)
    window.BringToFront()
    return window

def gen_stats(data,test):
    data_types   = list(map(operator.attrgetter('datatype'),data))
    data_values  = list(map(operator.attrgetter('values'),data))
    data_df      = pd.DataFrame(dict(zip(data_types,data_values)))
    if test == 'anova':
        anova        = stats.f_oneway(*[data_df[dtype].values for dtype in data_types])
        data_df_melt = pd.melt(data_df.reset_index(),id_vars=['index'],value_vars=data_types)
        data_df_melt.columns = ['index', 'datatype', 'value']
        tukeyhsd     = pairwise_tukeyhsd(endog=data_df_melt.value,groups=data_df_melt.datatype,alpha=0.05)
        tukeyhsd_df  = pd.DataFrame(data=tukeyhsd._results_table.data[1:],\
                                    columns=tukeyhsd._results_table.data[0])
        return anova.pvalue,tukeyhsd_df
    else:
        t = stats.ttest_ind(*[dat.values for dat in data])
        return t.pvalue
       
def p2text(p):
    if p < 0.001:
        text = '***'
    elif p < 0.01:
        text = '**'
    elif p < 0.05:
        text = '*'
    else:
        text = 'ns (p={:0.2f})'.format(p)
    return text
    
def annotate(fig,x_pos,data,comparison_p,anova_p=None,offset=0.05):
    data_types   = list(map(operator.attrgetter('datatype'),data))
    data_values  = list(map(operator.attrgetter('values'),data))
    bar_pairs    = list(itertools.combinations(x_pos, 2))
    compbars     = list()
    for (start_loc,stop_loc) in bar_pairs:
        values   = list((data_values[start_loc],data_values[stop_loc]))
        maxheight= max(list(map(max,values)))
        if compbars:
            if maxheight in list(map(operator.attrgetter('height'),compbars)):
                compbar       = ComparisonBar(start_loc,stop_loc,maxheight)
                old_bar_range = [cb for cb in compbars if cb.height == maxheight][0].range
                maxheight     = maxheight + 0.15 if compbar.range > old_bar_range else maxheight - 0.15
        y      = maxheight + offset
        uppery = y + offset
        if anova_p:
            dtypes = (data_types[start_loc],data_types[stop_loc])
            p      = comparison_p[((comparison_p.group1 == dtypes[0])  & \
                                   (comparison_p.group2 == dtypes[1])) | \
                                  ((comparison_p.group1 == dtypes[1])  & \
                                   (comparison_p.group2 == dtypes[0]))]['p-adj'].values[0]
        else:
            p = comparison_p
        fig.add_subplot(111).plot([start_loc,start_loc,stop_loc,stop_loc], [y,uppery,uppery,y], c='black')
        fig.add_subplot(111).text(np.mean((start_loc,stop_loc)),uppery + offset/2,p2text(p),fontsize=14,horizontalalignment='center')
        compbars.append(ComparisonBar(start_loc,stop_loc,maxheight))
        
class ComparisonBar(namedtuple('ComparisonBar', 'start stop height')):
    __slots__ = ()
    @property
    def range(self):
        return abs(self.stop - self.start)

class Trial(namedtuple('Trial', 'cage day trial')):
    __slots__ = ()
    @property
    def filename(self):
        return 'D{}C{}T{}'.format(self.day,self.cage,self.trial)
    def __hash__(self):
        return hash(self.filename)
    def __eq__(self, other):
        return self.cage == other.cage and self.day == other.day and self.trial == other.trial

class GroupData(namedtuple('DataType', 'datatype mean sem values')):
    __slots__ = ()

class MouseCage():
    
    def __init__(self,cage_id,df_keys):
        self.cage_id          = cage_id
        self.trials_stored    = set()
        self.mouse_winner_fig = None
        self.side_winner_fig  = None
        self.entry_winner_fig = None
        self.mid_winner_fig   = None
        self.data             = pd.DataFrame(np.nan,index=[trial + 1 for trial in range(8)],
                                             columns=df_keys)

    def update_cage_data(self,trial_data):
        trial_as_row              = [trial_data.mouse_one_winner,trial_data.mouse_two_winner,\
                                     trial_data.left_winner,trial_data.right_winner,\
                                     trial_data.first_entry_winner,trial_data.second_entry_winner,\
                                     trial_data.simult_entry,trial_data.first_middle_winner,\
                                     trial_data.second_middle_winner,trial_data.simult_middle]
        trial                     =  trial_data.trial if int(trial_data.day) == 1 else str(int(trial_data.trial) + 4)
        self.data.loc[int(trial)] =  trial_as_row
        self.data.loc[int(trial)] =  self.data.loc[int(trial)].astype(int)
        self.trials_stored.add(Trial(self.cage_id,trial_data.day,trial_data.trial).filename)
        
class TrialData:
    
    def __init__(self,day,trial,values):
        self.day                  = day
        self.trial                = trial
        self.mouse_one_winner     = values['ONE']
        self.mouse_two_winner     = values['TWO']
        self.left_winner          = values['LEFT']
        self.right_winner         = values['RIGHT']
        self.first_entry_winner   = values['FIRSTENTRY']
        self.second_entry_winner  = values['SECONDENTRY']
        self.simult_entry         = values['SIMULTANEOUSENTRY']
        self.first_middle_winner  = values['FIRSTMIDDLE']
        self.second_middle_winner = values['SECONDMIDDLE']
        self.simult_middle        = values['SIMULTANEOUSMIDDLE']
        
class MainApp:
    
    def __init__(self,videotype='.avi'):
        self.theme          = 'BlueMono'
        self.path           = './Assets/'
        self.buttons        = {img[:-4].upper(): self.path + img for img in listdir(self.path)}
        self.background     = self.path + 'background2.png'
        self.icon           = self.path + 'player.ico'
        self.videotype      = videotype
        self.num_videos     = 0
        self.current_video  = 0
        self.save_data      = True
        self.reanalyze_data = False
        self.final_pause    = False
        self.figures_agg    = list()
        self.group_data     = dict()
        self.video_path     = None
        self.w              = None
        self.h              = None
        self.cage_id        = None
        self.day            = None
        self.trial          = None
        self.cage           = None
        self.videos         = None
        self.figures        = None
        self.canvases       = None
        self.group_figures  = None
        self.group_canvases = None
        self.group_analysis = None
        self.group_bool     = False
        self.group_mouse_winner_fig = None
        self.group_side_winner_fig  = None
        self.group_entry_winner_fig = None
        self.group_mid_winner_fig   = None
        
        self.df_keys        = ['mouse1winner','mouse2winner',\
                               'left_winner','right_winner',\
                               'first_entry_winner',\
                               'second_entry_winner',\
                               'simult_entry',\
                               'first_middle_winner',\
                               'second_middle_winner',\
                               'simult_middle']
                              
        self.window         = self.open_main_app().Finalize()
        self.check_platform()
        self.run_analysis()
    
    def generate_player_button(self, sg_key, button_name):
        return sg.Button(image_filename=self.buttons[button_name],\
                         border_width=0,pad=(0, 0),key=sg_key,
                         button_color=('white', sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']))
    
    def open_main_app(self):
        self.vlc_instance = vlc.Instance()
        self.list_player  = self.vlc_instance.media_list_player_new()
        self.media_list   = self.vlc_instance.media_list_new([])
        self.list_player.set_media_list(self.media_list)
        self.player  = self.list_player.get_media_player()
        w, h         = sg.Window.get_screen_size()
        load_title   = 'Loading'
        load_text    = [[sg.Text('Loading Mouse Runner...')]]
        load         = open_window(load_title,load_text,int(w/3),int(h/3))
        self.w,self.h= int(w/1.3), int(h/1.3)
        title        = 'Analyze Tube Test Behavioral Data'
        layout_player= [[self.generate_player_button('SKIPTOPREVIOUS', 'START'),
                         self.generate_player_button('PAUSE', 'PAUSE_OFF'),
                         self.generate_player_button('PLAY', 'PLAY_OFF'),
                         self.generate_player_button('STOP', 'STOP'),
                         self.generate_player_button('SKIPTONEXT', 'END')]]
        layout_left  = sg.Column([[sg.Text('Cage ID: {}'.format(self.cage),\
                                           justification='center',\
                                           font='Helvetica 11 bold',\
                                           key='CAGEID'),
                                   sg.Text('Day: {}'.format(self.day),\
                                           justification='center',\
                                           font='Helvetica 11 bold',\
                                           key='DAY'),
                                   sg.Text('Trial: {}'.format(self.trial),\
                                           justification='center',\
                                           font='Helvetica 11 bold',\
                                           key='TRIAL'),
                                   sg.Text('Save Inputs:',\
                                           justification='center',\
                                           font='Helvetica 11 bold'),
                                   sg.Button(image_filename=(self.buttons['BUTTON_ON2'] if self.save_data else self.buttons['BUTTON_OFF2']),\
                                             key='SAVEBUTTON',button_color=(sg.theme_background_color(),\
                                             sg.theme_background_color()),border_width=0)],
                                  [sg.HorizontalSeparator()],
                                  [sg.Text('Trial Winner Number',size=(20,1),\
                                           justification='right'),\
                                   sg.Radio('One','WINNERNUMBER',default=True,\
                                        key='ONE',size=(7,1)),
                                   sg.Radio('Two','WINNERNUMBER',default=False,\
                                        key='TWO',size=(7,1))],
                                  [sg.Text('Trial Winner Side',size=(20,1),\
                                           justification='right'),\
                                   sg.Radio('Left','WINNERSIDE',default=True,\
                                        key='LEFT',size=(7,1)),
                                   sg.Radio('Right','WINNERSIDE',default=False,\
                                        key='RIGHT',size=(7,1))],  
                                  [sg.Text('Trial Winner Tube Entry',size=(20,1),\
                                           justification='right'),\
                                   sg.Radio('First','WINNERENTRY',default=True,\
                                        key='FIRSTENTRY',size=(7,1)),
                                   sg.Radio('Second','WINNERENTRY',default=False,\
                                        key='SECONDENTRY',size=(7,1)),
                                   sg.Radio('Simulataneous','WINNERENTRY',default=False,\
                                        key='SIMULTANEOUSENTRY',size=(15,1))],
                                  [sg.Text('Trial Winner Tube Middle',size=(20,1),\
                                           justification='right'),\
                                   sg.Radio('First','WINNERMIDDLE',default=True,\
                                        key='FIRSTMIDDLE',size=(7,1)),
                                   sg.Radio('Second','WINNERMIDDLE',default=False,\
                                        key='SECONDMIDDLE',size=(7,1)),
                                   sg.Radio('Simulataneous','WINNERMIDDLE',default=False,\
                                        key='SIMULTANEOUSMIDDLE',size=(15,1))],
                                  [sg.HorizontalSeparator()],
                                  [sg.Canvas(key='WINNERNUMBERFIG',size=(self.w/20,self.h/20)),\
                                   sg.Canvas(key='WINNERSIDEFIG',size=(self.w/20,self.h/20))],
                                  [sg.Canvas(key='WINNERENTRYFIG',size=(self.w/20,self.h/10)),\
                                   sg.Canvas(key='WINNERMIDDLEFIG',size=(self.w/20,self.h/10))]])
        layout_right = sg.Column([[sg.In(default_text='',enable_events=True,\
                                         key='VIDEOPATH'),
                                   sg.FolderBrowse('Select Video Directory',\
                                                   target='VIDEOPATH'),
                                   sg.Text('Re-analyze Stored Data:',\
                                           justification='center',\
                                           font='Helvetica 11 bold'),
                                   sg.Button(image_filename=(self.buttons['BUTTON_ON2'] if self.reanalyze_data else self.buttons['BUTTON_OFF2']),\
                                             key='LOADBUTTON',button_color=(sg.theme_background_color(),\
                                             sg.theme_background_color()),border_width=0)],
                                  [sg.Image(filename=self.background,pad=(0,5),\
                                            size=(self.w/1.75, self.h/1.75),\
                                            key='CANVAS')],
                                  [sg.Text('00:00', key='TIMEELAPSED'),
                                   sg.Slider(range=(0, 1), enable_events=True, resolution=0.0001, disable_number_display=True,
                                             background_color='#83D8F5', orientation='h', key='TIME'),
                                   sg.Text('00:00', key='TIMETOTAL'),
                                   sg.Text('          ', key='TRACKS')],
                                  [sg.Column(layout_player)],
                                  [sg.Button("Preview Group-Level Analysis",key="PREVIEWBUTTON")]],
                                   element_justification='center')
        layout = [[layout_left,sg.VSeperator(pad=(0,0)),layout_right]]
        load.close()
        window = open_window(title,layout,self.w,self.h,self.icon)
        window['TIME'].expand(expand_x=True)
        return window
    
    def check_platform(self):
        if PLATFORM.startswith('linux'):
            self.player.set_xwindow(self.window['CANVAS'].Widget.winfo_id())
        else:
            self.player.set_hwnd(self.window['CANVAS'].Widget.winfo_id())
            
    def add_media(self, video):
        media = self.vlc_instance.media_new(video)
        media.set_meta(0, video.replace('\\', '/').split('/').pop())
        media.set_meta(1, 'Local Media')
        media.set_meta(10, video)
        self.media_list.add_media(media)
        self.num_videos = self.media_list.count()
        self.window.read(1)
        if self.num_videos == 1:
            self.current_video = 1
            self.list_player.play()
            self.window['PLAY'].update(image_filename=self.buttons['PLAY_ON'])

    def get_meta(self, meta_type):
        media = self.player.get_media()
        return media.get_meta(meta_type)

    def get_track_info(self):
        time_elapsed = "{:02d}:{:02d}".format(*divmod(self.player.get_time() // 1000, 60))
        time_total = "{:02d}:{:02d}".format(*divmod(self.player.get_length() // 1000, 60))
        if self.player.is_playing():
            self.window['TIMEELAPSED'].update(time_elapsed)
            self.window['TIME'].update(self.player.get_position())
            self.window['TIMETOTAL'].update(time_total)
            self.window['TRACKS'].update('{} of {}'.format(self.current_video, self.num_videos))

    def update_trial_info(self):
        filename     = Path(self.get_meta(0)).stem
        fileparts    = re.split('C|D|T',filename)
        self.day     = fileparts[2]
        self.cage_id = fileparts[3]
        self.trial   = fileparts[4]
        self.window.find_element('CAGEID').Update('Cage ID: {}'.format(self.cage_id))
        self.window.find_element('DAY').Update('Day: {}'.format(self.day))
        self.window.find_element('TRIAL').Update('Trial: {}'.format(self.trial))
        if not self.cage_id in self.cage_data:
            self.cage = MouseCage(self.cage_id,self.df_keys)
        else:
            self.cage = self.cage_data[self.cage_id]
        self.figures  = [self.cage.mouse_winner_fig,self.cage.side_winner_fig,
                         self.cage.entry_winner_fig,self.cage.mid_winner_fig]
        self.canvases = (self.window['WINNERNUMBERFIG'].TKCanvas,
                         self.window['WINNERSIDEFIG'].TKCanvas,
                         self.window['WINNERENTRYFIG'].TKCanvas,
                         self.window['WINNERMIDDLEFIG'].TKCanvas)
    
    def save_button(self):
        self.save_data = not self.save_data
        self.window['SAVEBUTTON'].update(image_filename=(self.buttons['BUTTON_ON2'] if self.save_data else self.buttons['BUTTON_OFF2']))

    def load_button(self):
        self.reanalyze_data = not self.reanalyze_data
        self.window['LOADBUTTON'].update(image_filename=(self.buttons['BUTTON_ON2'] if self.reanalyze_data else self.buttons['BUTTON_OFF2']))
    
    def play(self):
        self.list_player.play()
        self.window['PLAY'].update(image_filename=self.buttons['PLAY_ON'])
        self.window['PAUSE'].update(image_filename=self.buttons['PAUSE_OFF'])

    def stop(self):
        self.player.stop()
        self.window['PLAY'].update(image_filename=self.buttons['PLAY_OFF'])
        self.window['PAUSE'].update(image_filename=self.buttons['PAUSE_OFF'])
        self.window['TIME'].update(value=0)
        self.window['TIMEELAPSED'].update('00:00')

    def pause(self):
        self.window['PAUSE'].update(
            image_filename=self.buttons['PAUSE_ON'] if self.player.is_playing() else self.buttons['PAUSE_OFF'])
        self.window['PLAY'].update(
            image_filename=self.buttons['PLAY_OFF'] if self.player.is_playing() else self.buttons['PLAY_ON'])
        self.player.pause()

    def skip_to_next(self):
        self.list_player.next()
        self.reset_pause_play()
        if not self.num_videos == self.current_video:
            self.current_video += 1
            self.update_trial_info()
        else:
            self.group_level_analysis()

    def skip_to_previous(self):
        self.list_player.previous()
        self.reset_pause_play()
        if not self.current_video == 1:
            self.current_video -= 1

    def reset_pause_play(self):
        self.window['PAUSE'].update(image_filename=self.buttons['PAUSE_OFF'])
        self.window['PLAY'].update(image_filename=self.buttons['PLAY_ON'])

    def load_videos(self):
        if self.video_path is None:
            return
        else:
            try: 
                with open(os.path.join(self.video_path,'cage_data.pickle'), 'rb') as handle:
                    self.cage_data = pickle.load(handle)
            except FileNotFoundError:
                self.cage_data = dict()
            if self.videos is None:
                self.videos = glob.glob(self.video_path+"/**/*{}".format(self.videotype),recursive=True)
                if not self.reanalyze_data:
                    # pdb.set_trace()
                    trials_stored = list(itertools.chain.from_iterable([cage.trials_stored for cage in self.cage_data.values()]))
                    self.videos   = [video for video in self.videos if not any(trial_stored in video for trial_stored in trials_stored)]
                    self.videos   = sorted(self.videos, key = lambda x: re.split('C|D|T',Path(x).stem)[3])
                else:
                    self.videos   = sorted(self.videos, key = lambda x: re.split('C|D|T',Path(x).stem)[3])
                for video in self.videos:
                    self.add_media(video.replace('\\','/'))
                    if not self.player.is_playing:
                        self.play()
                        self.window['PLAY'].update(image_filename=self.buttons['PLAY_ON'])
            else:
                new_videos = glob.glob(self.video_path+"/**/*{}".format(self.videotype),recursive=True)
                if not self.reanalyze_data:
                    trials_stored = list(itertools.chain.from_iterable([cage.trials_stored for cage in self.cage_data.values()]))
                    new_videos    = [video for video in new_videos if not any(trial_stored in video for trial_stored in trials_stored)]
                    new_videos    = [video for video in new_videos if video not in self.videos]
                    new_videos    = sorted(new_videos, key = lambda x: re.split('C|D|T',Path(x).stem)[3])
                else:
                    new_videos    = sorted(new_videos, key = lambda x: re.split('C|D|T',Path(x).stem)[3])
                self.videos.extend(new_videos)
                for video in new_videos:
                    self.add_media(video.replace('\\','/'))
                    if not self.player.is_playing:
                        self.play()
                        self.window['PLAY'].update(image_filename=self.buttons['PLAY_ON'])
        self.num_videos = self.media_list.count()

    def save_trial_data(self,values):
        trial_data = TrialData(self.day,self.trial,values)
        self.cage.update_cage_data(trial_data)
        self.cage_data[self.cage_id] = self.cage
        with open(os.path.join(self.video_path,'cage_data.pickle'), 'wb') as handle:
            pickle.dump(self.cage_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    def draw_plots(self):
        if not self.group_bool:
            for (idx,(figure,canvas)) in enumerate(zip(self.figures,self.canvases)):
                figure_canvas_agg = FigureCanvasTkAgg(figure,canvas)
                figure_canvas_agg.draw()
                figure_canvas_agg.get_tk_widget().pack(side='top',fill='both',expand=1)
                self.figures_agg.append(figure_canvas_agg)
        else:
            for (idx,(figure,canvas)) in enumerate(zip(self.group_figures,self.group_canvases)):
                figure_canvas_agg = FigureCanvasTkAgg(figure,canvas)
                figure_canvas_agg.draw()
                figure_canvas_agg.get_tk_widget().pack(side='top',fill='both',expand=1)
            
    def single_plot(self,data,bars,title,colors,size=(3.5,3.5)):
        fig   = matplotlib.figure.Figure(figsize=size)
        x_pos = np.arange(len(bars))
        for (pos,(dat,col)) in enumerate(zip(data,colors)):
            try:
                fig.add_subplot(111).bar(x_pos[pos],dat.mean(),\
                                         align='center',alpha=0.5,color=col,\
                                         yerr=dat.sem())
            except TypeError:
                fig.add_subplot(111).bar(x_pos[pos],dat.mean,\
                                         align='center',alpha=0.5,color=col,\
                                         yerr=dat.sem,zorder=1)
        if self.group_bool:
            ax          = fig.add_subplot(111)
            #scatter_dat = [(x_pos[pos],\
                            #dat.values[trial]) for trial in range(len(dat.values))]
            scatter_dat = np.concatenate(list(map(operator.attrgetter('values'),data))).ravel()
            scatter_df  = pd.DataFrame({'x_pos': np.repeat(x_pos,repeats=len(dat.values)),'values': scatter_dat})
            #fig.add_subplot(111).scatter(*zip(*scatter_dat),color='None',edgecolors='black',zorder=2)
            sns.swarmplot(x='x_pos',y='values',data=scatter_df,ax=ax,color='None',edgecolor='black')
            ax.set(xlabel=None)
            ax.set(ylabel=None)
            if len(data) > 2:
                ax.set(xlim=(-0.5,2.5))
                p, tukey = gen_stats(data,'anova')
                annotate(fig,x_pos,data,comparison_p=tukey,anova_p=p)
            else:
                ax.set(xlim=(-0.5,1.5))
                p = gen_stats(data,'t')
                annotate(fig,x_pos,data,comparison_p=p)
        fig.add_subplot(111).patch.set_facecolor(sg.theme_background_color())
        fig.add_subplot(111).set_xticks(x_pos)
        fig.add_subplot(111).set_xticklabels(bars,rotation=65)
        fig.add_subplot(111).set_yticks([0,0.2,0.4,0.6,0.8,1.0])
        fig.add_subplot(111).set_ylim([0,1.5])
        fig.add_subplot(111).set_title(title,fontsize=14)
        fig.patch.set_facecolor(sg.theme_background_color())
        fig.subplots_adjust(bottom=0.22)
        return fig
    
    def delete_plots(self):
        for figure in self.figures_agg:
            figure.get_tk_widget().forget()
            plt.close('all')
        self.figures_agg = list()
    
    def update_live_plots(self):
        if self.figures_agg:
            self.delete_plots()
        
        self.cage.mouse_winner_fig = self.single_plot(list((self.cage.data.mouse1winner,\
                                                            self.cage.data.mouse2winner)),\
                                                          ('Mouse 1','Mouse 2'),\
                                                           'Wining Mouse Number',\
                                                          ('black','fuchsia'),\
                                                          (3.5,4.5))
        self.cage.side_winner_fig  = self.single_plot(list((self.cage.data.left_winner,\
                                                            self.cage.data.right_winner)),\
                                                          ('Left','Right'),\
                                                           'Winning Mouse Side',\
                                                          ('black','fuchsia'),\
                                                          (3.5,4.5))
        self.cage.entry_winner_fig = self.single_plot(list((self.cage.data.first_entry_winner,\
                                                            self.cage.data.second_entry_winner,\
                                                            self.cage.data.simult_entry)),\
                                                          ('First','Second','Simultaneous'),\
                                                           'Winning Mouse Entry Order',\
                                                          ('black','fuchsia','gold'),\
                                                          (3.5,4.5))
        self.cage.mid_winner_fig   = self.single_plot(list((self.cage.data.first_middle_winner,\
                                                            self.cage.data.second_middle_winner,\
                                                            self.cage.data.simult_middle)),\
                                                          ('First','Second','Simultaneous'),\
                                                           'Winning Mouse Middle Order',\
                                                          ('black','fuchsia','gold'),\
                                                          (3.5,4.5))
        self.figures  = [self.cage.mouse_winner_fig,self.cage.side_winner_fig,
                         self.cage.entry_winner_fig,self.cage.mid_winner_fig]
        self.draw_plots()
    
    def popup_yes_no(self):
        layout = [[sg.Text('Finalize cage-level analysis and initiate group-level analysis?',\
                   size=(30, 3),justification='center')],
                  [sg.Button('Yes'), sg.Button('No')]]
        popup  = open_window('Finalize Analysis',layout,int(self.w/6),int(self.h/6))
        e,v = popup.read()
        popup.close()
        return e == 'Yes'
    
    def group_and_plot(self):
        for key in self.df_keys:
            self.group_data[key] = GroupData(key,self.group_analysis.groupby(level=['cagename'])[key].mean().mean(),
                                             self.group_analysis.groupby(level=['cagename'])[key].mean().sem(),
                                             self.group_analysis.groupby(level=['cagename'])[key].mean().values)
            
        self.group_mouse_winner_fig = self.single_plot(list((self.group_data['mouse1winner'],\
                                                             self.group_data['mouse2winner'])),\
                                                           ('Mouse 1','Mouse 2'),\
                                                            'Wining Mouse Number',\
                                                           ('black','fuchsia'),\
                                                           (3.5,4.5))
        self.group_side_winner_fig  = self.single_plot(list((self.group_data['left_winner'],\
                                                             self.group_data['right_winner'])),\
                                                           ('Left','Right'),\
                                                            'Winning Mouse Side',\
                                                           ('black','fuchsia'),
                                                           (3.5,4.5))
        self.group_entry_winner_fig = self.single_plot(list((self.group_data['first_entry_winner'],\
                                                             self.group_data['second_entry_winner'],\
                                                             self.group_data['simult_entry'])),\
                                                           ('First','Second','Simultaneous'),\
                                                            'Winning Mouse Entry Order',\
                                                           ('black','fuchsia','gold'),\
                                                           (3.5,4.5))
        self.group_mid_winner_fig   = self.single_plot(list((self.group_data['first_middle_winner'],\
                                                             self.group_data['second_middle_winner'],\
                                                             self.group_data['simult_middle'])),\
                                                           ('First','Second','Simultaneous'),\
                                                            'Winning Mouse Middle Order',\
                                                           ('black','fuchsia','gold'),\
                                                           (3.5,4.5))
        group_layout        = [[sg.Canvas(key='WINNERNUMBERGROUPFIG',size=(int(self.w/20),int(self.h/20))),\
                                sg.Canvas(key='WINNERSIDEGROUPFIG',size=(int(self.w/20),int(self.h/20)))],
                               [sg.Canvas(key='WINNERENTRYGROUPFIG',size=(int(self.w/20),int(self.h/10))),\
                                sg.Canvas(key='WINNERMIDDLEGROUPFIG',size=(int(self.w/20),int(self.h/10)))],
                               [sg.Button('Save Figure',key='SAVEANALYSIS'),\
                                sg.Button('Close',key='CLOSEANALYSIS')]]
        group_window        = open_window('Group-level Analysis',group_layout,int(self.w/2.75),int(self.h/1.2))
        self.group_figures  = [self.group_mouse_winner_fig,self.group_side_winner_fig,
                               self.group_entry_winner_fig,self.group_mid_winner_fig]
        self.group_canvases = (group_window['WINNERNUMBERGROUPFIG'].TKCanvas,
                               group_window['WINNERSIDEGROUPFIG'].TKCanvas,
                               group_window['WINNERENTRYGROUPFIG'].TKCanvas,
                               group_window['WINNERMIDDLEGROUPFIG'].TKCanvas)
        self.draw_plots()
        self.group_bool = False
        while True:
            e,v = group_window.read()
            if e in (sg.WINDOW_CLOSED, 'Exit', 'CLOSEANALYSIS'):
                group_window.close()
                break
            elif e == 'SAVEANALYSIS':
                figure_names = ['winnernumber.svg','winnerside.svg',\
                                'winnerentry.svg','winnermiddle.svg']
                for (figure,name) in zip(self.group_figures,figure_names):
                    figure.savefig(os.path.join(self.video_path,name),format='svg',dpi=1200)
                group_window.close()
                break
    
    def group_level_analysis(self,preview=False):
        if not preview:
            analyze_group = self.popup_yes_no()
        else:
            analyze_group = True
        if analyze_group:
            self.group_bool = True
            try:
                self.group_analysis = pd.concat([cage.data for cage in self.cage_data.values()],\
                                                keys=self.cage_data.keys(),\
                                                names=['cagename']).apply(pd.to_numeric)
                self.group_and_plot()
            except ValueError:
                error_window = open_window('Error',[[sg.Text('No data to display!')]],int(self.w/6),int(self.h/6))
                e,v = error_window.read()
                error_window.close()
                self.group_bool = False

    def run_analysis(self):
        while True:  
            if (self.player.get_position() > 0.99995) and (not self.final_pause):
                self.pause()
                self.final_pause = True
            event, values = self.window.Read(timeout=50)
            self.get_track_info()
            if event in (sg.WINDOW_CLOSED, 'Exit', 'Cancel'):
                self.window.close()
                break
            elif event == 'PREVIEWBUTTON':
                self.group_level_analysis(preview=True)
            elif event == 'SAVEBUTTON':
                self.save_button()
            elif event == 'LOADBUTTON':
                self.load_button()
            elif event == 'VIDEOPATH':
                self.video_path = values['VIDEOPATH']
                try:
                    self.load_videos()
                    self.update_trial_info()
                    self.update_live_plots()
                except AttributeError:
                    self.group_level_analysis()
                pdb.set_trace()
            elif event == 'PLAY':
                    self.play()
                    self.final_pause = False if self.final_pause else self.final_pause
            elif event == 'PAUSE':
                    self.pause() 
            elif event == 'STOP':
                    self.stop()
            elif event == 'TIME':
                    self.player.set_position(values['TIME'])
            elif event in ('SKIPTONEXT', 'SKIPTOPREVIOUS'):
                if event == 'SKIPTONEXT':
                    if self.save_data:
                        self.save_trial_data(values)
                    if not self.day == 2 and self.trial == 4:
                        self.update_live_plots()
                        self.skip_to_next()
                    else:
                        self.skip_to_next()
                        self.update_live_plots()
                if event == 'SKIPTOPREVIOUS':
                    self.skip_to_previous()
                    self.update_trial_info()
                    self.update_live_plots()
                self.final_pause = False




MainApp()
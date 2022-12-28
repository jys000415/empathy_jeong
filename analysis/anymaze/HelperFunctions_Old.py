import os
import glob
import itertools
import PySimpleGUI as sg
from pathlib import Path
import ClassDefinitions as Classes

folder_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABnUlEQVQ4y8WSv2rUQRSFv7vZgJFFsQg2EkWb4AvEJ8hqKVilSmFn3iNvIAp21oIW9haihBRKiqwElMVsIJjNrprsOr/5dyzml3UhEQIWHhjmcpn7zblw4B9lJ8Xag9mlmQb3AJzX3tOX8Tngzg349q7t5xcfzpKGhOFHnjx+9qLTzW8wsmFTL2Gzk7Y2O/k9kCbtwUZbV+Zvo8Md3PALrjoiqsKSR9ljpAJpwOsNtlfXfRvoNU8Arr/NsVo0ry5z4dZN5hoGqEzYDChBOoKwS/vSq0XW3y5NAI/uN1cvLqzQur4MCpBGEEd1PQDfQ74HYR+LfeQOAOYAmgAmbly+dgfid5CHPIKqC74L8RDyGPIYy7+QQjFWa7ICsQ8SpB/IfcJSDVMAJUwJkYDMNOEPIBxA/gnuMyYPijXAI3lMse7FGnIKsIuqrxgRSeXOoYZUCI8pIKW/OHA7kD2YYcpAKgM5ABXk4qSsdJaDOMCsgTIYAlL5TQFTyUIZDmev0N/bnwqnylEBQS45UKnHx/lUlFvA3fo+jwR8ALb47/oNma38cuqiJ9AAAAAASUVORK5CYII='
file_icon = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABU0lEQVQ4y52TzStEURiHn/ecc6XG54JSdlMkNhYWsiILS0lsJaUsLW2Mv8CfIDtr2VtbY4GUEvmIZnKbZsY977Uwt2HcyW1+dTZvt6fn9557BGB+aaNQKBR2ifkbgWR+cX13ubO1svz++niVTA1ArDHDg91UahHFsMxbKWycYsjze4muTsP64vT43v7hSf/A0FgdjQPQWAmco68nB+T+SFSqNUQgcIbN1bn8Z3RwvL22MAvcu8TACFgrpMVZ4aUYcn77BMDkxGgemAGOHIBXxRjBWZMKoCPA2h6qEUSRR2MF6GxUUMUaIUgBCNTnAcm3H2G5YQfgvccYIXAtDH7FoKq/AaqKlbrBj2trFVXfBPAea4SOIIsBeN9kkCwxsNkAqRWy7+B7Z00G3xVc2wZeMSI4S7sVYkSk5Z/4PyBWROqvox3A28PN2cjUwinQC9QyckKALxj4kv2auK0xAAAAAElFTkSuQmCC'

def groupbylist(*args, **kwargs):
    """
    Credit: https://stackoverflow.com/a/20013133
    """
    return [Classes.GroupedFiles(k, Classes.Files(list(g))) for k, g in itertools.groupby(*args, **kwargs)]

def open_window(title,layout,w,h):
    sg.theme('BlueMono')  
    window = sg.Window(title,layout,finalize=True,size=(w,h), 
                       element_justification='center')
    return window

def filetree_search(path=r'J:/Jacob Dahan/MouseRunner/retired',width=60):
    """
    Credit: https://github.com/PySimpleGUI/PySimpleGUI/issues/4393
    """
    def short(file, width):
        return file[:width//2-3] + '...' + file[-width//2:] if len(file)>width else file

    def create_win(path):
        files = sorted(sorted(Path(path).iterdir()), key=lambda x:Path(x).is_file())
        treedata = sg.TreeData()
        for i, file in enumerate(files):
            f = str(file)
            treedata.insert("", i, short(f, width-8), [f], icon=folder_icon if Path(f).is_dir() else file_icon)
        layout = [[sg.Tree(data=treedata, headings=['Notes',], pad=(0, 0),\
                           show_expanded=True, col0_width=width, auto_size_columns=False,\
                           visible_column_map=[False,], select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
                           num_rows=15, row_height=20, font=('Courier New', 10), key="TREE")],
                  [sg.Button('OK'), sg.Button('Cancel'), sg.Button('UP')]]
        window = sg.Window("Select files or directories", layout, modal=True, finalize=True)
        tree = window['TREE']
        tree.Widget.configure(show='tree')
        tree.bind("<Double-1>", "_DOUBLE_CLICK")
        while True:
            event, values = window.read()
            if event == 'TREE_DOUBLE_CLICK':
                if values['TREE'] != []:
                    value = values['TREE'][0]
                    path = treedata.tree_dict[value].values[0]
                    if Path(path).is_dir():
                        result = path
                        break
                continue
            elif event in (sg.WINDOW_CLOSED, 'Cancel'):
                result = []
            elif event == 'OK':
                result = [treedata.tree_dict[i].values[0] for i in values['TREE']]
                result = result if result else [str(Path(path))]
                break
            elif event == 'UP':
                result = str(Path(path).parent)
            break
        window.close()
        return result

    while True:
        result = create_win(path)
        if isinstance(result, str):
            path = result
        else:
            break
    return result

def generate_GUI_layout():
    w, h      = sg.Window.get_screen_size()
    load_title= 'Loading'
    load_text = [[sg.Text('Loading file selector...')]]
    load      = open_window(load_title,load_text,int(w/3),int(h/3))
    w, h      = int(w/2.5), int(h/8)
    layout    = [[sg.Text('Session Timing Path:',size=(23,1),justification='right'),
                  sg.In(default_text='',\
                        enable_events=True,key='SESSIONPATH'),
                  sg.Button('Select File/Directory',target='SESSIONPATH',size=(23,1))],
                 [sg.Text('AnyMaze Analysis Path:',size=(23,1),justification='right'),
                  sg.In(default_text='',\
                        enable_events=True,key='ANYMAZEPATH'),
                  sg.Button('Select File/Directory',target='ANYMAZEPATH',size=(23,1))],
                 [sg.Text('Note: AnyMaze path defaults to Session path if left blank!')],
                 [sg.OK()]]
    load.close()
    return (w, h, layout)

def run_gui():
    SessionFilePath = list()
    AnymazeFilePath = list()
    w, h, layout = generate_GUI_layout()
    main = open_window('Select Session and Anymaze Files',layout,w,h)
    main.BringToFront()
    while True:
        event, values = main.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            main.close()
            return None, None
        if event == 'SESSIONPATH':
            SessionFilePath = filetree_search()
            main.find_element('SESSIONPATH').Update(SessionFilePath)
        if event == 'ANYMAZEPATH':
            AnymazeFilePath = filetree_search()
            main.find_element('ANYMAZEPATH').Update(AnymazeFilePath)
        if event == 'OK':
            try:
                AnymazeFilePath = AnymazeFilePath if AnymazeFilePath else SessionFilePath 
                main.close()
                return SessionFilePath, AnymazeFilePath
            except NameError:
                print('At a minimum, the Session path must be defined.')

def validate_inputs(SessionFiles,AnymazeFiles):
    if all(InputType in (list,tuple) for InputType in (type(SessionFiles),type(AnymazeFiles))):
        return
    else:
        raise TypeError('File or Folder input arguments must be of type LIST or TUPLE when bypassing GUI.')

def data_load(SessionFilePath,AnymazeFilePath,identifier,filetype):
    SessionFiles = list()
    AnymazeFiles = list()
    if all(os.path.isdir(r"{}".format(FilePath)) for FilePath in list(itertools.chain.from_iterable((SessionFilePath,AnymazeFilePath)))):
        for (SessionFP, AnymazeFP) in zip(SessionFilePath, AnymazeFilePath): 
            SessionFiles.extend(glob.glob(SessionFP+"/**/*{}.{}".format(identifier,filetype),recursive=True))
            AnymazeFiles.extend(glob.glob(AnymazeFP+"/**/*{}.{}".format('anymaze',filetype),recursive=True))
    elif all(os.path.isfile(r"{}".format(FilePath)) for FilePath in list(itertools.chain.from_iterable((SessionFilePath,AnymazeFilePath)))):
        SessionFiles.extend(SessionFilePath)
        AnymazeFiles.extend(AnymazeFilePath)
    else:
        raise ValueError('Session and/or Anymaze path input is neither a valid directory nor file path, or are of non-matching path types.')
    return SessionFiles, AnymazeFiles
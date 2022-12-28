from __future__ import annotations

import os
import yaml
import pytest
import datetime
import collections
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from collections.abc import Iterable
from decorators import validate_file, repeat

import pdb


def getNestedAttr(obj : object, attrs : Iterable[str]) -> object:
    if len(attrs) == 1:
        return obj[attrs.pop()]
    attrs = collections.deque(attrs)
    nestedObj = obj
    while attrs:
        nestedObj = nestedObj[attrs.popleft()]
    return nestedObj
        
def setNestedAttr(obj : object, attrs : Iterable[str], val : Any) -> object:
    if len(attrs) == 1:
        obj[attrs.pop()] = val
        return obj
    attrs = collections.deque(attrs)
    nestedObj = obj
    while len(attrs) > 1:
        nestedObj = nestedObj[attrs.popleft()]
    nestedObj[attrs.popleft()] = val
    return obj

class Converter:
    
    def __init__(self, expression : str):
        self.expression = expression
        self.knownConversions = {'np.array'     , 'list' , 'tuple', 
                                 'pd.DataFrame' , 'float', 'int'   } 
        
    def convert(self, val : Any) -> Any:
        if self.expression not in self.knownConversions:
            raise ValueError(f'Unknown conversion type: {self.expression}')
        if self.expression == 'np.array':
            return np.array(val)
        if self.expression == 'list':
            return list(val)
        if self.expression == 'tuple':
            return tuple(val)
        if self.expression == 'pd.DataFrame':
            return pd.DataFrame(val)
        if self.expression == 'float':
            return float(val)
        if self.expression == 'int':
            return int(val)

class YAML:
    
    def __init__(self, path : str, fileName : str='QAConfig', fileExt : str='yaml'):
        self.filePath = os.path.join(path,f'{fileName}.{fileExt}')
    
    def read(self) -> 'YAML':
        with open(self.filePath, 'r') as yml:
            try: 
                self.doc = yaml.full_load(yml)
            except yaml.constructor.ConstructorError as error:
                print('YAML Error: Some complex datatypes are not supported '
                      'by PyYAML. Only built-in Python datatypes should be '
                      'considered safe. Aborted testing.')
                raise(error)
            return self

    def clean(self) -> 'YAML':
        attrs = self.doc['retype']
        for (field, dtype) in attrs.items():
            attr = getNestedAttr(self.doc,field)
            val = Converter(dtype).convert(attr)
            self.doc = setNestedAttr(self.doc,field,val)
        return self
    
    def fetch_test_set(self, test_type : str, test_id : str='tests') -> Dict[str,list[Tuple[float, ...]]]:
        try:
            return self.doc[test_id]['input'][test_type]
        except KeyError:
            raise KeyError(f'Test {test_type} not configured in QAConfig. Test automatically failed.')
            
    def gen_full_path(self,test_type_num : int) -> str:
        return os.path.join(os.path.abspath(self.doc['path']), f'type{test_type_num}') 


class Files:
    
    def __init__(self, path : str, iters : int, session_parameters : dict):
        self.path = path
        self.iters = iters
        self.session_parameters = session_parameters
        self.session_data = self.gen_session_data()
        self.file_names = self.gen_file_name('actualtiming')

    def gen_session_data(self) -> list[list[float]]:
        return [self.session_parameters['order'],\
                np.full_like(self.session_parameters['order'], 0),\
                self.session_parameters['timing']]  
    
    def gen_trialized_freezing(self, _iter : int, cue_duration : int, 
                               trial_order : list[int], trial_timing : np.ndarray,
                               test : list[Tuple[float, ...]]) -> list[list[str]]:
        
        order, timing = (trial_order[_iter], trial_timing[_iter])
        
        
        pass
            
    def gen_freezing_data(self, test : list[Tuple[float, ...]]) -> list[list[str]]:
        header = ['Timing','Freezing','Not freezing']
        start = [str(datetime.timedelta(seconds=0)),'0','1']
        data = [start]
        
        
        
        data = list(map())
        
        
        
#         content = [start]
#         for (trialID,trialTiming) in zip(order,timing):
#             preStart = trialTiming - (cueDuration / 2)
#             preStartDateTime = str(datetime.timedelta(seconds=preStart))
#             if freezing[trialID][0] > 0:
#                 content.append([preStartDateTime,'1','0'])
#                 if freezing[trialID][0] < 100:
#                     preStop = preStart + ((cueDuration / 2) * (freezing[trialID][0] / 100))
#                     preStopDateTime = str(datetime.timedelta(seconds=preStop))
#                     content.append([preStopDateTime,'0','1'])
#                 else:
#                     trialTimingDateTime = str(datetime.timedelta(seconds=trialTiming))
#                     content.append([trialTimingDateTime,'0','1'])
#             if freezing[trialID][1] > 0:
#                 trialTimingDateTime = str(datetime.timedelta(seconds=trialTiming))
#                 content.append([trialTimingDateTime,'1','0'])
#                 if freezing[trialID][1] < 100:
#                     trialStop = trialTiming + (cueDuration * (freezing[trialID][1] / 100))
#                     trialStopDateTime = str(datetime.timedelta(seconds=trialStop))
#                     content.append([trialStopDateTime,'0','1'])
#                 else:
#                     trialStop = trialTiming + cueDuration
#                     trialStopDateTime = str(datetime.timedelta(seconds=trialStop))
#                     content.append([trialStopDateTime,'0','1'])
#         data = pd.DataFrame(data=content,columns=header)

    @repeat
    def gen_file_name(self, _iter : int, dtype : str) -> str:
        rel_path = os.path.join(f'mouse{_iter}',f'dayX-mouse{_iter}-{dtype}.csv')
        return os.path.join(self.path,rel_path)
    
    @repeat
    @validate_file
    def create_file(self, _iter : int, data : list[list[float]], header : bool=False, index : bool=False) -> str:
        try:
            pd.DataFrame(data=data).to_csv(self.file_names[_iter],header=header,index=index)
            return self.file_names[_iter]
        except OSError:
            raise OSError('Failed to generate and store test data.')

class TestCase:
    
    def __init__(self, test_type : str, yml : 'YAML'):
        self.test_type = test_type
        self.yml = yml
        self.session_files = self.files.init_files().create_file(self.files.session_data)
        self.test_set = self.yml.fetch_test_set(self.test_type)
    
    def init_files(self) -> 'TestCase':
        iters = self.yml.doc['iters']
        session_parameters = self.yml.doc['SessionParameters']
        self.full_path = self.yml.gen_full_path(self.test_type)
        self.files = Files(self.full_path,iters,session_parameters)
        return self
    
    def test_freezing(self, test : list[Tuple[float, ...]]) -> list[Tuple[float, ...]]:
        self.files.file_names = self.files.gen_file_name('anymaze')
        self.anymaze_files = self.files.create_file(self.files.gen_freezing_data(test))
        pdb.set_trace()
    
    def test(self):
        for (test_num,test) in self.test_set.items():
            if self.test_type in {'freezing'}:
                return self.test_freezing(test)
    
def main(path : str=os.getcwd()):
    yml = YAML(path).read().clean()
    output = []
    for test_type in yml.doc['tests']['input']:
        output.append(TestCase(test_type, yml).test())

if __name__ == "__main__":
    main()

        
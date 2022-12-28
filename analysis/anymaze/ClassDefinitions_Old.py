# -*- coding: utf-8 -*-

import inspect
from operator import attrgetter
from operator import itemgetter
import HelperFunctions as Helper
from collections import namedtuple


class MappedMethod:
    """
    This class maps a single method to all elements of an iterable, with both
    *args and **kwargs compatibility.
    :param elements: Elements onto which the method should be applied.
    :type elements: iterable
    :param ret: Determines whether output of method called is returned.
    :type ret: bool
    :param *args: Any args applicabale to the method (will be applied uniformly to all elements).
    :type *args: any (method-dependent)
    :param **kwargs: Any kwargs applicable to the method (will be applied unformly to all elements).
    :type **kwargs: any (method-dependent)
    """
    def __init__(self, elements, ret=False):
        self.elements = elements
        self.ret      = ret
    def __getattr__(self, attr):
        def apply_to_all(*args, **kwargs):
            if self.ret:
                ret = []
                for obj in self.elements:
                    ret.append(getattr(obj, attr)(*args, **kwargs))
                return ret
            else:
                for obj in self.elements:
                    getattr(obj, attr)(*args, **kwargs)
        return apply_to_all

class Parameters():
    def __init__(self,**kwargs):
        self.Set(**kwargs) 
    def Set(self,**kwargs):
        self.__dict__.update(kwargs) 
    def SetAttr(self,label,val):
        self.__dict__[label] = val
    def Fill(ParameterData):
        pass

class AllData():
    pass

class Filters():
    pass
    

class AnalysisStruct():
    def __init__(self,**kwargs):
        self.Set(**kwargs) 
    def Set(self,**kwargs):
        self.__dict__.update(kwargs) 
    def SetAttr(self,label,val):
        self.__dict__[label] = val
    def Display(self):
        for attribute in self.__dict__.keys():
            if not attribute.startswith('__'):
                value = getattr(self, attribute)
                if not callable(value):
                    if not inspect.isclass(type(value)):
                        print(attribute, '=', value)
                    else:
                        print(attribute, '=', value.Display())
    def FillParameters(self,GroupedDataFrame):
        self.Parameters = Parameters().Fill(GroupedDataFrame)
    
class GroupedDataFrame(namedtuple('GroupedDataFrame',*'mouse frame')):
    __slots__ = ()
    
class GroupedFiles(namedtuple('GroupedFiles','mouse_id files')):
    __slots__ = ()
    @property
    def mouse2day(self):
        return self.files.days
    
class Files:
    def __init__(self,files):
        self.files = sorted(files, key=attrgetter('mouse_id'), reverse=False)
        self.days  = list(map(attrgetter('behavior_day'), self.files))
    def isFull(self):
        return True if len(self.files) else False
    def group(self):
        self.groups = Helper.groupbylist(self.files, lambda f: f.mouse_id)
    def return_matches(self,toMatch):
        try:
            return Files(list(itemgetter(*toMatch)(self.files)))
        except AttributeError:
            return Files([itemgetter(*toMatch)(self.files)])

class File(namedtuple('File','filepath mouse_id behavior_day')):
    __slots__ = ()

class ComparisonBar(namedtuple('ComparisonBar', 'start stop height')):
    __slots__ = ()
    @property
    def range(self):
        return abs(self.stop - self.start)

class Statistics(namedtuple('Statistics','mousetype anova_f anova_p tukey')):
    __slots__ = ()

class InterpolatedAnalysis(namedtuple('InterpolatedAnalysis','mousetype data')):
    __slots__ = ()
    @property
    def freezing(self):
        return (self.data.loc['Pre'],\
                self.data.loc['Cue'],\
                self.data.loc['Post'])
            

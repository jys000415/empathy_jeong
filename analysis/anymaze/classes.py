# -*- coding: utf-8 -*-

from collections import namedtuple

class ComparisonBar(namedtuple('ComparisonBar', 'start stop height')):
    __slots__ = ()
    @property
    def range(self):
        return abs(self.stop - self.start)

class Statistics(namedtuple('Statistics','mousetype anova_f anova_p tukey')):
    __slots__ = ()
    
class File(namedtuple('File','filepath mouse_id')):
    __slots__ = ()

class InterpolatedAnalysis(namedtuple('InterpolatedAnalysis','mousetype data')):
    __slots__ = ()
    @property
    def freezing(self):
        return (self.data.loc['Pre'],\
                self.data.loc['Cue'],\
                self.data.loc['Post'])
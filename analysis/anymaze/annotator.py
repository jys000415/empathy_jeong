# -*- coding: utf-8 -*-

import itertools
import numpy as np
from ordered_set import OrderedSet
from statannotations.Annotator import Annotator

def p2text(p):
    if p <= 0.001:
        text = '***'
    elif p < 0.01:
        text = '**'
    elif p < 0.05:
        text = '*'
    else:
        text = 'ns (p={:0.2f})'.format(p)
    return text
    
def annotate(ax,df,statistics,offset=5):
    bar_pairs = np.repeat(list(itertools.combinations(OrderedSet(df.CueStatus.values),2)),repeats=len(df.columns))
    pvalues=list()
    bar_pairs = [[('Pre','CS-'),('Pre','CS+1')],\
                 [('Cue','CS-'),('Cue','CS+1')],\
                 [('Post','CS-'),('Post','CS+1')],\
                 [('Pre','CS-'),('Pre','CS+2')],\
                 [('Cue','CS-'),('Cue','CS+2')],\
                 [('Post','CS-'),('Post','CS+2')],\
                 [('Pre','CS+1'),('Pre','CS+2')],\
                 [('Cue','CS+1'),('Cue','CS+2')],\
                 [('Post','CS+1'),('Post','CS+2')]]
    for pair in bar_pairs:
        key = pair[0][0]
        start_cue = pair[0][1]
        stop_cue  = pair[1][1]
        tukey = statistics[key].tukey
        p = tukey[(((tukey.group1 == start_cue) & (tukey.group2 == stop_cue)) | \
            ((tukey.group2 == start_cue) & (tukey.group1 == stop_cue)))]['p-adj'].values[0]
        pvalues.append(p)
    annotator = Annotator(ax,bar_pairs,data=df,x='CueStatus',y='Value',hue='CueType',\
                          hue_order=['CS-','CS+1','CS+2'],order=['Pre','Cue','Post'])
    annotator.configure(test=None, text_format='simple', loc='inside')
    annotator.set_pvalues_and_annotate(pvalues)
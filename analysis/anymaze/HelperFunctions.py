import os
import re
import glob
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from functools import reduce
from itertools import product
from collections import deque
from collections import defaultdict
import ClassDefinitions as Classes
from statannotations.Annotator import Annotator
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def groupbylist(*args, **kwargs):
    """
    Credit: https://stackoverflow.com/a/20013133
    """
    return [Classes.GroupedFiles(k, Classes.Files(list(g))) for k, g in itertools.groupby(*args, **kwargs)]

def groupby_consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)

def file_load(FilePaths,load_archive,archive_only,data_ids,data_types):
    assert FilePaths, 'No file or directory path(s) specified.'
    if load_archive:
        if 'analysis' not in data_ids:
            data_ids.extend(['analysis'])
        if 'archive' not in data_types:
            data_types.extend(['archive'])
    if archive_only:
        data_ids, data_types = (['analysis'], ['archive'])
    if all(os.path.isdir(r"{}".format(FilePath)) for FilePath in FilePaths):
        SuperFiles = defaultdict(set)
        for FilePath in FilePaths:
            Files = {dtype : glob.glob(FilePath+"/**/*{}.*".format(data_id),\
                                       recursive=True) for (data_id,dtype) in\
                                       zip(data_ids,data_types)}
            for (dtype,files) in Files.items():
                for f in files:
                    SuperFiles[dtype].add(f)
    elif all(os.path.isfile(r"{}".format(FilePath)) for FilePath in FilePaths):
        SuperFiles = {dtype : [FilePath for FilePath in FilePaths if data_id in\
                               FilePath] for (data_id,dtype) in zip(data_ids,data_types)}
    else:
        raise ValueError('Provided paths are either of mixed file/directory types or are not valid.')
    assert all(SuperFiles.values()),'Unable to load files for at least one data type.'
    return SuperFiles

def match_constants(Files,MatchedFiles,data_constants,overwrite_id,key):
    ConstantFiles      = {dtype:list(filter(None,[dtype_file if not key in dtype_file\
                         else None for dtype_file in dtype_files])) for\
                         (dtype,dtype_files) in Files.items() if dtype in data_constants}
    ConstantMouseNames = {dtype:list(map(os.path.basename,map(os.path.dirname,dtype_files)))\
                         for (dtype,dtype_files) in ConstantFiles.items()}
    ConstantsUnlabeled = pd.DataFrame([ConstantMouseNames,ConstantFiles]).to_dict(orient='list')
    ConstantsLabeled   = {dtype:pd.DataFrame(dtype_data).transpose().set_axis(['mouse_id',\
                         'file_path'],axis=1,inplace=False) for\
                         (dtype,dtype_data) in ConstantsUnlabeled.items()}
    MatchedConstants   = reduce(lambda df_n,df_n_plus_one:pd.merge(df_n,df_n_plus_one,\
                               on=['mouse_id']),ConstantsLabeled.values()).set_axis(['mouse_id',\
                               *ConstantsLabeled.keys()],axis=1,inplace=False)
    for header in MatchedFiles.columns.to_list():
        if header in MatchedConstants.columns.to_list() and header not in 'mouse_id':
            MatchedConstants.rename(columns=lambda x: x.replace(header, '{}_{}'.format(header,overwrite_id)), inplace=True)                                                                         
    return MatchedFiles.merge(MatchedConstants, on=['mouse_id']), MatchedConstants.columns.drop('mouse_id').to_list()

def file_sort(Files,data_constants,overwrite_id,key):
    MouseNames         = {dtype:list(map(os.path.basename,map(os.path.dirname,dtype_files)))\
                         for (dtype,dtype_files) in Files.items()}
    SessionDays        = {dtype:[deque(re.split(r'(?<=\d)\D',os.path.basename(dtype_file))).popleft()\
                         if key in dtype_file else None for dtype_file in dtype_files]\
                         for (dtype,dtype_files) in Files.items()}
    FilesUnlabeled     = pd.DataFrame([MouseNames,SessionDays,Files]).to_dict(orient='list')
    FilesLabeled       = {dtype:pd.DataFrame(dtype_data).transpose().set_axis(['mouse_id',\
                         'session_day','file_path'],axis=1,inplace=False).dropna() for\
                         (dtype,dtype_data) in FilesUnlabeled.items() if\
                         not pd.DataFrame(dtype_data).transpose().set_axis(['mouse_id',\
                         'session_day','file_path'],axis=1,inplace=False).dropna().empty}
    MatchedFiles       = reduce(lambda df_n,df_n_plus_one:pd.merge(df_n,df_n_plus_one,\
                               on=['mouse_id','session_day']),FilesLabeled.values()).set_axis(['mouse_id',\
                               'session_day',*FilesLabeled.keys()],axis=1,inplace=False)
    assert not MatchedFiles.empty, 'No complete dataset found for any mouse for any session.'
    if data_constants:
        MatchedFiles, renamed_constants = match_constants(Files,MatchedFiles,data_constants,overwrite_id,key)
        assert set(data_constants).issubset(MatchedFiles.columns.to_list()), 'No complete dataset found for any mouse for any session.'
    return MatchedFiles, renamed_constants    

def anova_compare(df,dtype='normalized_freezing',by='cue',alpha=0.05):
    anova       = stats.f_oneway(*[getattr(df.groupby([by]).get_group(x),dtype) for x in\
                                   getattr(df,by).unique() if len(getattr(df.groupby([by]).get_group(x),dtype)) > 1])
    tukey       = pairwise_tukeyhsd(endog=df[dtype],groups=df[by],alpha=alpha)._results_table.data
    p_values    = pd.DataFrame(data=tukey).T.set_index(0).T['p-adj'].values
    pairs       = pd.DataFrame(data=tukey).T.set_index(0).T[['group1','group2']].values
    pairs_li    = [(str(id1),str(id2)) for (id1,id2) in pairs]
    return anova,p_values,pairs_li

def annotate(ax,df,p_values,pairs,dtype='normalized_freezing',fmt='stars'):
    df        = df.copy()
    df.cue    = df.cue.apply(lambda x: str(x))
    annotator = Annotator(ax,pairs,data=df,x='cue',y=dtype,order=sorted(df.cue.unique().tolist()))
    annotator.configure(test=None,text_format=fmt,loc='outside')
    annotator.set_pvalues_and_annotate(p_values)

def filter_tuples(df,iterables,x,hue):
    firstpass = [(xval,hval) for (xval,hval) in iterables if not df[(df[x] == xval) & (df[hue] == hval)].empty]
    return [(xval,hval) for (xval,hval) in firstpass if len(df[df[x] == xval]) > 1]

def search_tuples(iterables,key_to_find):
    return tuple(filter(lambda x:key_to_find == x[0], iterables)) 
    
def generate_pairs(df,x,hue=None):
    if hue:
        pairs          = list(product(df[x].unique(),df[hue].unique()))
        filtered_pairs = filter_tuples(df,pairs,x,hue)
        matched_pairs  = [search_tuples(filtered_pairs,key) for key in pd.DataFrame(filtered_pairs,columns=[x,hue])[x].unique()]
    else:
        matched_pairs = list(itertools.combinations(df[x].unique(),2))
        matched_pairs = [(str(id1),str(id2)) for (id1,id2) in matched_pairs]
    return matched_pairs
    
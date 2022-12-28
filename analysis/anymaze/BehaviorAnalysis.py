import os
import pdb
import FileHandler as Handler
import ClassDefinitions as Classes

def AnalysisBehavior(GUI=True,archive=True,load_archive=False,archive_only=False,\
                     data_ids=['actualtiming', 'anymaze', 'dlc', 'params', 'genotype', 'virus', 'special'],\
                     data_types=['session', 'anymaze', 'dlc', 'parameters', 'genotype', 'virus', 'special'],\
                     data_constants=['parameters','genotype','virus','special'],\
                     similar_group_ids=['virus'],similar_groups=[['AAV5-CamKII-eGFP','AAV5-CamKII-eYFP']],\
                     group_order=['genotype','cs1','cs2','special','virus','session_day','mouse_type'],\
                     overwrite_id='constant',key='day',manual_files=[],default_dir=os.getcwd()):
    """
    This function is the top-level controller of all behavioral analysis
    functions, enabling file collection and filtering, returning any warnings
    for missing data, and sorting and parsing data, as well as supervising 
    plotting functions.
    :param GUI: Boolean controller for GUI use, set to TRUE by default. If 
        FALSE, manual data input will be used.
    :type GUI: bool 
    :param archive: Boolean controller for archiving, set to TRUE by default. 
        If TRUE, will store Analysis files in mouse home directories for 
        efficient data re-loading.
    :type archive: bool 
    :param load_archive: Boolean controller for archiving, set to FALSE by
        default. If TRUE, archived Analysis files will override loading of
        previously analyzed files.
    :type load_archive: bool 
    :param archive_only: Boolean controller for archiving, set to FALSE by
        default. If TRUE, only archived Analysis files will be loaded, even if
        other files were present in the selected directory.
    :type archive_only: bool 
    :param data_ids: Unique identifier strings found in names of each filetype
        to be loaded into Analysis structure.
    :type data_ids: list
    :param data_types: Unique identifier names for each file type to be loaded 
        into Analysis structure.
    :type data_types: list
    :param data_constants: Unique identifier names for each file type
        that is NOT session-specific to be loaded into Analysis structure.
        Set to EMPTY list if no constants used.
    :type data_constants: list
    :param similar_group_ids: Unique identifier names for each file type that
        has multiple, joinable groups. Set to EMPTY list if no group merges
        needed.
    :type similar_group_ids: list
    :param similar_groups: LIST of LISTS of mergable groups, in order of
        corresponding SIMILAR_GROUP_IDS. These groups will be merged for analysis
        and treated as identical values.
    :param group_order: Specific ordering for PANDAS GROUBY analyses, such that
        data will be sorted and grouped by the categories specified. Note that
        all group names MUST match a DATA_TYPE parameter with the sole
        exception of SESSION_DAY, which is generated regardless of DATA_TYPES.
    :type group_order: list
    :param overwrite_id: Unique identifier string appended to END of
        any CONSTANT file IDs that are identical to session-wise file IDs.
        Used for naming Analysis DataFrame columns. (Example: Overlapping
        session-wise parameters ID `params` and mouse constant parameters
        ID `params` are separated by the appended string.)
    :type overwrite_id: string
    :param key: Non-unique identifier for all session-specific
        file types to be loaded into Analysis structure.
    :type key: string
    :param manual_files: Argument for manual file entry. If non-empty, will 
        override argument GUI to FALSE and bypass file selection. Files should 
        be inputted as a list of strings.
    :type manual_files: list
    :param default_dir: Default directory for file/directory path search tree.
        Only used if GUI set to TRUE for interactive file selection.
    :type default_dir: string
    """
    MatchedFiles, renamed_constants = Handler.grab_files(GUI,load_archive,archive_only,data_ids,\
                                                         data_types,data_constants,overwrite_id,\
                                                         key,manual_files,default_dir)
    Analysis = Classes.AnalysisContainer(MatchedFiles,data_ids,data_types,\
                                         renamed_constants,similar_group_ids,\
                                         similar_groups,group_order)
    return Analysis

Analysis=AnalysisBehavior(data_ids=['actualtiming','anymaze','params','genotype','virus','special'],\
                          data_types=['session','anymaze','parameters','genotype','virus','special'],\
                          default_dir=r'J:\Jacob Dahan\MouseRunner\retired')
    
# Analysis.filter_mice(which='Freezing',by='baseline_freezing',criteria=['0.2'])
# Analysis.filter_mice(which='Freezing',by='mouse_id',criteria=['034399','034411','034394'])
# Analysis.filter_trials(which='Freezing',by='trialized_freezing',criteria=0.8)
# Analysis.normalize(which='Freezing',by='pre',scale=False,scale_by=0,scale_to=1)
Analysis.normalize(which='Freezing',by=None,scale=True,scale_by=0,scale_to=1)
# Analysis.normalize(which='Freezing',by='baseline',scale=False,scale_by=0,scale_to=1)
# Analysis.normalize(which='Freezing',by=None,scale=False)
# Analysis.plotify(ignore_traits={'':''},normalized=False)
plotter_norm=Classes.Plotter(Analysis,normalized=True,ignore_traits={})
plotter=Classes.Plotter(Analysis,normalized=False,ignore_traits={})

# -*- coding: utf-8 -*-

import GUIOperator
import HelperFunctions as Helper

def grab_files(GUI,load_archive,archive_only,data_ids,data_types,data_constants,overwrite_id,key,manual_files,default_dir):
    if GUI and not manual_files:
        FilePaths    = GUIOperator.run_gui(default_dir)
        Files        = Helper.file_load(FilePaths,load_archive,archive_only,data_ids,data_types)
        MatchedFiles = Helper.file_sort(Files,data_constants,overwrite_id,key)
    else:
        Files        = Helper.file_load(manual_files,load_archive,archive_only,data_ids,data_types)
        MatchedFiles = Helper.file_sort(Files,data_constants,overwrite_id,key)
    return MatchedFiles

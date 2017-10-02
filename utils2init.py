#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
  Purpose:  helper functions for input/output handling
  Author:   Andrey Korzh <ao.korzh@gmail.com>
  Created:  2016 - 2017
"""
from __future__ import print_function
#from future.standard_library import install_aliases
#install_aliases()
import sys
from os import path as os_path, listdir as os_listdir, mkdir as os_mkdir
from os import access as os_access, R_OK as os_R_OK, W_OK as os_W_OK
from fnmatch import fnmatch
from datetime import timedelta, datetime
from codecs import open
import configparser
import re


class Ex_nothing_done(Exception):
   def __init__(self, msg= ''):
       self.message= msg + ' => nothing done. For help use "-h" option'
       #self.args= (0, msg)
       #self.errmsg= msg+" - nothing done"

class Error_in_config_parameter(Exception):
    pass

readable  = lambda f: os_access(f, os_R_OK)
writeable = lambda f: os_access(f, os_W_OK)

def dir_walker(root, fileMask='*', bGoodFile=lambda fname,mask: fnmatch(fname, mask),
                                   bGoodDir= lambda fname: True):
    """

    :param root: upper dir to start search files
    :param fileMask: mask for files to find
    :param bGoodFile: filter for files
    :param bGoodDir:  filter for dirs. If set False will search only in root dir
    :return: list of full names of files found
    """
    if root.startswith('.'):
        root = os_path.abspath(root)
    root = os_path.expanduser(os_path.expandvars(root))
    if readable(root):
        if not os_path.isdir(root):
            yield root
            return
        for fname in os_listdir(root):
            pth = os_path.join(root, fname)
            if os_path.isdir(pth):
                if bGoodDir(fname):
                    for entry in dir_walker(pth, fileMask, bGoodFile, bGoodDir):
                        yield entry
            elif readable(pth) and bGoodFile(fname, fileMask):
                yield pth


#Used in next two functions
bGood_NameEdge  = lambda name, namesBadAtEdge: \
    all([name[-len(notUse):] != notUse and name[:len(notUse)] != notUse \
         for notUse in namesBadAtEdge])

def bGood_dir(dirName, namesBadAtEdge):
    if bGood_NameEdge(dirName, namesBadAtEdge):
        return True
    return False

def bGood_file(fname, mask, namesBadAtEdge, bPrintGood = True):
    #any([fname[i] == strProbe for i in range(min(len(fname), len(strProbe) + 1))])
    #in fnmatch.filter(os_listdir(root)
    if fnmatch(fname, mask) and bGood_NameEdge(fname, namesBadAtEdge):
        if bPrintGood: print(fname, end=' ')
        return True
    return False


def dir_create_if_need(str_dir):
    if not os_path.isdir(str_dir):
        print('making output dir...')
        os_mkdir(str_dir)


#def path2rootAndMask(pathF):
    #if pathF[-1] == '\\':
        #root, fname = os_path.split(pathF)
        #fname= '*'
    #else:
        #root, fname = os_path.split(pathF)

    #return(root, fname)
    #fileInF_All, strProbe):
    #for fileInF in fileInF_All:
        #DataDirName, fname = os_path.split(fileInF)
        #if all([DataDirName[-len(noDir):] != noDir for noDir in (r'\bad', r'\test')]) and \
           #any([fname[i] == strProbe for i in range(min(len(fname), len(strProbe) + 1))]) \
           #and fname[-4:] == '.txt' and fname[:4] != 'coef':
            ##fileInF = os_path.join(root, fname)
            #print(fname, end=' ')
            #yield (DataDirName, fname)

def get1stString(manyRows):
    #Get only first path from manyRows
    iSt= min(manyRows.find(r':', 3)-1, manyRows.find(r'\\', 3))+2
    iEn= min(manyRows.find(r':', iSt)-1, manyRows.find(r'\\', iSt))
    return manyRows[iSt-2:iEn].rstrip('\\\n\r ')

def set_field_if_no(dictlike, dictfield, value= None):
    """
    Modifies dict: sets field to value only if it notexist
    :param dictlike: dict
    :param dictfield: field
    :param value: value
    :return: nothing
    """
    if not dictfield in dictlike or dictlike[dictfield] is None:
        dictlike[dictfield] = value

def getDirBaseOut(fileMaskIn, source_dir_words= None, replaceDir= None):
    """
    Finds 'Cruise' and 'Device' dirs. Also returns full path to 'Cruise'.
    If 'keyDir' in fileMaskIn then treat next subsequence as:
    ...\\'keyDir'\\'Sea'\\'Cruise'\\'Device'\\... i.e. finds subdirs after 'keyDir'
    Else use subsequence from end of fileMaskIn:
    ...\\'Sea'\\'Cruise'
    :param fileMaskIn: path to analyse
    :param source_dir_words: 'keyDir' or list of variants in priority order
    :param replaceDir: "dir" - used to create out_path by modifying "Cruise" dir
        - used instead "Device" dir if "keyDir" not in fileMaskIn
    :return: returns tuple, which contains:
    #1. out_path: full path to "Cruise" (see #2.)
        - if "replaceDir" is not None: with "keyDir" is replaced by "replaceDir"
        i.e. modify dir before "Sea"
    #2. "Cruise" dir: subdir of subdir of keyDir
        - if "keyDir" dir not found: parent dir of "Device" dir
        - if "Cruise" dir not found: parent of last subdir in fileMaskIn
    #3. "Device" dir: subdir of subdir of subdir of "keyDir"
        - if "keyDir" dir not found: "replaceDir" (or "" if "replaceDir" is None)
        - if "Cruise" dir not found: last subdir
    """
    if isinstance(source_dir_words, list):
        for source_dir_word in source_dir_words:
            # Start of source_dir_word in 1st detected variant
            st= fileMaskIn.find(source_dir_word, 3) # .lower()
            if st>=0: break
    else:
        source_dir_word= source_dir_words
        st= fileMaskIn.find(source_dir_word, 3)
    if st<0:
        print("Directory structure should be ..."
        "*{}\\'Sea'\\'Cruise'\\'Device'\\!".format(source_dir_word))
        out_path, cruise = os_path.split(fileMaskIn)
        return(out_path, cruise, "" if replaceDir is None else replaceDir)

    else:
        stSea= fileMaskIn[st:].find(u'\\')+st+1            #start of next Dir      (Sea)
        stCruise= fileMaskIn[stSea:].find(u'\\')+stSea+1   #start of next next Dir (Cruise)
        if stCruise==stSea: #no Cruise
            #use last dirs for "\\'Sea'\\'Cruise'\\'Device'\\'{}'"
            enDevice = fileMaskIn[:st].rfind('\\')         #end   of prev Dir (Device)
            enCruise = fileMaskIn[:enDevice].rfind('\\')   #start of prev Dir (Cruise)
            stCruise = fileMaskIn[:enCruise].rfind('\\')+1 #start of prev prev Dir (Cruise)
            out_path = os_path.join(fileMaskIn[:enCruise], replaceDir) if \
                replaceDir else fileMaskIn[:enCruise]
        else:

            enCruise = fileMaskIn[stCruise:].find('\\')+stCruise    #  end of next next Dir (Device)
            enDevice = fileMaskIn[(enCruise+1):].find('\\')+enCruise+1
            if replaceDir == None:
                out_path = fileMaskIn[:enCruise]
            else:
                out_path = fileMaskIn[:(1+fileMaskIn[:st].rfind('\\'))] + \
                                   os_path.join(replaceDir, fileMaskIn[stSea:enCruise])
    return out_path, fileMaskIn[stCruise:enCruise], fileMaskIn[(enCruise+1):enDevice]

def getBase(fileMaskIn, keyDir= 'source'):
# returns first dir after 'keyDir'
    saveDir, baseName= fileMaskIn.split(keyDir,1)
    baseName= baseName.split('\\',1)[0]
    return baseName

def ini2dict(source= None):
    """
    Loads configuration dict from *.ini file with type conversion based on keys names.
    Removes suffics type indicators but keep prefiх.
    prefiх/suffics type indicators (following/precieded with "_"):
        b
        time
        re
        dt (prefix only) with suffixes: ... , minutes, hours, ... - to timedelta
        list, (names - not recommended)
        int, integer, index
        float - to float
    :param source: path of *.ini file. if None - use name of program called with
        ini extension.
    :return: dict - configuration parsed

    Uses only ".ini" extension nevertheless which was cpecified or was specified at all
    """
    config = configparser.RawConfigParser(inline_comment_prefixes=(';',))  # allow_no_value = True
    if source is None or isinstance(source, str):
        # Load data from config file
        # Set default name of config file if it is not specified.
        if source is None:
            source = os_path.splitext(sys.argv[0]) # inspect.getfile()
        else:
            source = os_path.splitext(source)[0]
            if not '\\' in source:
                source= os_path.join(os_path.dirname(sys.argv[0]), source)
        fileNE= source + '.ini'
        with open(fileNE, 'r', encoding= 'cp1251') as f:
            config.read(fileNE)
    elif isinstance(source, dict):
        config.read_dict(source)
        source= '<dict>'

    cfg= dict.fromkeys(config.sections(), {}) #[dict(config.items(sect)) for sect in config.sections()]

    # convert cpecific fields data types
    try:
        for sect in config.sections():
            if sect[:7]=='TimeAdd':
                d= {opt: config.getfloat(sect, opt) for opt in config.options(sect)}
                cfg[sect]= timedelta(**d)
            else:
                optc = None
                for opt in config.options(sect):
                    key_splitted = opt.split('_')
                    key_splitted_len= len(key_splitted)
                    if key_splitted_len<=1:
                        continue
                    #prefix_suffix = key_splitted[0::key_splitted_len-1]
                    prefix= key_splitted[ 0]
                    suffix= key_splitted[-1]

                    if prefix == 'b':
                        config.set(sect, opt, config.getboolean(sect, opt))
                    elif prefix == 'time':
                        config.set(sect, opt, datetime.strptime(config.get(sect, opt),
                                                               '%Y %m %d %H %M %S'))
                    elif prefix == 're':
                        config.set(sect, opt, re.compile(config.get(sect,opt)))
                    elif prefix == 'dt':
                        optc= '_'.join(key_splitted[:-1])
                        if not optc in config.options(sect):
                            config.set(sect, optc, timedelta(**{suffix: config.getfloat(sect, opt)}))
                        else: #convert units and add to accumulated value
                            config.set(sect, optc, config.get(sect,opt) + timedelta(
                                **{suffix: config.getfloat(sect, opt)}))
                        config.remove_option(sect, opt)
                    elif suffix in {'list', 'names'}: #, '_ends_with_list' -> '_ends_with'
                        # parse list
                        suffix = key_splitted[-2] # check if type of list values is specified
                        if suffix in {'int', 'integer', 'index'}:
                            optc = '_'.join(key_splitted[0:-2])
                            config.set(sect, optc, [int(n) for n in config.get(sect, opt).split(',')])
                        else:
                            optc = '_'.join(key_splitted[0:-1])
                            if config.get(sect,opt)[0]=="'": # "'," in
                                config.set(sect, optc, [n.strip(" ',") for n in config.get(
                                    sect,opt).split("',")])
                            else:
                                config.set(sect, optc, [n.strip() for n in config.get(
                                    sect,opt).split(',')])
                    elif 'date' in {suffix, prefix}:
                        if suffix != 'date':
                            opt_new= opt  # use other temp. var instead optc to keep name (see last "if" below)
                        else:
                            opt_new = '_'.join(key_splitted[0:-1]) # del suffix
                            optc = opt_new                         # will del old name (see last "if" below)
                        try:
                            config.set(sect, opt_new, datetime.strptime(config.get(sect, opt), '%d.%m.%Y'))   # %H %M %S
                        except:
                            config.set(sect, opt_new, datetime.strptime(config.get(sect, opt), '%d.%m.%Y %H:%M:%S'))
                        if suffix != 'date':
                            optc = None
                    elif suffix in {'int', 'integer', 'index'}:
                        optc= '_'.join(key_splitted[0:-1])
                        config.set(sect, optc, config.getint(sect, opt))
                    elif suffix == 'float': #, 'percent'
                        optc = '_'.join(key_splitted[0:-1])
                        config.set(sect, optc, config.getfloat(sect, opt))
                    elif suffix=='chars':
                        optc= '_'.join(key_splitted[0:-1])
                        config.set(sect, optc, config.get(sect, opt).replace('\\t','\t'))
                    elif prefix in {'fixed' , 'float', 'max' , 'min'}:
                        # this section is at end because includes frequently used 'max'&'min' which not
                        # nesesary for floats, so set to float only if have no other special format words
                        config.set(sect, opt, config.getfloat(sect, opt))

                    if optc: # optc is replasement of opt
                        config.remove_option(sect, opt)
                        optc= None
                cfg[sect]= dict(config.items(sect)) # for sect in config.sections()]
    except Exception as e: #ValueError, TypeError
        raise Error_in_config_parameter(
            '[{}].{} = {}: {}'.format(sect, opt, config.get(sect, opt), e.args[0]))
    set_field_if_no(cfg, 'input_files', {})
    cfg['input_files']['cfgFile'] = source

    #replace re strings to compiled re objects
    if 're mask' in cfg:
        for strKey, v in cfg['re mask'].items():
            cfg['re mask'][strKey]= re.compile(v)

    return cfg

def pathAndMask(path, filemask= None, ext= None):
    # Find Path & Mask
    # File mask can be specified in "path" (for examample full path) it has higher priority than
    # "filemask" which can include ext part which has higher priority than specified by "ext"
    # But if turget file(s) has empty name or ext than they need to be specified explisetly by ext = .(?)
    path, fileN_fromCfgPath= os_path.split(path)
    if fileN_fromCfgPath:
        if '.' in fileN_fromCfgPath:
            fileN_fromCfgPath, cfg_path_ext= os_path.splitext(fileN_fromCfgPath)
            if cfg_path_ext:
                cfg_path_ext= cfg_path_ext[1:]
            else:
                cfg_path_ext= fileN_fromCfgPath[1:]
                fileN_fromCfgPath= ''
        else: # wrong split => undo
            cfg_path_ext= ''
            path = os_path.join(path, fileN_fromCfgPath)
            fileN_fromCfgPath= ''
    else:
        cfg_path_ext= ''

    if not filemask is None:
        fileN_fromCfgFilemask, cfg_filemask_ext= os_path.splitext(filemask)
        if '.' in cfg_filemask_ext:
            if not cfg_path_ext:
                # possible use ext. from ['filemask']
                if not cfg_filemask_ext:
                    cfg_path_ext= fileN_fromCfgFilemask[1:]
                elif cfg_filemask_ext:
                    cfg_path_ext= cfg_filemask_ext[1:]

        if not fileN_fromCfgPath:
            # use name from ['filemask']
            fileN_fromCfgPath= fileN_fromCfgFilemask
    elif not fileN_fromCfgPath:
        fileN_fromCfgPath = '*'

    if not cfg_path_ext:
        #check ['ext'] exists
        if ext is None:
            cfg_path_ext= '*'
        else:
            cfg_path_ext= ext

    filemask= fileN_fromCfgPath + '.' + cfg_path_ext
    return path,filemask

#----------------------------------------------------------------------
def generator_good_between(i_start= None, i_end= None):
    k = 0
    if i_start is not None:
        while k < i_start:
            yield False
            k += 1
    if i_end is not None:
        while k < i_end:
            yield True
            k += 1
        while True:
            yield False
    while True:
        yield True

def init_file_names(cfg_files, b_interact= True):
    """
      Fill cfg_files filds of file names: {'path', 'filemask', 'ext'}
    which are not specified.
      Searches for files with this mask. Prints number of files found.
      If any - asks user to proceed and if yes returns its names list.
      Else raises Ex_nothing_done exception.

    :param cfg_files: dict with fields:
        'path', 'filemask', 'ext' - name of file with mask or it's part
        exclude_files_ends_with - additional filter for ends in file's names
        b_search_in_subdirs, exclude_dirs_ends_with - to search in dirs recursively
        start_file, end_file - exclude files before and after this values in search list result
    :param b_interact: do ask user to proceed? If false proseed silently
    :return: (namesFull, cfg_files)
        cfg_files: configuration with added (if was not) fields
    'path':,
    'filemask':,
    'nfiles': number of files found,
    'namesFull': list of full names of found files
    """
    set_field_if_no(cfg_files, 'b_search_in_subdirs', False)
    set_cfg_path_filemask(cfg_files)

    # Filter unused directories and files
    filt_dirCur = lambda f: bGood_dir(f, namesBadAtEdge= cfg_files[
        'exclude_dirs_ends_with']) if ('exclude_dirs_ends_with' in cfg_files) else \
        lambda f: bGood_dir(f, namesBadAtEdge= (r'bad', r'test')) #, r'\w'


    def skip_to_start_file(fun):
        if ('start_file' in cfg_files) or ('end_file' in cfg_files):
            fun_skip = generator_good_between(
                cfg_files['start_file'] if 'start_file' in cfg_files else None,
                cfg_files['end_file'] if 'end_file' in cfg_files else None)
            def call_skip(*args, **kwargs):
                return (fun(*args, **kwargs) and fun_skip.__next__())
            return call_skip
        return fun

    def skip_files_ends_with(fun):
        if 'exclude_files_ends_with' in cfg_files:
            def call_skip(*args, **kwargs):
                return fun(*args, namesBadAtEdge= cfg_files['exclude_files_ends_with'])
        else:
            def call_skip(*args, **kwargs):
                return fun(*args, namesBadAtEdge= (r'coef.txt',))
        return call_skip

    bPrintGood= True
    def print_file_name(fun):
        if bPrintGood:
            def call_print(*args, **kwargs):
                if fun(*args, **kwargs):
                    print(args[0], end=' ')
                    return True
                else:
                    return False
            return call_print
        return fun

    @print_file_name
    @skip_files_ends_with
    @skip_to_start_file
    def filt_file_cur(fname, mask, namesBadAtEdge):
        # if fnmatch(fname, mask) and bGood_NameEdge(fname, namesBadAtEdge):
        #     return True
        # return False
        return bGood_file(fname, mask, namesBadAtEdge, bPrintGood= False)

    print('Search {} files'.format(os_path.join(os_path.abspath(
        cfg_files['dir']), cfg_files['filemask'])), end='')
    if cfg_files['b_search_in_subdirs']:
        print(', including subdirs:', end= ' ')
        cfg_files['namesFull'] = [f for f in dir_walker(
            cfg_files['dir'], cfg_files['filemask'],
            bGoodFile=filt_file_cur, bGoodDir= filt_dirCur)]
    else:
        print(':', end=' ')
        cfg_files['namesFull'] = [os_path.join(cfg_files['dir'], f) for f in os_listdir(
            cfg_files['dir']) if filt_file_cur(f, cfg_files['filemask'])]
    cfg_files['nfiles'] = len(cfg_files['namesFull'])
    if cfg_files['nfiles']==0:
        print('\n0 found', end='')
        raise Ex_nothing_done
    elif b_interact:
        s= input('\n' + str(cfg_files['nfiles'])+ r' found. Process them? Y/n: ')
        if 'n' in s or 'N' in s:
            print('answered No')
            raise Ex_nothing_done
        else:
            print('wait... ', end= '')


    """
    def get_vsz_full(inFE, vsz_path):
        # inFE = os_path.basename(in_full)
        inF = os_path.splitext(inFE)[0]
        vszFE = inF + '.vsz'
        return os_path.join(vsz_path, vszFE)

    def filter_existed(inFE, mask, namesBadAtEdge, bPrintGood, cfg_out):
        if cfg_out['fun_skip'].next(): return False

        # any([inFE[i] == strProbe for i in range(min(len(inFE), len(strProbe) + 1))])
        # in fnmatch.filter(os_listdir(root)
        if not cfg_out['b_update_existed']:
            # vsz file must not exist
            vsz_full = get_vsz_full(inFE, cfg_out['path'])
            if os_path.isfile(vsz_full):
                return False
        elif cfg_out['b_images_only']:
            # vsz file must exist
            vsz_full = get_vsz_full(inFE, cfg_out['path'])
            if not os_path.isfile(vsz_full):
                return False
        else:
            return bGood_file(inFE, mask, namesBadAtEdge, bPrintGood=True)


    """



    return cfg_files


# File management ##############################################################
def name_output_file(fileDir, filenameB, filenameE = None, bInteract= True, fileSizeOvr = 0):
    """
    Helps to decide what to do if output file exist.
    :param fileDir:   file directoty
    :param filenameB: file base name
    :param filenameE: file extention. if None suppose filenameB is contans it
    :param bInteract: to ask user?
    :param fileSizeOvr: (bytes) bad files have this or smaller size. So will be overwrite
    :return: (filePFE, sChange, msgFile):
    filePFE - suggested output name. May be the same if bInteract=True, and user
    answer "no" (i.e. to update existed), or size of existed file <= fileSizeOvr
    sChange - user input if bInteract else ''
    msgFile - string about resulting output name
    """

    #filename_new= re_sub("[^\s\w\-\+#&,;\.\(\)']+", "_", filenameB)+filenameE

    # Rename while target exists and it hase data (otherwise no criminal to overwrite)
    msgFile= ''
    m= 0
    sChange= ''
    str_add= ''
    if filenameE is None:
        filenameB, filenameE= os_path.splitext(filenameB)

    def append_to_filename(str_add):
        """
        Returns filenameB + str_add + filenameE if no file with such name in fileDir
        or its size < fileSizeOvr else returns None
        :param str_add: string to add to file name before extension
        :return: base file name or None
        """
        filename_new= filenameB + str_add + filenameE
        full_filename_new= os_path.join(fileDir, filename_new)
        if not os_path.isfile(full_filename_new):
            return filename_new
        try:
            if os_path.getsize(full_filename_new)<=fileSizeOvr:
                msgFile= 'small target file (with no records?) will be overwrited:'
                if bInteract:
                    print('If answer "no" then ' + msgFile)
                return filename_new
        except Exception: #WindowsError
            pass
        return None

    while True:
        filename_new = append_to_filename(str_add)
        if filename_new:
            break
        m += 1
        str_add = '_(' + str(m) + ')'

    if (m>0) and bInteract:
        sChange= input('File "{old}" exists! Change target name to '\
                       '"{new}" (Y) or update existed (n)?'.format(
                       old= filenameB + filenameE, new=filename_new))

    if bInteract and sChange in ['n','N']:
        # update only if answer No
        msgFile= 'update existed'
        filePFE= os_path.join(fileDir, filenameB + filenameE) # new / overwrite
        writeMode= 'a'
    else:
        # change name if need in auto mode or other answer
        filePFE= os_path.join(fileDir, filename_new)
        if m>0:
            msgFile+= (str_add + ' added to name.')
        writeMode= 'w'
    dir_create_if_need(fileDir)
    return(filePFE, writeMode, msgFile)

def set_cfg_path_filemask(cfg_files):
    """
    Sets 'dir' and 'filemask' of cfg_files based on its
    'path','filemask','ext' fieds ('path' or 'filemask' is required)
    :param cfg_files: dict with field 'path' or/and 'filemask' and may be 'ext'
    :return: None
    """
    cfg_files['dir'], cfg_files['filemask'] = pathAndMask(*[
        cfg_files[spec] if spec in cfg_files else None for
        spec in ['path','filemask','ext']])


def splitPath(path, default_filemask):
    """
    Split path to (D, mask, Dlast). Enshure that mask is not empty by using default_filemask.
    :param path: file or dir path
    :param default_filemask: used for mask if path is directory
    :return: (D, mask, Dlast). If path is file then D and mask adjasent parts of path, else
    mask= default_filemask
        mask: never has slash and is never empty
        D: everything leading up to mask
        Dlast: last dir name in D
    """
    D = os_path.abspath(path)
    if os_path.isdir(D):
        mask = default_filemask
        Dlast = os_path.basename(D)
    else:
        D, mask = os_path.split(D)
        if not os_path.splitext(mask)[1]:  # no ext => path is dir, no mask provided
            Dlast = mask
            D = os_path.join(D, Dlast)
            mask = default_filemask
        else:
            Dlast = os_path.basename(D)
    return D, mask, Dlast

def prep(args, default_input_filemask= '*.pdf',
        msgFound_n_ext_dir='Process {n} {ext}{files} from {dir}'):
    """
    Depreciated!!!

    :param args: dict {path, out_path}
        *path: input dir or file path
        *out_path: output dir. Can contain
    <dir_in>: will be replased with last dir name in args['path']
    <filename>: not changed, but used to plit 'out_path' such that it is not last in outD
    but part of outF
    :param default_input_filemask:
    :param msgFound_n_ext_dir:
    :return: tuple (inD, namesFE, nFiles, outD, outF, outE, bWrite2dir, msgFile):
    inD             - input directory
    namesFE, nFiles - list of input files found and its size
    outD            - output directory
    outF, outE      - output base file name and its extension ()
    bWrite2dir      - "output is dir" True if no extension specified.
    In this case outE='csv', outF='<filename>'
    msgFile         - string about numaber of input files found
    """

        # Input files


    inD, inMask, inDlast = splitPath(args['path'], default_input_filemask)
    try:
        namesFE = [f for f in os_path.os.listdir(inD) if fnmatch(f, inMask)]
    except WindowsError as e:
        raise Ex_nothing_done(e.message + ' No {} files in "{}"?'.format(inMask, inD))
    nFiles = len(namesFE)

    if nFiles > 1:
        msgFile = msgFound_n_ext_dir.format(n=nFiles, dir=inD, ext=inMask, files=' files')
    else:
        msgFile = msgFound_n_ext_dir.format(n='', dir=inD, ext=inMask, files='')

    if nFiles == 0:
        raise Ex_nothing_done
    else:
        # Output dir
        outD, outMask, Dlast = splitPath(args['out_path'], '*.%no%')
        # can not replace just in args['out_path'] if inDlast has dots
        Dlast = Dlast.replace('<dir_in>', inDlast)
        outD = outD.replace('<dir_in>', inDlast)

        if '<filename>' in Dlast:  # ?
            outD = os_path.dirname(outD)
            outMask = outMask.replace('*', Dlast)

        outF, outE = os_path.splitext(outMask)
        bWrite2dir = outE.endswith('.%no%')
        if bWrite2dir:  # output path is dir
            outE = '.csv'
            if not '<filename>' in outF:
                outF = outF.replace('*', '<filename>')
    if not os_path.isdir(outD):
        os_path.os.mkdir(outD)
    return inD, namesFE, nFiles, outD, outF, outE, bWrite2dir, msgFile


def this_prog_basename():
    return os_path.splitext(os_path.split(sys.argv[0])[1])[0]


def init_logging(logging, logD, logN= None, levelFile= 'INFO', levelConsole= 'WARNING'):
    """
    Logging to file logD/logN.log and console with piorities levelFile and levelConsole
    :param logging: logging library
    :param logD: directory to save log
    :param logN: default: & + "this program file name"
    :param levelFile: 'INFO'
    :param levelConsole: 'WARN'
    :return: logging Logger
   
    Call example:
    l= init_logging(logging, outD, None, args.verbose)
    l.warning(msgFile)
    """
    if logN is None:
       logN= '&' + this_prog_basename() + '.log'
    logging.basicConfig(filename=os_path.join(logD, logN), format=\
                       '%(asctime)s %(message)s', level= levelFile)
    # set up logging to console - warnings only
    console= logging.StreamHandler()
    console.setLevel(levelConsole) #logging.WARN
    # set a format which is simpler for console use
    formatter= logging.Formatter('%(message)s') #%(name)-12s: %(levelname)-8s ...
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    l = logging.getLogger(__name__)
    return l

def cfg_from_args(p):
    """
    Convert configargparse object to configuration dict of dicts
    :param p:    configargparse object of parameters
    :return cfg: dict with parameters

    - argument_groups (sections) is top level dict
    - '<prog>' strings in p replaces with p.prog
    """
    try:
        args = vars(p.parse_args())
        #args['verbose'] = args['verbose'][0]
        # groupsection by
        cfg_strings = {}
        # cfg= {section: {} for section in ['input_files', 'output_files', 'program']}
        for gr in p._action_groups:
            # skip argparse argument groups
            if gr.title.split(' ')[-1] == 'arguments':
                continue
            cfg_strings[gr.title] = {key: args[key].replace('<prog>', p.prog) if \
                isinstance(args[key], str) else args[key] for key in \
                args.keys() & [a.dest for a in gr._group_actions]}

        cfg = ini2dict(cfg_strings)
    except Exception as e: #IOError
        print('Configuration ({}) error:'.format(p._default_config_files), end=' ')
        print('\n==> '.join([s for s in e.args if isinstance(s, str)]))  # e.message
        raise (e)
    except SystemExit as e:
        cfg = None
    return(cfg)


def name_output_and_log(cfg, logging, f_rep_filemask= lambda f: f, bInteract= False):
    """
    Initialize cfg['output_files']['path'] and splits it to fields
    'path', 'filemask', 'ext'
    Initialize logging and prints message of beginning to write

    :param cfg: dict of dicts, requires fields:
        'input_files' with fields
            'namesFull'
        'output_files' with fields
            'out_path'

    :param logging:
    :param bInteract: see name_output_file()
    :param f_rep_filemask: function f(cfg['output_files']['path']) modifying its argument
        To replase in 'filemask' string '<File_in>' with base of cfg['input_files']['namesFull'][0] use
    lambda fmask fmask.replace(
            '<File_in>', os_path.splitext(os_path.basename(cfg['input_files']['namesFull'][0])[0] + '+')
    :return: cfg, l
    cfg with added fields:
        in 'output_files':
            'path'

            'ext' - splits 'out_path' or 'csv' if not found in 'out_path'
    """
    cfg['output_files']['path'], cfg['output_files']['ext'] = os_path.splitext(
        cfg['output_files']['out_path'])  # set_cfg_path_filemask requires 'path'
    if not cfg['output_files']['ext']:    # set_cfg_path_filemask requires some ext in path or in 'ext'
        cfg['output_files']['ext']= '.csv'
    cfg['output_files']['path'] = f_rep_filemask(cfg['output_files']['out_path'])
    set_cfg_path_filemask(cfg['output_files'])

    # Check target exists
    cfg['output_files']['path'], cfg['output_files']['writeMode'], \
    msg_name_output_file = name_output_file(
        cfg['output_files']['dir'], cfg['output_files']['filemask'], None,
        bInteract, cfg['output_files']['min_size_to_overwrite'])

    str_print = '{msg_name} Saving all to {out}:'.format(
        msg_name=msg_name_output_file, out=os_path.abspath(cfg['output_files']['path']))
    print(str_print)

    l = init_logging(logging, cfg['output_files']['dir'], cfg['program']['log'], cfg['program']['verbose'])
    l.info(str_print)

    return cfg, l
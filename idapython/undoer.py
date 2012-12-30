#!/usr/bin/env python
"""
Do you make mistakes? Do you constantly undefine some important structure and
really wish there was a friggen undo function?
Well then, this script is for you!

After loading this script (Alt-F7), three new hotkeys will be mapped.
shift-s: For saving your idb to a timestamped backup.
shift-l: Loads the last saved idb (via last modification time)
shift-r: Replaces the original idb that you opened with the last saved
timestamped idb.

It is recommended you hit Shift-r when you are done with your ida session so
you don't have to bother finding the correct time stamped one. Keep in mind
this will reload the replaced (now master) file.

TODO: Implement clean out old timestamped versions on shift-r or exit.

Author if you like the code: Isaac Dawson:isaac.dawson@gmail.com:@_wirepair
Depends on:
IDA Pro: (duh)
pywin32: http://sourceforge.net/projects/pywin32/files/pywin32
Windows 7: windows 8 seems to fail due to SendKeys oddness :(.
"""
import glob
import time

import idaapi
from idc import GetIdbPath, SaveBase, AddHotkey, LoadFile
from idautils import GetIdbDir


# SendKeys delays
OPEN_DELAY=1
CLOSE_DELAY=1
EXPLORER_DELAY=1

################################################################################   
############################## Hotkey functions ################################
################################################################################
def save_file():
    ret = 0
    idb_file = GetIdbPath()
    print "IDB Path: %s"%idb_file
    prefix, suffix = get_file_parts(idb_file)
    if prefix == None:
        return 0
    new_file = "%s==%s==%s"%(prefix, time.strftime("%Y.%m.%d.%H%M%S"), suffix)
    print "Saving to: %s"%new_file
    ret = SaveBase(new_file)
    return ret

def load_file(last_idb=""):
    
    # some weird import issues if you don't import in function scope
    try:
        import win32com.client
    except ImportError, msg:
        print "Error win32com is required!"
        return -1

    if last_idb == "":
        last_idb = get_last_idb()
    else:
        print "Loading %s"%last_idb

    if (last_idb == ""):
        print "Error no idb files in our current directory!"
        return -1
    print "Loading last file: %s"%last_idb
    sh = win32com.client.Dispatch("WScript.Shell")

    # to make sure fat fingers leave the shift key
    time.sleep(OPEN_DELAY)
    sh.SendKeys("%fo")

    # give IDA Pro sometime to close file
    # i should probably check file size and adjust accordingly, meh.
    time.sleep(CLOSE_DELAY) 
    sh.SendKeys("{ENTER}")

    # give explorer sometime to list the directory.
    time.sleep(EXPLORER_DELAY) 
    sh.SendKeys(last_idb+"{ENTER}")

def replace_file():
    p = s = ret = 0
    
    last_saved_idb = get_last_idb()
    idb_file = GetIdbPath()
    
    prefix, suffix = get_file_parts(idb_file)
    original = "%s%s"%(prefix,suffix)
    backup = original+"_"
    try:
        if os.path.exists(backup):
            os.unlink(backup)
        os.rename(original, backup) # make a backup
    except (OSError, IOError), msg:
        print "Error making backup of our original idb: %s\n%s"%(original, msg)
        return -1
    try:
        os.rename(last_saved_idb, original)
    except (OSError, IOError), msg:
        print "Error writing our last save file:\n%s"%(original, msg)
        return -1
    print "Reloading original file."
    load_file(original)
    
################################################################################   
############################## Helper functions ################################
################################################################################   

def get_last_idb():
    idb_file = GetIdbPath() # get full filename
    print "idb_file %s"%idb_file
    prefix,suffix = get_file_parts(idb_file) # just take the beginning
    if prefix == None:
        print "Error getting idb file path information."
        return ""
    
    # guess i should be proper about this and use last modified time.
    idbs = [idbs for idbs in glob.glob(prefix+"*.idb")]
    idb_stats = []
    for idb in idbs:
        mtime = os.stat(idb).st_mtime
        idb_stats.append((idb, mtime))
    sorted_idb = sorted(idb_stats, key=lambda idb: idb[1])
    return sorted_idb[-1][0]

def get_file_parts(idb_file):
    p = s = 0
    try:
        if (idb_file.find('==') != -1):
            p = idb_file.find('==')
            s = idb_file.rfind('==')+2
        else:
            p = idb_file.rfind('.')
            s = p
        prefix = idb_file[:p]
        suffix = idb_file[s:]
        return (prefix, suffix)
    except Exception, msg:
        print "Error getting file path information: %s"%msg
    return None,None
    
def add_hot_key(key, str_func):
    idaapi.CompileLine('static %s() { RunPythonStatement("%s()"); }'%(str_func, str_func))
    AddHotkey(key, str_func)

if __name__ == '__main__':
    # for saving...
    add_hot_key("Shift-S", "save_file")
    # for loading
    add_hot_key("Shift-L", "load_file")
    # for replacing original idb last timestamped (saved!) file to make it be the master.
    # NOTE THIS RENAMES THE ORIGINAL to <orig>.idb_ and will overwrite if <orig>.idb_ exists!
    # You should run this when you're "done" and not want to deal with the other files.
    add_hot_key("Shift-R", "replace_file")

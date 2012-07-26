#!/usr/bin/env python
from pykd import *
import sys


def dump_module(link):
    
    data_table_entry = typedVar("_LDR_DATA_TABLE_ENTRY", link)
    try:
        dprintln("Module Path: %s"%loadUnicodeString(data_table_entry.FullDllName))
    except:
        dprintln("Module Path: <Unknown>")
    
    dprintln("Module Base: 0x%08x"%(data_table_entry.DllBase))
    dprintln("Module Entry Point: 0x%08x"%(data_table_entry.EntryPoint))
    dprintln("Module Size: 0x%08x"%(data_table_entry.SizeOfImage))
    dprintln("Module Load Count: %d"%(data_table_entry.LoadCount))
    

def main():
    # get the address of PsLoadedModuleList
    pslist = ptrPtr(getOffset("PsLoadedModuleList")) 
    dprintln("PsLoadedModuleList is @ 0x%08x"%pslist)
    
    data_table_entry = typedVar("_LDR_DATA_TABLE_ENTRY", pslist)
    flink = data_table_entry.InLoadOrderLinks.Flink
    first_entry = flink
    # walk forward
    while (flink != 0x0):
        list_entry = typedVar("_LIST_ENTRY", flink)
        dump_module(list_entry)
        flink = list_entry.Flink
        if (first_entry == flink):
            # seen it.
            break

if __name__ == "__main__":
    if isKernelDebugging():
        main()
    else:
        dprintln( "[*] We are not debugging the kernel..." )

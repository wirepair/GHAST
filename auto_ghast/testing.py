#!/usr/bin/env python
import sys
from pykd import *
from breakpoints import BreakpointRecorder, RecordedObject
from driverobject import DriverObject
"""
Author: Isaac Dawson 2012 for My Adventures in Game Hacking
STUPID SHUT UP FACE DON'T CARE LICENSE:
Copyright or left, or whatever the hell you want. If it blows up, probably
my fault, but I don't care and you can't sue me because you stole my junk.
"""

if __name__ == "__main__":
    if isKernelDebugging():
        dprintln( "[*] Single stepping into driver...\n" )	
    
        try:
            setExecutionStatus(DEBUG_STATUS_STEP_INTO)
            waitForEvent()
        except:
            pass
        
        ip = reg("eip")
        dprintln("[*] eip is: %08x"%ip)
        esp = reg("esp")
        esp += 0x04 # this points to our DriverObject
        pnkbstrk = DriverObject()
        pnkbstrk.get_driver_by_address(esp)
        # should be loaded, now try to extract some of the details.
        # start of driver in memory
        base = pnkbstrk.get_base_address()
        end = pnkbstrk.get_end_address()
        entry = pnkbstrk.get_entry()
        dprintln("[*] Base: 0x%08x"%(base))
        dprintln("[*] Driver Entry: 0x%08x"%(entry))
        dprintln("[*] End: 0x%08x"%(end))
        # run through the DriverEntry function
        
        try:
            dbgCommand("gu")
            waitForEvent()
        except:
            pass
        
        # get the dispatch func address
        control_address = pnkbstrk.get_device_control_address()
        dprintln("[*] IRP_MJ_DEVICE_CONTROL: 0x%08x"%control_address)
        #pnkbstrk.print_irp_table()
        ioctl_breakpoint = BreakpointRecorder(control_address, "IOCTL Breakpoint")
        ioctl_breakpoint.record_register("ebp", 0x0c, "IRP IOCTL #: ")
        ioctl_breakpoint.record_register("eax", description="EAX is: ")
        ioctl_breakpoint.set_breakpoint()
        try:
            setExecutionStatus(DEBUG_STATUS_GO)
            waitForEvent()
        except:
            pass

        #driver_object_pointer = ptrPtr(esp+4)
        #driver_object = typedVar("nt!_DRIVER_OBJECT", driver_object_pointer)
        #object_name = loadUnicodeString(driver_object.DriverName)
        #print object_name
        #driver_name = object_name.replace('\\Driver\\','')
        

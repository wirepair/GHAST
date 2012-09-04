#!/usr/bin/env python
import sys
from pykd import *
from breakpoints import BreakpointRecorder, RecordedObject
from driverobject import DriverObject

if __name__ == "__main__":
    # be sure to call this only when you break at:
    # bp nt!IopLoadDriver+0x66a
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
        some_driver = DriverObject()
        some_driver.get_driver_by_address(esp)
        # should be loaded, now try to extract some of the details.
        # start of driver in memory
        base = some_driver.get_base_address()
        end = some_driver.get_end_address()
        entry = some_driver.get_entry()
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
        control_address = some_driver.get_device_control_address()
        dprintln("[*] IRP_MJ_DEVICE_CONTROL: 0x%08x"%control_address)
        #some_driver.print_irp_table()
        ioctl_breakpoint = BreakpointRecorder(control_address,
                                              "IOCTL Breakpoint")
        # a custom callback called during our bp
        def get_ioctl_cb(recorded_object, value):
            val = ptrDWord(reg("ebp")+0x0c) # arg to PIRP Pirp
            irp = typedVar("nt!_IRP", val) # get the IRP struct
            iostack = typedVar('nt!_IO_STACK_LOCATION',
                               irp.Tail.Overlay.CurrentStackLocation)
            iocode = iostack.Parameters.DeviceIoControl.IoControlCode
            dprintln("%s %s"%(recorded_object.description, iocode))
        
        ioctl_breakpoint.record_with_callback(get_ioctl_cb, '[*] IOCTL')
        ioctl_breakpoint.record_register("eax", description="[*] EAX is: {0:08x}")
        ioctl_breakpoint.record_register("esp", description="[*] ESP is: {0:08x}")
        ioctl_breakpoint.record_register("esp", 0x0c,
                                         description="[*] ESP + 0x0c is: {0:08x}")
        
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
        
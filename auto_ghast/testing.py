#!/usr/bin/env python
import sys
from pykd import *
from breakpoints import BreakpointRecorder, RecordedObject
from driverobject import DriverObject

def print_md5context(context):
    print "MD5Context.buf:"
    for dword in loadDWords(context, 4):
        print "0x%08x"%dword,
    print
    print "MD5Context.bits:"
    for dword in loadDWords(context+4*4, 2):
        print "0x%08x"%dword,
    print
    print "MD5Context.in: "
    for byte in loadBytes(context+6*4, 64):
        try:
            print "%c"%byte,
        except:
            print "\\x%x"%byte,
    print

def set_ioctl_breakpoint(some_driver):
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
    return
    
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

        # MD5Update Breakpoint right after func prolog
        md5update_rva = 0x6373 #
        dprintln("[*] Setting breakpoint @ 0x%08x"%(base+md5update_rva))
        md5u_bp = BreakpointRecorder(base+md5update_rva)
        def read_value(recorded_object, value):
            try:
                length = ptrDWord(reg("ebp")+0x10)
                print "length: %r"%length
                buf_addr = ptrDWord(reg("ebp")+0x0c)
                print "addr of buff: %08x"%buf_addr
                #buf = ptrDWord(buf_addr)
                for byte in loadBytes(buf_addr, length):
                    try:
                        print "%c"%byte,
                    except:
                        print "\\x%x"%byte,
                print
                context = ptrDWord(reg("ebp")+8)
                print_md5context(context)                
            except Exception, msg:
                print "error: ",msg
        md5u_bp.record_with_callback(read_value)
        
        md5u_bp.set_breakpoint()

        #MD5Final Breakpoint , right before func epilog
        md5final_rva = 0x74EC #
        dprintln("[*] Setting MD5Final breakpoint @ 0x%08x"%(base+md5final_rva))
        md5f_bp = BreakpointRecorder(base+md5final_rva)
        def read_md5_digest(recorded_object, value):
            try:
                """
                digest = ptrDWord(reg("ebp")+8)
                print "Digest @ %08x: "%digest,
                
                for byte in loadBytes(digest, 16):
                    print "%x"%byte,
                print 
                """
                context = ptrDWord(reg("ebp")+0x08)
                print "MD5Context @ %08x: "%context,
                print_md5context(context)
            except Exception, msg:
                print "Exception: %s"%msg
            #setExecutionStatus(DEBUG_STATUS_STOP)
            
            
        md5f_bp.record_with_callback(read_md5_digest)
        md5f_bp.set_breakpoint()
        
        ketickcnt_rva = 0x2A5A
        dprintln("[*] Setting KeTickCount breakpoint @ 0x%08x"%(base+ketickcnt_rva))
        ketickcnt_bp = BreakpointRecorder(base+ketickcnt_rva)
        ketickcnt_bp.record_register("ecx", "[*] KeTickCount value: {0:08x}")
        ketickcnt_bp.set_breakpoint()
        
        # unknown strlen func
        strlencall_rva = 0x61B3
        dprintln("[*] Setting Unknown strlen caller func breakpoint @ 0x%08x"%(base+strlencall_rva))
        strlencall_bp = BreakpointRecorder(base+strlencall_rva)
        def read_strings(recorded_object, value):
            try:
                string1_addr = ptrDWord(reg("ebp")+0x10)
                string2_addr = ptrDWord(reg("ebp")+0x8)
                print "[*] Game: %08x"%string1_addr
                print loadCStr(string1_addr)
                print "[*] Unknown hash: %08x"%string2_addr
                print loadCStr(string2_addr)
            except Exception, msg:
                print "error: ",msg
        strlencall_bp.record_with_callback(read_strings)
        strlencall_bp.set_breakpoint()
        

        strlen_rva = 0x74FE
        dprintln("[*] Setting strlen breakpoint @ 0x%08x"%(base+strlen_rva))
        strlen_bp = BreakpointRecorder(base+strlen_rva)
        def read_strlen_string(recorded_object, value):
            try:
                string1_addr = ptrDWord(reg("esp")+0x4)
                print "[*] string: %08x"%string1_addr
                print loadCStr(string1_addr)
            except Exception, msg:
                print "Error: ",msg
        strlen_bp.record_with_callback(read_strlen_string)
        strlen_bp.set_breakpoint()

        memcpy_rva = 0x74F8
        dprintln("[*] Setting memcpy breakpoint @ 0x%08x"%(base+memcpy_rva))
        memcpy_bp = BreakpointRecorder(base+memcpy_rva)
        def read_memcpy(recorded_object, value):
            try:
                dest = ptrDWord(reg("esp")+0x4)
                src = ptrDWord(reg("esp")+0x8)
                size = ptrDWord(reg("esp")+0x0c)
                print "[*] src @ %08x of size: %08x to dest: %08x"%(src,size,dest)
                for byte in loadBytes(src, size):
                    try:
                        print "%c"%byte,
                    except:
                        print "\\x%x"%byte,
                print
            except Exception, msg:
                print "Error: ",msg
        memcpy_bp.record_with_callback(read_memcpy)
        memcpy_bp.set_breakpoint()

        try:
            setExecutionStatus(DEBUG_STATUS_GO)
            waitForEvent()
        except:
            pass
#!/usr/bin/env python
from pykd import *
"""
Author: Isaac Dawson 2012 for My Adventures in Game Hacking
STUPID SHUT UP FACE DON'T CARE LICENSE:
Copyright or left, or whatever the hell you want. If it blows up, probably
my fault, but I don't care and you can't sue me because you stole my junk.
"""

class RecordedObject(object):
    def __init__(self, breakpoint_object, recorded_type, object_to_record,
                 modifier=None, description="", callback=None):
        """Our object to record"""
        self.breakpoint_object = breakpoint_object
        self.recorded_type = recorded_type
        self.object_to_record = object_to_record
        self.modifier = modifier
        self.description = description
        self.callback = callback
        
    def has_callback(self):
        return self.callback is not None
        
class BreakpointRecorder(object):
    def __init__(self, address, name=""):
        self.address = address
        self.name = name
        self.bp_id = None
        self.recorder = {}
        self.recorded_objects = []

    def record_register(self, register, modifier=0, description="", callback=None):
        self.recorded_objects.append(RecordedObject(self, "register", register,
                                                    modifier=modifier,
                                                    description=description,
                                                    callback=callback))
    
    def record_address(self, address, description="", callback=None):
        self.recorded_objects.append(RecordedObject(self, "address", address,
                                                    modifier=None,
                                                    description=description,
                                                    callback=callback))
        
    def record_with_callback(self, callback, description=""):
        self.recorded_objects.append(RecordedObject(self, "callback", callback,
                                                    modifier=None,
                                                    description=description,
                                                    callback=callback))

    def set_breakpoint(self):
        
        if self.bp_id is not None:
            dprintln("[*] Removing Callback %d"%self.bp_id)
            removeBp(self.bp_id)

        dprintln("[*] Setting Callback")
        self.bp_id = setBp(self.address, self.callback)            
            

    def callback(self, value):
        dprintln("[*] In breakpoint callback, got value: %s"%value)
        dprintln("[*] Recorded objects len: %d"%len(self.recorded_objects))
        try:
            for recorded_object in self.recorded_objects:
                if recorded_object.recorded_type == "register":
                    dprintln("[*] In-register")
                    register_value = reg(recorded_object.object_to_record)
                    dprintln("[*] Register: %08x"%(register_value))
                    final_value = register_value + recorded_object.modifier
                    dprintln("[*] Final Value: %08x"%(final_value))
                    recorded_object.value = final_value
                    if getattr(recorded_object, "description"):
                        dprintln("[*] %s %s"%(recorded_object.description, recorded_object.value))
                    dprintln("[*] Leaving register")
                    if recorded_object.has_callback():
                        recorded_object.callback(recorded_object, value)
    
                elif recorded_object.recorded_type == "address":
                    final_value = ptrDWord(recorded_object.object_to_record)
                    recorded_object.value = final_value
                    dprintln("[*] %s %s"%(recorded_object.description, recorded_object.value))
    
                    if recorded_object.has_callback():
                        recorded_object.callback(recorded_object, value)
                    
                elif recorded_object.recorded_type == "callback":
                    if recorded_object.has_callback():
                        recorded_object.callback(recorded_object, value)
        except Exception, msg:
            dlprint("[*] Exception handling breakpoint: %s"%(msg))
        # reset our BP
        return DEBUG_STATUS_GO 
        
    

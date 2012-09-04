#!/usr/bin/env python
from pykd import *
import string

DEBUG = False
class RecordedObject(object):
    """A single Recorded Object. Used to hold various information that
    we are interested in when we set our breakpoints."""
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
    """
    A breakpoint recorder object. One instance per breakpoint is created.
    A breakpoint can record many different things. Usually only registers
    or addresses are necessary. However for more complex things you'll
    probably want to create a custom callback. Each type of value to
    be recorded requires various properties. Also you may attach a call
    back to any of the various record_* types if necessary.
    
    The 'description' field must contain a proper format string for
    the value to be properly displayed.
    See: U{http://docs.python.org/library/functions.html#format}

    Examples of descriptions:
    bp.record_register("eax", description='val: {0:08x}')
    bp.record_address(0xf00ff00f,description='val: {0}')
    
    WARNING WARNING WARNING: Exceptions do not seem to be properly (?)
    handled by pykd. If you set a callback and it doesn't seem to work,
    it probably is causing some sort of exception. Print out each
    line to determine what you f'd up.
    """
    def __init__(self, address, name=""):
        self.address = address
        self.name = name
        self.bp_id = None
        self.recorder = {}
        self.recorded_objects = []

    def record_register(self, register, modifier=0, description="", callback=None):
        """Records a single registers value for the breakpoint.
        
        @type register: string
        @param register: The register name: eax, ebp, esi...
        @type modifier: number
        @param modifier: A value to sub/add to the register
        @type description: string
        @param description: A string to print out, along with proper format place holders.
        @type callback: function
        @param callback: A callback to call when we hit this breakpoint."""
        self.recorded_objects.append(RecordedObject(self, "register", register,
                                                    modifier=modifier,
                                                    description=description,
                                                    callback=callback))
    
    def record_address(self, address, description="", callback=None):
        """Records a single value for the breakpoint.
        
        @type address: number
        @param address: The location in memory to record
        @type description: string
        @param description: A string to print out, along with proper format place holders.
        @type callback: function
        @param callback: A callback to call when we hit this breakpoint."""
        self.recorded_objects.append(RecordedObject(self, "address", address,
                                                    modifier=None,
                                                    description=description,
                                                    callback=callback))
        
    def record_with_callback(self, callback, description=""):
        """Calls a user supplied callback when the breakpoint hits. The
        callback *must* take two values. First is a L{RecordedObject}
        the second parameter is the value, which is useless as far as I
        can tell.
        
        @type address: number
        @param address: The location in memory to record
        @type description: string
        @param description: A string to print out, along with proper format place holders.
        @type callback: function
        @param callback: A callback to call when we hit this breakpoint."""
        self.recorded_objects.append(RecordedObject(self, "callback", callback,
                                                    modifier=None,
                                                    description=description,
                                                    callback=callback))

    def set_breakpoint(self):
        """Sets the breakpoint on the address specified during init."""
        if self.bp_id is not None:
            dprintln("[*] Removing Callback %d"%self.bp_id)
            removeBp(self.bp_id)

        dprintln("[*] Setting Callback")
        self.bp_id = setBp(self.address, self.callback)            
            

    def callback(self, value):
        """Called when breakpoint is hit. You do not call this manually, pykd
        will call us."""
        if DEBUG:
            dprintln("[*] In breakpoint callback, got value: %s"%value)
            dprintln("[*] Recorded objects len: %d"%len(self.recorded_objects))

        for recorded_object in self.recorded_objects:
            if recorded_object.recorded_type == "register":
                register_value = reg(recorded_object.object_to_record)
                final_value = register_value + recorded_object.modifier
                recorded_object.value = final_value
                if getattr(recorded_object, "description"):
                    dprintln(recorded_object.description.format(recorded_object.value))
                if recorded_object.has_callback():
                    recorded_object.callback(recorded_object, value)

            elif recorded_object.recorded_type == "address":
                final_value = ptrDWord(recorded_object.object_to_record)
                recorded_object.value = final_value
                dprintln(recorded_object.description.format(recorded_object.value))

                if recorded_object.has_callback():
                    recorded_object.callback(recorded_object, value)
                
            elif recorded_object.recorded_type == "callback":
                if recorded_object.has_callback():
                    recorded_object.callback(recorded_object, value)

        # reset our BP
        return DEBUG_STATUS_GO 
        
    
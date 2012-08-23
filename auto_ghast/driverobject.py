#!/usr/bin/env python
from pykd import *
"""
Author: Isaac Dawson 2012 for My Adventures in Game Hacking
STUPID SHUT UP FACE DON'T CARE LICENSE:
Copyright or left, or whatever the hell you want. If it blows up, probably
my fault, but I don't care and you can't sue me because you stole my junk.
"""

class DriverObject(object):
    def __init__(self):
        self.driver_name = ""
        self.object_name = ""
        self.driver_object_pointer = None
        
    
    def get_driver_by_address(self, address):
        self.module_object = None
        self.driver_object_pointer = ptrPtr(address)
        self.driver_object = typedVar("nt!_DRIVER_OBJECT", self.driver_object_pointer)
        if self.driver_object is not None:
            print loadUnicodeString(self.driver_object.DriverName)
            self.object_name = loadUnicodeString(self.get_name())
            self.driver_name = self.object_name.replace('\\Driver\\','')
            try:
                self.module_object = loadModule(self.driver_name)
            except:
                pass

    def get_driver_by_name(self, driver_name):
        self.driver_name = driver_name
        self.object_name = "\\Driver\\" + driver_name
        self.driver_object_pointer = self.get_object_by_name(self.object_name)
        self.module_object = loadModule(self.driver_name)

    def get_object_by_name(self, object_name):
        if len(object_name)==0: 
            return
        if object_name[0] != '\\':
            return

        root_directory = typedVar("nt!_OBJECT_DIRECTORY",
                                  ptrPtr( nt.ObpRootDirectoryObject))

        return self.get_object_in_directory(root_directory, object_name[1:])

    def get_object_in_directory(self, directory_object, object_name):
        if object_name.find( "\\" ) != -1:
            (directory_sub_name, object_sub_name) =  object_name.split("\\", 1)
        else:
            directory_sub_name = object_name
     
        for i in range( 0, 37 ):
           if directory_object.HashBuckets[i] != 0:
              directory_entry = typedVar("nt!_OBJECT_DIRECTORY_ENTRY",
                                  directory_object.HashBuckets[i])
    
              while directory_entry != 0:
                object_header = containingRecord(directory_entry.Object,
                                                  "nt!_OBJECT_HEADER", "Body")
    
                object_name = self.get_object_name_from_object_header(
                    object_header
                )
                
                if object_name.lower() == directory_sub_name.lower():
                    object_type = self.get_object_type_from_object_header(
                        object_header
                    )
                    
                    
                    if object_type == ptrPtr(nt.ObpDirectoryObjectType):
                        return self.get_object_in_directory(
                            typedVar("nt!_OBJECT_DIRECTORY",
                                     directory_entry.Object),
                            object_sub_name)
                    else:
                        return directory_entry.Object
    
                if directory_entry.ChainLink != 0:
                    directory_entry = typedVar("nt!_OBJECT_DIRECTORY_ENTRY",
                                               directory_entry.ChainLink)
                else:
                    directory_entry = 0
        return

    def get_object_type_from_object_header(self, object_header):
        if hasattr( object_header, "Type"):
            return object_header.Type
        return ptrPtr(nt.ObTypeIndexTable + ptrSize() * object_header.TypeIndex)
 
    def get_object_name_from_object_header(self, object_header ):
        if hasattr( object_header, "NameInfoOffset"):
            object_name = typedVar(
                "nt!_OBJECT_HEADER_NAME_INFO",
                object_header.getAddress() - object_header.NameInfoOffset
            )
        else:
            if (0 == (object_header.InfoMask & 2)):
               return ""
            offsetNameInfo = ptrByte(
                nt.ObpInfoMaskToOffset + (object_header.InfoMask & 3)
            )
            if (0 == offsetNameInfo):
                return ""
    
            object_name = nt.typedVar("_OBJECT_HEADER_NAME_INFO",
                                      object_header.getAddress() - offsetNameInfo)
    
        return loadUnicodeString(object_name.Name.getAddress())

    def get_base_address(self):
        if (self.module_object is not None):
            return self.module_object.begin()
        elif(self.driver_object is not None):
            return self.driver_object.DriverStart
        else:
            dprintln("[*] Unable to get base address, driver object not found")
        return None

    def get_entry(self):
        if (self.driver_object is not None):
            return self.driver_object.DriverInit
        else:
            dprintln("[*] Unable to get Entry, driver object not found")
        return None
     
    def get_name(self):
        if (self.driver_object is not None):
            return self.driver_object.DriverName
        else:
            dprintln("[*] Unable to get the driver's name, driver object not found")
        return None

    def get_end_address(self):
        if (self.module_object is not None):
            return self.module_object.end()
        elif(self.driver_object is not None):
            return self.get_base_address()+self.get_size()
        else:
            dprintln("[*] Unable to get driver end address, driver object not found")
        return None

    def get_size(self):
        if (self.module_object is not None):
            return self.module_object.size()
        elif (self.driver_object is not None):
            return self.driver_object.DriverSize
        else:
            dprintln("[*] Unable to get driver size, driver object not found")
        return None

    def get_image(self):
        if (self.module_object is not None):
            return self.module_object.image()
        else:
            dprintln("[*] Unable to get image name, module object not found")
        return None
    
    # this can change.
    def get_device_control_address(self):
        self.reload_driver()
        if self.driver_object is None:
            dprintln("[*] Unable to get device control address, driver object not found")
            return None
        print "%08x"%self.driver_object.MajorFunction[0x0e] # IRP_MJ_DEVICE_CONTROL
        return self.driver_object.MajorFunction[0x0e]

    # this can change.    
    def print_irp_table(self):
        self.reload_driver()
        if self.driver_object is None:
            dprintln("[*] Driver object not found")
            return None
        for i in xrange(len(self.driver_object.MajorFunction)):
            symbol = None
            try:
                symbol = findSymbol(self.driver_object.MajorFunction[i])
            except Exception, msg:
                pass
            dprintln("MajorFunction[%02x] = 0x%08x <%s>"%(
                i, self.driver_object.MajorFunction[i], symbol)
            )
    
    def reload_driver(self):
        self.driver_object = typedVar("nt!_DRIVER_OBJECT", self.driver_object_pointer)
    
    def record_ioctls(self):
        pass
    
    def record_functions(self, function_recorder):
        pass
    

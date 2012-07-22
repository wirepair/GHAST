from pykd import *
import sys

if __name__ == "__main__":
    if isKernelDebugging():
        dprintln( "check interrupt handlers...\n" )	
        idtr = reg( "idtr" )
        nt = loadModule( "nt" )
        ErrorCount = 0
        dprintln("idtr is: %08x"%idtr)
        for i in xrange(0, 255):
            idtEntry = nt.typedVar("_KIDTENTRY", idtr+i*8)
            if idtEntry.Selector == 8:
                offset = ( idtEntry.ExtendedOffset * 0x10000 ) + idtEntry.Offset
                InterruptHandler = offset
                kinterrupt = nt.typedVar("_KINTERRUPT",InterruptHandler)
                if InterruptHandler != 0x00:
                    try:
                        dprintln("IDT [%02x] InterruptHandler: 0x%08x "\
                                 "DispatchAddress: 0x%08x "\
                                 "KINTERRUPT.DispatchCode 0x%08x"\
                                 " (symbol: %s)"%(i,InterruptHandler,
                                                  kinterrupt.DispatchAddress,
                                                  kinterrupt.DispatchCode,
                                                  findSymbol(InterruptHandler)))
                    except Exception, msg:
                        dprintln("IDT [%02x] empty"%i)
    else:
        dprintln( "we are not debugging the kernel..." )
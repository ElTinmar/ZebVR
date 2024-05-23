import lightcrafter as lcr
import time

"""
adapted from https://github.com/eulerlab/QDSpy/blob/master/Stimuli/__toGB_8bit_patternMode.py
Put the LigthCrafter in pattern mode, take input from HDMI at 120 Hz, and expose red 
for 1/120 s    
"""

# Generate lightcrafter object and try to connect to it
dev = lcr.Lightcrafter(_isCheckOnly=False,_logLevel=3)
res = dev.connect()
if res[0] is not lcr.ERROR.OK:
    # No connection
    RuntimeError("Impossible to connect to Lightcrafter")

# Print report and video signal status
dev.getFirmwareVersion()
dev.getHardwareStatus()
dev.getMainStatus()
dev.getSystemStatus()
dev.getVideoSignalDetectStatus()

# Stop pattern
dev.stopPatternSequence()

# Set video source
dev.setInputSource(lcr.SourceSel.HDMI, lcr.SourcePar.Bit24)

# Select pattern sequence mode
dev.setDisplayMode(lcr.DispMode.Pattern)

# Select the 24bit RGB stream as input
dev.setPatternDisplayDataInputSource(lcr.SourcePat.Parallel)

# Set trigger mode to VSYNC
dev.setPatternTriggerMode(lcr.PatTrigMode.Vsync_fixedExposure)

# Set exposure time, frame rate (in usec)
# In external video input pattern sequence modes, the pattern exposure time must equal the frame period.
dev.setPatternExpTimeFrPer(8333, 8333)

# Setup LUT:
# 1 LUT entries, repeat sequence, 1 patterns/sequence, n/a
dev.setPatternDispLUTControl(1, True, 1, 1)

# Open LUT mailbox for pattern sequence mode (external input)
# The following parameters: display mode, trigger mode, exposure, and frame rate must be set up
# before sending any mailbox data. If the Pattern Display Data Input Source is set to streaming, the
# image indexes are not required to be set. Regardless of the input source, the pattern definition must be
# set.
dev.setPatternDispLUTAccessControl(lcr.MailboxCmd.OpenPat)

# LUT entry #0 ...
dev.setPatternDispLUTOffsetPointer(0)
# Pattern G0-G7, internal trigger, 8 bit, red LED
dev.setPatternDispLUTData(lcr.MailboxPat.G76543210,
                        lcr.MailboxTrig.ExternalPos,
                        8, lcr.MailboxLED.Red,False,True)

# Close LUT mailbox
dev.setPatternDispLUTAccessControl(lcr.MailboxCmd.Close)

# Validate pattern sequence
res = dev.validateDataCommandResponse()

if res[0] == lcr.ERROR.OK: # and res[1]:
    dev.getHardwareStatus()
    dev.getMainStatus()
    time.sleep(1)
    dev.startPatternSequence()
    time.sleep(1)

dev.getMainStatus()
dev.getSystemStatus()

dev.disconnect()

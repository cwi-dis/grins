Testing GRiNS Player under Pocket PC emulator
---------------------------------------------

1. copy python lib for wince under 
	"Windows CE Tools\wce300\MS Pocket PC\emulation\palm300\Program Files\Python"

2. copy bin, common, grins, lib, pylib under
	"Windows CE Tools\wce300\MS Pocket PC\emulation\palm300\Program Files\GRiNS"

3. Open eMbedded Visual C++ workspace "grins extensions.vcw" (from cmif\win32\CE\src)
   
   a) set active project to "python16.vcp" and call "build (F7)"
   Check that the download directory is \Windows (setings/debug_tab)

   b) do the same for winuser.vcp, winkernel.vcp, wingdi.vcp
   Check that the download directory is \Program Files\GRiNS\bin\wince

   c) finally do the same for GRiNS Player
    Check that the download directory is \\Windows\Start Menu (or create a shortcut there)
    The build process has a custom step to create and copy grinsRC.py to \Program Files\GRiNS\bin\wince

Run GRiNS Player from Pocket PC emulator 'Start' menu




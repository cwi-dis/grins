rem Run this by dragging it to the "emulation environment" DOS shell.
rem
rem This is the NT path of the emulation dir
set CEEMU="D:\Windows CE Tools\wce300\MS Pocket PC\emulation\palm300"
rem This is the NT path of the emulation Python
set PYTHON=%CEEMU%"\windows\Start Menu\Python_d.exe"
rem This is the EMULATION path of the grins script
set IGRINS=\cmif\bin\win32\iGRiNSplayer_SMIL2_CE.py
%PYTHON% %IGRINS%

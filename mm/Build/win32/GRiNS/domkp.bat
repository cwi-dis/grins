rem BEGIN_CUSTOMIZATION

set GRINS_HOME=e:\cmif

set FREEZE_WHAT=grins
set EXCLUDE_WHAT=cmifed
set main_script=%GRINS_HOME%\fGRiNS.py

del *.c

set PYTHON_EXE=e:\cmif\bin\python.exe
set PYTHONHOME=e:\python
call E:\Program Files\Microsoft Visual Studio\VC98\Bin\vcvars32.bat

rem END_CUSTOMIZATION



rem The rest of the script assumes that the folder tree  
rem has the same structure as CWI's CVS root 
rem It is the same for both player(GRiNS) and editor (GRiNSed)


set PYTHONEX=%PYTHONHOME%\Extensions
set FREEZE=%GRINS_HOME%\pytools\freeze\freeze.py

rem GENERAL PART
set LIB=%LIB%;%pythonex%\win32\build;%pythonex%\pythonwin\build;%GRINS_HOME%\win32\src\Build
set INCLUDE=%INCLUDE%;%pythonex%\win32\src;%pythonex%\pythonwin
rem Set the following line if win32ui is frozen into the final .exe
rem set CL=%CL%;/D FREEZE_WIN32UI

:freeze

rem Set up the PYTHONPATH for the freeze - this points to all the cmif directories
rem we need to perform the freeze.
set PYTHONPATH=%GRINS_HOME%
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\win32\src\Build
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\pylib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\pylib\audio
rem And the standard Python extensions.
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\lib
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\Build
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin\Build

: Do the freeze
if exist FreezeOpts del FreezeOpts
rem The channels...
echo -x ExternalChannel >> FreezeOpts
echo -x MACVideoChannel >> FreezeOpts
echo -x MidiChannel >> FreezeOpts
echo -x MovieChannel >> FreezeOpts
echo -x mpegchannel >> FreezeOpts
echo -x MPEGVideoChannel >> FreezeOpts
echo -x SGIVideoChannel >> FreezeOpts
echo -x ShellChannel >> FreezeOpts
echo -x VcrChannel >> FreezeOpts

rem Duration stuff
echo -x SGIVideoDuration >> FreezeOpts
echo -x MACVideoDuration >> FreezeOpts
echo -x MovieDuration >> FreezeOpts
rem ****************************
rem Do not exclude lib/MPEGVideoDuration
rem It is  imported by NTVideoDuration
rem echo -x MPEGVideoDuration >> FreezeOpts
rem ****************************

rem Audio stuff not supported on this platform
echo -x audiodevsun >> FreezeOpts
echo -x audiodevmac >> FreezeOpts
echo -x audiodevsgi >> FreezeOpts
echo -x audio8svx >> FreezeOpts
echo -x audiohcom >> FreezeOpts
echo -x audioop >> FreezeOpts
echo -x audiosndr >> FreezeOpts
echo -x audiosndt >> FreezeOpts
echo -x audiovoc >> FreezeOpts
echo -x sunaudiodev >> FreezeOpts
echo -x SUNAUDIODEV >> FreezeOpts

rem Other platform specific stuff
echo -x macostools >> FreezeOpts
echo -x mm >> FreezeOpts
echo -x mv >> FreezeOpts
echo -x SOCKS >> FreezeOpts
echo -x Tkinter >> FreezeOpts
echo -x WindowCanvas >> FreezeOpts
echo -x X >> FreezeOpts
echo -x Xm >> FreezeOpts
echo -x Xrm >> FreezeOpts
echo -x Xt >> FreezeOpts

rem Other to be checked
echo -x FCNTL >> FreezeOpts
echo -x IN >> FreezeOpts
echo -x Res >> FreezeOpts
echo -x TERMIOS >> FreezeOpts
echo -x Xcursorfont >> FreezeOpts
echo -x Xmd >> FreezeOpts
echo -x Xtdefs >> FreezeOpts
echo -x fcntl >> FreezeOpts
echo -x glX >> FreezeOpts
echo -x glXconst >> FreezeOpts
echo -x greekconv >> FreezeOpts
echo -x ic >> FreezeOpts
echo -x img >> FreezeOpts
echo -x imgcolormap >> FreezeOpts
echo -x imgconvert >> FreezeOpts
echo -x imgformat >> FreezeOpts
echo -x pwd >> FreezeOpts
echo -x sitecustomize >> FreezeOpts
echo -x termios >> FreezeOpts

echo -x readline >> FreezeOpts

rem Windows specific stuff we just dont want!!
echo -x win32ui  >> FreezeOpts
echo -x win32dbg >> FreezeOpts

rem EXCLUDE_WHAT
echo -x %EXCLUDE_WHAT% >> FreezeOpts

%PYTHON_EXE% %FREEZE% -s windows -i FreezeOpts -e %GRINS_HOME%\win32\extensions.ini %main_script% >> log.txt

: Make the target
rem echo Executing NMAKE
rem nmake


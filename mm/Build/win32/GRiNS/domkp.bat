rem BEGIN_CUSTOMIZATION

set GRINS_HOME=..\..\..

set FREEZE_WHAT=grins
set EXCLUDE_WHAT=cmifed

set INCLUDE_MMEXTENSIONS=no

set main_script=%GRINS_HOME%\fGRiNS.py

set PYTHON_EXE=..\..\..\..\python\PCbuild\python.exe

set PYTHONHOME=..\..\..\..\python

call c:\Program Files\Microsoft Visual Studio\VC98\Bin\vcvars32.bat

rem END_CUSTOMIZATION


del log.txt

rem The rest of the script assumes that the folder tree  
rem has the same structure as CWI's CVS root 
rem It is the same for both player(GRiNS) and editor (GRiNSed)


set PYTHONEX=%PYTHONHOME%\Extensions
set FREEZE=%PYTHONHOME%\Tools\freeze\freeze.py
set COMPILE=%PYTHONHOME%\Lib\compileall.py

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
IF NOT %INCLUDE_MMEXTENSIONS%==yes GOTO restpath
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\mmextensions\real\win32
:restpath
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\pylib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\win32\src\Build


rem And the standard Python extensions.
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\img\Lib
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\lib
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\Build
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin\Build

: Do the freeze
if exist FreezeOpts del FreezeOpts
rem The channels...
echo -x ExternalChannel >> FreezeOpts
echo -x MACVideoChannel >> FreezeOpts
rem echo -x MidiChannel >> FreezeOpts
echo -x MovieChannel >> FreezeOpts
echo -x mpegchannel >> FreezeOpts
echo -x MPEGVideoChannel >> FreezeOpts
echo -x SGIVideoChannel >> FreezeOpts
echo -x ShellChannel >> FreezeOpts
echo -x VcrChannel >> FreezeOpts
echo -x SMILTreeWrite >> FreezeOpts

rem Duration stuff
echo -x SGIVideoDuration >> FreezeOpts
echo -x MACVideoDuration >> FreezeOpts
echo -x MovieDuration >> FreezeOpts
rem ****************************
rem Do not exclude lib/MPEGVideoDuration
rem It is  imported by NTVideoDuration
rem echo -x MPEGVideoDuration >> FreezeOpts
rem ****************************

echo -x HierarchyView >> FreezeOpts

rem Audio stuff not supported on this platform
echo -x audio >> FreezeOpts
echo -x audio.convert >> FreezeOpts
echo -x audio.devsun >> FreezeOpts
echo -x audio.devmac >> FreezeOpts
echo -x audio.devsgi >> FreezeOpts
echo -x audio.file >> FreezeOpts
echo -x audio.format >> FreezeOpts
echo -x audio.hcom >> FreezeOpts
echo -x audio.sndr >> FreezeOpts
echo -x audio.sndt >> FreezeOpts
echo -x audio.svx8 >> FreezeOpts
echo -x audio.voc >> FreezeOpts
echo -x audio.what >> FreezeOpts
echo -x audioop >> FreezeOpts
echo -x sunaudiodev >> FreezeOpts
echo -x SUNAUDIODEV >> FreezeOpts
echo -x hcom >> FreezeOpts
echo -x sndr >> FreezeOpts
echo -x sndt >> FreezeOpts
echo -x svx8 >> FreezeOpts
echo -x voc >> FreezeOpts

rem Other platform specific stuff
echo -x ce >> FreezeOpts
echo -x MacOS >> FreezeOpts
echo -x macostools >> FreezeOpts
echo -x EasyDialogs >> FreezeOpts
echo -x Evt >> FreezeOpts
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
echo -x imgjpeg >> FreezeOpts
echo -x sitecustomize >> FreezeOpts
echo -x termios >> FreezeOpts

echo -x readline >> FreezeOpts
echo -x pwd >> FreezeOpts

rem Windows specific stuff we just dont want!!
echo -x win32ui  >> FreezeOpts
echo -x win32dbg >> FreezeOpts

rem exclude RMASDK
echo -x rma >> FreezeOpts

rem producer stuff
echo -x producer >> FreezeOpts
echo -x dshow >> FreezeOpts

rem EXCLUDE_WHAT
echo -x %EXCLUDE_WHAT% >> FreezeOpts

%PYTHON_EXE% -c "import MMAttrdefs" >> log.txt

%PYTHON_EXE% -OO %COMPILE% >> log.txt

%PYTHON_EXE% -OO %FREEZE% -s windows -i FreezeOpts -e %GRINS_HOME%\win32\grins_extensions.ini %main_script% >> log.txt

: Make the target
rem echo Executing NMAKE
rem nmake


@echo off
rem This batch file assumes "..\.." is the "root" directory of the app.
set GRINS_HOME=..\..
set FREEZE_WHAT=editor

rem Check if environment variables need setting up!
if '%PYTHONEX%==' goto no_env

if not '%FREEZE%==' goto freeze_override
set FREEZE %PYTHONHOME%\Tools\freeze\freeze.py
:freeze_override

if not '%FREEZE_ENV%==' goto freeze

echo Setting up freeze environment variables.
set FREEZE_ENV=1
set LIB=%LIB%;%pythonex%\win32\build;%pythonex%\pythonwin\build;%GRINS_HOME%\win32\src\Build
set INCLUDE=%INCLUDE%;%pythonex%\win32\src;%pythonex%\pythonwin
rem Set the following line if win32ui is frozen into the final .exe
rem set CL=%CL%;/D FREEZE_WIN32UI

:freeze

rem Set up the PYTHONPATH for the freeze - this points to all the GRINS directories
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

set main_script=%GRINS_HOME%\GRiNSed.py 
rem set main_script=test.py

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
echo -x MPEGVideoDuration >> FreezeOpts
echo -x MovieDuration >> FreezeOpts

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

rem Windows specific stuff we just dont want!!
echo -x win32ui  >> FreezeOpts
echo -x win32dbg >> FreezeOpts


%FREEZE% -s windows -i FreezeOpts -e %GRINS_HOME%\win32\grins_extensions.ini %main_script%
if errorlevel 1 goto xit

: Make the target
echo Executing NMAKE
nmake
goto xit

:no_env
echo You must set the following environment variables before freezing:
echo PYTHONEX=The path to the Python extensions (eg, the directory with
echo          "win32" and "pythonwin" sub-directories.
echo PYTHONHOME=The path to the root of Python-1.5.x
echo .
echo If you want to use a nonstandard freeze.py set FREEZE to its path
goto xit


:xit


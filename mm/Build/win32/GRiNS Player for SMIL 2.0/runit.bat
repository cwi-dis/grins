rem BEGIN_CUSTOMIZATION

set GRINS_HOME=D:\ufs\mm\cmif
set PYTHONHOME=D:\ufs\mm\python

set FREEZE_WHAT=grins
set EXCLUDE_WHAT=editor
set PRODUCT=smil20
set EMBEDDED=no

rem END_CUSTOMIZATION

set main_script=%GRINS_HOME%\fGRiNS.py
IF NOT %EMBEDDED%==yes GOTO gotmainscript
set main_script=%GRINS_HOME%\feGRiNS.py
:gotmainscript

set PYTHON_EXE=%PYTHONHOME%\PCbuild\python.exe


set PATH=%PATH%;%GRINS_HOME%\bin\win32


set PYTHONEX=%PYTHONHOME%\Extensions
set FREEZE=%PYTHONHOME%\Tools\freeze\freeze.py
set COMPILE=%PYTHONHOME%\Lib\compileall.py


rem Set up the PYTHONPATH for the freeze - this points to all the cmif directories
rem we need to perform the freeze.
set PYTHONPATH=%GRINS_HOME%
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%\smil20
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%\smil20\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib\win32
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\%FREEZE_WHAT%
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\common
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\lib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\pylib
set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\win32\src\Build

set PYTHONPATH=%PYTHONPATH%;%GRINS_HOME%\bin\win32

rem And the standard Python extensions.
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\img\Lib
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\lib
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\win32\Build
REM set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin
set PYTHONPATH=%PYTHONPATH%;%PYTHONEX%\Pythonwin\Build

rem Path for old standard python libraries
set PYTHONPATH=%PYTHONPATH%;%PYTHONHOME%\Lib\lib-old

%PYTHON_EXE%  %main_script%
echo OK


# Microsoft Developer Studio Project File - Name="GRiNSed" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Application" 0x0101

CFG=GRiNSed - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSed.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSed.mak" CFG="GRiNSed - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "GRiNSed - Win32 Release" (based on "Win32 (x86) Application")
!MESSAGE "GRiNSed - Win32 Debug" (based on "Win32 (x86) Application")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "GRiNSed - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "."
# PROP Intermediate_Dir "Build/Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /YX /FD /c
# ADD CPP /nologo /MD /W3 /GX /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /D "BUILD_FREEZE" /FD /c
# SUBTRACT CPP /YX /Yc /Yu
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /machine:I386
# ADD LINK32 python15.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /machine:I386
# Begin Custom Build
OutDir=.\.
InputPath=.\GRiNSed.exe
SOURCE="$(InputPath)"

"d:\ufs\mm\cmif\bin\win32 \GRiNSed.exe" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	del d:\ufs\mm\cmif\bin\win32\GRiNSed.exe 
	copy $(OutDir)\GRiNSed.exe d:\ufs\mm\cmif\bin\win32 
	
# End Custom Build

!ELSEIF  "$(CFG)" == "GRiNSed - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /YX /FD /GZ /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "BUILD_FREEZE" /D "_AFXDLL" /FR /YX /FD /GZ /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /debug /machine:I386 /pdbtype:sept
# ADD LINK32 python15_d.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /debug /machine:I386 /pdbtype:sept

!ENDIF 

# Begin Target

# Name "GRiNSed - Win32 Release"
# Name "GRiNSed - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
# Begin Source File

SOURCE=.\cmifdoc.ico
# End Source File
# Begin Source File

SOURCE=.\Editor.ico
# End Source File
# Begin Source File

SOURCE=.\Editor.rc
# End Source File
# Begin Source File

SOURCE=.\smildoc.ico
# End Source File
# End Group
# Begin Group "Python Source files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=..\..\..\..\python\PC\frozen_dllmain.c
# End Source File
# Begin Source File

SOURCE=..\..\..\pylib\frozenmain.c
# End Source File
# End Group
# Begin Group "Extensions"

# PROP Default_Filter ""
# Begin Source File

SOURCE=..\..\..\..\python\Extensions\win32\src\win32apimodule.cpp
# End Source File
# Begin Source File

SOURCE=..\..\..\..\python\Extensions\win32\src\win32trace.cpp
# End Source File
# End Group
# Begin Group "Freeze cmd files"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\domkp.bat
# End Source File
# Begin Source File

SOURCE=..\..\..\exec_cmif.py
# End Source File
# Begin Source File

SOURCE=..\..\..\fGRiNSed.py
# End Source File
# Begin Source File

SOURCE=..\..\..\grins_app_core.py
# End Source File
# Begin Source File

SOURCE=.\log.txt
# End Source File
# Begin Source File

SOURCE=.\Readme.txt
# End Source File
# End Group
# End Target
# End Project

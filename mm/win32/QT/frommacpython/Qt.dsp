# Microsoft Developer Studio Project File - Name="Qt" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=Qt - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "Qt.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "Qt.mak" CFG="Qt - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "Qt - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "Qt - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "Qt - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "QT_EXPORTS" /YX /FD /c
# ADD CPP /nologo /MT /W3 /GX /O2 /I "..\..\..\..\python\Include" /I "..\..\..\..\python\PC" /I "..\SDK\CIncludes" /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "QT_EXPORTS" /FR /YX /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x409 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /machine:I386
# ADD LINK32 ..\SDK\Libraries\QtmlClient.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /machine:I386 /out:"Release/Qt.pyd"
# Begin Custom Build
TargetPath=.\Release\Qt.pyd
InputPath=.\Release\Qt.pyd
SOURCE="$(InputPath)"

"..\..\..\bin\win32\Qt.pyd" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(TargetPath) ..\..\..\bin\win32

# End Custom Build

!ELSEIF  "$(CFG)" == "Qt - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "QT_EXPORTS" /YX /FD /GZ /c
# ADD CPP /nologo /MTd /W3 /Gm /GX /ZI /Od /I "..\..\..\..\python\Include" /I "..\..\..\..\python\PC" /I "..\SDK\CIncludes" /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "QT_EXPORTS" /FR /YX /FD /GZ /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x409 /d "_DEBUG"
# ADD RSC /l 0x409 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /debug /machine:I386 /pdbtype:sept
# ADD LINK32 ..\SDK\Libraries\QtmlClient.lib kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /incremental:no /debug /machine:I386 /out:"Debug/Qt_d.pyd" /pdbtype:sept
# Begin Custom Build
TargetPath=.\Debug\Qt_d.pyd
InputPath=.\Debug\Qt_d.pyd
SOURCE="$(InputPath)"

"..\..\..\bin\win32\Qt_d.pyd" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(TargetPath) ..\..\..\bin\win32

# End Custom Build

!ENDIF 

# Begin Target

# Name "Qt - Win32 Release"
# Name "Qt - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=.\macglue.h
# End Source File
# Begin Source File

SOURCE=.\pymactoolbox.cpp
# End Source File
# Begin Source File

SOURCE=.\pymactoolbox.h
# End Source File
# Begin Source File

SOURCE=.\pywintoolbox.cpp
# End Source File
# Begin Source File

SOURCE=.\pywintoolbox.h
# End Source File
# Begin Source File

SOURCE=.\Qt.rc
# End Source File
# Begin Source File

SOURCE=.\Qtmodule.cpp
# End Source File
# Begin Source File

SOURCE=.\test.py
# End Source File
# Begin Source File

SOURCE=.\test2.py
# End Source File
# End Group
# Begin Group "Temp"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\MovieCtlObj.inc
# End Source File
# Begin Source File

SOURCE=.\MovieObj.inc
# End Source File
# Begin Source File

SOURCE=.\qt.inc
# End Source File
# End Group
# End Target
# End Project

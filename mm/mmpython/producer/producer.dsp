# Microsoft Developer Studio Project File - Name="producer" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=producer - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "producer.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "producer.mak" CFG="producer - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "producer - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "producer - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "producer - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "producer_EXPORTS" /Yu"stdafx.h" /FD /c
# ADD CPP /nologo /MD /W3 /GX /O2 /I "./include" /I "./win32" /I "..\..\..\python\Include" /I "..\..\..\python\PC" /I "..\..\..\python\Extensions\win32\src" /D "NDEBUG" /D "WIN32" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "PY_EXPORTS" /D "_WINDLL" /D "_AFXDLL" /FR /FD /c
# SUBTRACT CPP /YX /Yc /Yu
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x409 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /machine:I386
# ADD LINK32 version.lib winmm.lib vfw32.lib /nologo /dll /machine:I386 /out:"Release/producer.pyd"
# Begin Custom Build
OutDir=.\Release
TargetPath=.\Release\producer.pyd
InputPath=.\Release\producer.pyd
SOURCE="$(InputPath)"

"$(OutDir)\log.txt" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(TargetPath) d:\ufs\mm\cmif\bin\win32

# End Custom Build

!ELSEIF  "$(CFG)" == "producer - Win32 Debug"

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
F90=df.exe
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "producer_EXPORTS" /Yu"stdafx.h" /FD /GZ /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /ZI /Od /I "./include" /D "_DEBUG" /D "WIN32" /D "_WINDOWS" /D "_MBCS" /D "_USRDLL" /D "PY_EXPORTS" /D "_WINDLL" /D "_AFXDLL" /FR /Yu"std.h" /FD /GZ /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /dll /debug /machine:I386 /pdbtype:sept
# ADD LINK32 advapi32.lib version.lib kernel32.lib user32.lib gdi32.lib winmm.lib vfw32.lib /nologo /dll /debug /machine:I386 /out:"Debug/producer_d.pyd" /pdbtype:sept
# Begin Custom Build
OutDir=.\Debug
InputPath=.\Debug\producer_d.pyd
SOURCE="$(InputPath)"

"$(OutDir)\log.txt" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	copy $(OutDir)\producer_d.pyd d:\ufs\mm\cmif\bin

# End Custom Build

!ENDIF 

# Begin Target

# Name "producer - Win32 Release"
# Name "producer - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;idl;hpj;bat"
# Begin Source File

SOURCE=.\include\engcodec.h
# End Source File
# Begin Source File

SOURCE=.\include\engtargs.h
# End Source File
# Begin Source File

SOURCE=.\include\engtypes.h
# End Source File
# Begin Source File

SOURCE=.\include\pncom.h
# End Source File
# Begin Source File

SOURCE=.\include\pnresult.h
# End Source File
# Begin Source File

SOURCE=.\include\pntypes.h
# End Source File
# Begin Source File

SOURCE=.\include\pnwintyp.h
# End Source File
# Begin Source File

SOURCE=.\include\progsink.h
# End Source File
# Begin Source File

SOURCE=.\include\rmaenum.h
# End Source File
# Begin Source File

SOURCE=.\include\rmapckts.h
# End Source File
# Begin Source File

SOURCE=.\include\rmbldeng.h
# End Source File
# Begin Source File

SOURCE=.\include\rmmetain.h
# End Source File
# Begin Source File

SOURCE=.\rprod.cpp

!IF  "$(CFG)" == "producer - Win32 Release"

# SUBTRACT CPP /YX /Yc /Yu

!ELSEIF  "$(CFG)" == "producer - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\lib\enceng.lib
# End Source File
# End Group
# End Target
# End Project

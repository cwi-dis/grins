# Microsoft Developer Studio Project File - Name="CmifEx" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 5.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=CmifEx - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "CmifEx.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "CmifEx.mak" CFG="CmifEx - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "CmifEx - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "CmifEx - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe

!IF  "$(CFG)" == "CmifEx - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir ".\Release"
# PROP BASE Intermediate_Dir ".\Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir ".\Release"
# PROP Intermediate_Dir ".\Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MD /W3 /GX /Od /I "c:\jack\pythonex\pythonwin" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 Python15.Lib /nologo /base:"0x1e240000" /subsystem:windows /dll /machine:I386 /out:".\release\cmifex.pyd" /libpath:"c:\jack\pythonex\pythonwin\Build"
# SUBTRACT LINK32 /pdb:none /nodefaultlib

!ELSEIF  "$(CFG)" == "CmifEx - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir ".\Debug"
# PROP BASE Intermediate_Dir ".\Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir ".\Debug"
# PROP Intermediate_Dir ".\Debug"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /Zi /Od /I "c:\jack\pythonex\pythonwin" /D "_DEBUG" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /FD /c
# SUBTRACT CPP /Gy /YX
# ADD BASE MTL /nologo /D "_DEBUG" /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 Python.Lib /nologo /base:"0x1e240000" /subsystem:windows /dll /debug /machine:I386 /out:".\debug\cmifex.pyd" /libpath:"c:\jack\pythonex\pythonwin\Build"
# SUBTRACT LINK32 /pdb:none /nodefaultlib

!ENDIF 

# Begin Target

# Name "CmifEx - Win32 Release"
# Name "CmifEx - Win32 Debug"
# Begin Group "Source Files"

# PROP Default_Filter "cpp;c;cxx;rc;def;r;odl;hpj;bat;for;f90"
# Begin Source File

SOURCE=.\Cmif.rc

!IF  "$(CFG)" == "CmifEx - Win32 Release"

!ELSEIF  "$(CFG)" == "CmifEx - Win32 Debug"

!ENDIF 

# End Source File
# Begin Source File

SOURCE=.\cmifexhelp.cpp
# End Source File
# Begin Source File

SOURCE=.\cmifexmodule.cpp
# End Source File
# Begin Source File

SOURCE=.\Ezfont.c
# End Source File
# End Group
# Begin Group "Header Files"

# PROP Default_Filter "h;hpp;hxx;hm;inl;fi;fd"
# Begin Source File

SOURCE=.\allobjects.h
# End Source File
# Begin Source File

SOURCE=.\cmifex.h
# End Source File
# Begin Source File

SOURCE=.\cmifexhelp.h
# End Source File
# Begin Source File

SOURCE=.\Ezfont.h
# End Source File
# Begin Source File

SOURCE=.\StdAfx.h
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;cnt;rtf;gif;jpg;jpeg;jpe"
# Begin Source File

SOURCE=.\Res\C_no04.cur
# End Source File
# Begin Source File

SOURCE=.\res\cmif.ico
# End Source File
# Begin Source File

SOURCE=.\res\cmif.rc2
# End Source File
# Begin Source File

SOURCE=.\Res\Copy4way.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cur00001.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cur00002.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cursor1.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cursor2.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cursor9.cur
# End Source File
# Begin Source File

SOURCE=.\Res\grab_han.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_move.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_ne.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_ns.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_nw.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_point.cur
# End Source File
# Begin Source File

SOURCE=.\Res\H_we.cur
# End Source File
# Begin Source File

SOURCE=.\RES\hand.cur
# End Source File
# Begin Source File

SOURCE=.\Res\l_strech.cur
# End Source File
# Begin Source File

SOURCE=.\Res\Misc06.ico
# End Source File
# Begin Source File

SOURCE=.\res\pause.ico
# End Source File
# Begin Source File

SOURCE=.\res\play.ico
# End Source File
# Begin Source File

SOURCE=.\RES\python.ico
# End Source File
# Begin Source File

SOURCE=.\res\stop.ico
# End Source File
# Begin Source File

SOURCE=.\Res\Timer01.ico
# End Source File
# Begin Source File

SOURCE=.\Res\ul_strec.cur
# End Source File
# End Group
# End Target
# End Project

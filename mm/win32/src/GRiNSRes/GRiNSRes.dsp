# Microsoft Developer Studio Project File - Name="GRiNSRes" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 6.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

CFG=GRiNSRes - Win32 Release
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSRes.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "GRiNSRes.mak" CFG="GRiNSRes - Win32 Release"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "GRiNSRes - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 

# Begin Project
# PROP AllowPerConfigDependencies 0
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
MTL=midl.exe
RSC=rc.exe
# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "..\Build"
# PROP Intermediate_Dir "..\Build\Temp\GRiNSRes\Release"
# PROP Ignore_Export_Lib 0
# PROP Target_Dir ""
F90=df.exe
# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /FD /c
# ADD CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /FD /c
# ADD BASE MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD MTL /nologo /D "NDEBUG" /mktyplib203 /o "NUL" /win32
# ADD BASE RSC /l 0xc09 /d "NDEBUG"
# ADD RSC /l 0xc09 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /pdb:none /machine:I386 /noentry
# Begin Custom Build - Generating grinsRC.py
OutDir=.\..\Build
InputPath=\cmif\win32\src\Build\GRiNSRes.dll
SOURCE="$(InputPath)"

"$(OutDir)\grinsRC.py" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"
	e:\cmif\bin\python e:\python\tools\scripts\h2py.py  GRiNSRes.h 
	copy GRiNSRes.py $(OutDir)\grinsRC.py 
	del GRiNSRes.py 
	copy $(OutDir)\GRiNSRes.dll e:\cmif\bin 
	
# End Custom Build
# Begin Target

# Name "GRiNSRes - Win32 Release"
# Begin Group "Resources"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\Res\C_no04.cur
# End Source File
# Begin Source File

SOURCE=.\Res\CMIF.ICO
# End Source File
# Begin Source File

SOURCE=.\Res\Copy4way.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cur00001.cur
# End Source File
# Begin Source File

SOURCE=.\Res\cursor2.cur
# End Source File
# Begin Source File

SOURCE=.\Res\grab_han.cur
# End Source File
# Begin Source File

SOURCE=.\RES\grins_ed.ico
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

SOURCE=.\Res\hand.cur
# End Source File
# Begin Source File

SOURCE=.\Res\l_strech.cur
# End Source File
# Begin Source File

SOURCE=.\Res\pause.ico
# End Source File
# Begin Source File

SOURCE=.\Res\play.ico
# End Source File
# Begin Source File

SOURCE=.\Res\python.ico
# End Source File
# Begin Source File

SOURCE=.\Res\stop.ico
# End Source File
# Begin Source File

SOURCE=.\Res\Timer01.ico
# End Source File
# Begin Source File

SOURCE=.\Res\ul_strec.cur
# End Source File
# End Group
# Begin Source File

SOURCE=.\RES\GRiNSed.ico
# End Source File
# Begin Source File

SOURCE=.\RES\grinsed1.bmp
# End Source File
# Begin Source File

SOURCE=.\RES\grinsed2.bmp
# End Source File
# Begin Source File

SOURCE=..\Build\grinsRC.py
# End Source File
# Begin Source File

SOURCE=.\GRiNSRes.h
# End Source File
# Begin Source File

SOURCE=.\GRiNSRes.rc
# End Source File
# Begin Source File

SOURCE=.\RES\ico00001.ico
# End Source File
# Begin Source File

SOURCE=.\RES\Toolbar.bmp
# End Source File
# End Target
# End Project

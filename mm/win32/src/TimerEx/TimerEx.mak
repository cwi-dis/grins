# Microsoft Developer Studio Generated NMAKE File, Format Version 4.20
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

!IF "$(CFG)" == ""
CFG=TimerEx - Win32 Debug
!MESSAGE No configuration specified.  Defaulting to TimerEx - Win32 Debug.
!ENDIF 

!IF "$(CFG)" != "TimerEx - Win32 Release" && "$(CFG)" !=\
 "TimerEx - Win32 Debug"
!MESSAGE Invalid configuration "$(CFG)" specified.
!MESSAGE You can specify a configuration when running NMAKE on this makefile
!MESSAGE by defining the macro CFG on the command line.  For example:
!MESSAGE 
!MESSAGE NMAKE /f "TimerEx.mak" CFG="TimerEx - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "TimerEx - Win32 Release" (based on\
 "Win32 (x86) Dynamic-Link Library")
!MESSAGE "TimerEx - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE 
!ERROR An invalid configuration is specified.
!ENDIF 

!IF "$(OS)" == "Windows_NT"
NULL=
!ELSE 
NULL=nul
!ENDIF 
################################################################################
# Begin Project
# PROP Target_Last_Scanned "TimerEx - Win32 Debug"
RSC=rc.exe
CPP=cl.exe
MTL=mktyplib.exe

!IF  "$(CFG)" == "TimerEx - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
OUTDIR=.\Release
INTDIR=.\Release

ALL : "$(OUTDIR)\timerex.pyd" "$(OUTDIR)\TimerEx.bsc"

CLEAN : 
	-@erase "$(INTDIR)\timerexmodule.obj"
	-@erase "$(INTDIR)\timerexmodule.sbr"
	-@erase "$(OUTDIR)\TimerEx.bsc"
	-@erase "$(OUTDIR)\timerex.exp"
	-@erase "$(OUTDIR)\timerex.lib"
	-@erase "$(OUTDIR)\timerex.pyd"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MT /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MD /W3 /GX /Od /D "_AFXDLL" /D "USE_DL_IMPORT" /D "HAVE_CONFIG_H" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D "_MBCS" /FR /c
CPP_PROJ=/nologo /MD /W3 /GX /Od /D "_AFXDLL" /D "USE_DL_IMPORT" /D\
 "HAVE_CONFIG_H" /D LEAVE=__LEAVE /D FINALLY=__FINALLY /D EXCEPT=__EXCEPT /D\
 CRTAPI1=_cdecl /D CRTAPI2=_cdecl /D _X86=1 /D WINVER=0x0400 /D "_WINDLL" /D\
 "_MBCS" /FR"$(INTDIR)/" /Fo"$(INTDIR)/" /c 
CPP_OBJS=.\Release/
CPP_SBRS=.\Release/
# ADD BASE MTL /nologo /D "NDEBUG" /win32
# ADD MTL /nologo /D "NDEBUG" /win32
MTL_PROJ=/nologo /D "NDEBUG" /win32 
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/TimerEx.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\timerexmodule.sbr"

"$(OUTDIR)\TimerEx.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /machine:I386 /out:".\release\timerex.pyd" /SECTION:SHARED,RWS
# SUBTRACT LINK32 /pdb:none
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:no /pdb:"$(OUTDIR)/timerex.pdb" /machine:I386\
 /out:"$(OUTDIR)/timerex.pyd" /implib:"$(OUTDIR)/timerex.lib"\
 /SECTION:SHARED,RWS 
LINK32_OBJS= \
	"$(INTDIR)\timerexmodule.obj"

"$(OUTDIR)\timerex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ELSEIF  "$(CFG)" == "TimerEx - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 2
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
OUTDIR=.\Debug
INTDIR=.\Debug

ALL : "$(OUTDIR)\timerex.pyd" "$(OUTDIR)\TimerEx.bsc"

CLEAN : 
	-@erase "$(INTDIR)\timerexmodule.obj"
	-@erase "$(INTDIR)\timerexmodule.sbr"
	-@erase "$(INTDIR)\vc40.idb"
	-@erase "$(INTDIR)\vc40.pdb"
	-@erase "$(OUTDIR)\TimerEx.bsc"
	-@erase "$(OUTDIR)\timerex.exp"
	-@erase "$(OUTDIR)\timerex.ilk"
	-@erase "$(OUTDIR)\timerex.lib"
	-@erase "$(OUTDIR)\timerex.pdb"
	-@erase "$(OUTDIR)\timerex.pyd"

"$(OUTDIR)" :
    if not exist "$(OUTDIR)/$(NULL)" mkdir "$(OUTDIR)"

# ADD BASE CPP /nologo /MTd /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /YX /c
# ADD CPP /nologo /MDd /W3 /Gm /GX /Zi /Od /D "_DEBUG" /D "USE_DL_IMPORT" /D "HAVE_CONFIG_H" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR /c
# SUBTRACT CPP /Gy /YX
CPP_PROJ=/nologo /MDd /W3 /Gm /GX /Zi /Od /D "_DEBUG" /D "USE_DL_IMPORT" /D\
 "HAVE_CONFIG_H" /D "_WINDLL" /D "_AFXDLL" /D "_MBCS" /FR"$(INTDIR)/"\
 /Fo"$(INTDIR)/" /Fd"$(INTDIR)/" /c 
CPP_OBJS=.\Debug/
CPP_SBRS=.\Debug/
# ADD BASE MTL /nologo /D "_DEBUG" /win32
# ADD MTL /nologo /D "_DEBUG" /win32
MTL_PROJ=/nologo /D "_DEBUG" /win32 
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG" /d "_AFXDLL"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/TimerEx.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\timerexmodule.sbr"

"$(OUTDIR)\TimerEx.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /debug /machine:I386 /out:".\debug\timerex.pyd" /SECTION:SHARED,RWS
# SUBTRACT LINK32 /pdb:none
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:yes /pdb:"$(OUTDIR)/timerex.pdb" /debug /machine:I386\
 /out:"$(OUTDIR)/timerex.pyd" /implib:"$(OUTDIR)/timerex.lib"\
 /SECTION:SHARED,RWS 
LINK32_OBJS= \
	"$(INTDIR)\timerexmodule.obj"

"$(OUTDIR)\timerex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ENDIF 

.c{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_OBJS)}.obj:
   $(CPP) $(CPP_PROJ) $<  

.c{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cpp{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

.cxx{$(CPP_SBRS)}.sbr:
   $(CPP) $(CPP_PROJ) $<  

################################################################################
# Begin Target

# Name "TimerEx - Win32 Release"
# Name "TimerEx - Win32 Debug"

!IF  "$(CFG)" == "TimerEx - Win32 Release"

!ELSEIF  "$(CFG)" == "TimerEx - Win32 Debug"

!ENDIF 

################################################################################
# Begin Source File

SOURCE=.\timerexmodule.cpp
DEP_CPP_TIMER=\
	"..\..\python1.4\Src\Include\accessobject.h"\
	"..\..\python1.4\Src\Include\bltinmodule.h"\
	"..\..\python1.4\Src\Include\ceval.h"\
	"..\..\python1.4\Src\Include\classobject.h"\
	"..\..\python1.4\Src\Include\cobject.h"\
	"..\..\python1.4\Src\Include\complexobject.h"\
	"..\..\python1.4\Src\Include\config.h"\
	"..\..\python1.4\Src\Include\fileobject.h"\
	"..\..\python1.4\Src\Include\floatobject.h"\
	"..\..\python1.4\Src\Include\funcobject.h"\
	"..\..\python1.4\Src\Include\import.h"\
	"..\..\python1.4\Src\Include\intobject.h"\
	"..\..\python1.4\Src\Include\intrcheck.h"\
	"..\..\python1.4\Src\Include\listobject.h"\
	"..\..\python1.4\Src\Include\longobject.h"\
	"..\..\python1.4\Src\Include\mappingobject.h"\
	"..\..\python1.4\Src\Include\methodobject.h"\
	"..\..\python1.4\Src\Include\moduleobject.h"\
	"..\..\python1.4\Src\Include\mymalloc.h"\
	"..\..\python1.4\Src\Include\myproto.h"\
	"..\..\python1.4\Src\Include\object.h"\
	"..\..\python1.4\Src\Include\objimpl.h"\
	"..\..\python1.4\Src\Include\pydebug.h"\
	"..\..\python1.4\Src\Include\pyerrors.h"\
	"..\..\python1.4\Src\Include\pythonrun.h"\
	"..\..\python1.4\Src\Include\rangeobject.h"\
	"..\..\python1.4\Src\Include\rename2.h"\
	"..\..\python1.4\Src\Include\sliceobject.h"\
	"..\..\python1.4\Src\Include\stringobject.h"\
	"..\..\python1.4\Src\Include\sysmodule.h"\
	"..\..\python1.4\Src\Include\thread.h"\
	"..\..\python1.4\Src\Include\traceback.h"\
	"..\..\python1.4\Src\Include\tupleobject.h"\
	".\StdAfx.h"\
	".\timerex.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	{$(INCLUDE)}"\win32assoc.h"\
	{$(INCLUDE)}"\win32cmd.h"\
	{$(INCLUDE)}"\win32ui.h"\
	{$(INCLUDE)}"\win32win.h"\
	

"$(INTDIR)\timerexmodule.obj" : $(SOURCE) $(DEP_CPP_TIMER) "$(INTDIR)"

"$(INTDIR)\timerexmodule.sbr" : $(SOURCE) $(DEP_CPP_TIMER) "$(INTDIR)"


# End Source File
# End Target
# End Project
################################################################################

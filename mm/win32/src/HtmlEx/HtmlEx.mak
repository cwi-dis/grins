# Microsoft Developer Studio Generated NMAKE File, Format Version 4.20
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Dynamic-Link Library" 0x0102

!IF "$(CFG)" == ""
CFG=HtmlEx - Win32 Debug
!MESSAGE No configuration specified.  Defaulting to HtmlEx - Win32 Debug.
!ENDIF 

!IF "$(CFG)" != "HtmlEx - Win32 Release" && "$(CFG)" != "HtmlEx - Win32 Debug"
!MESSAGE Invalid configuration "$(CFG)" specified.
!MESSAGE You can specify a configuration when running NMAKE on this makefile
!MESSAGE by defining the macro CFG on the command line.  For example:
!MESSAGE 
!MESSAGE NMAKE /f "HtmlEx.mak" CFG="HtmlEx - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "HtmlEx - Win32 Release" (based on "Win32 (x86) Dynamic-Link Library")
!MESSAGE "HtmlEx - Win32 Debug" (based on "Win32 (x86) Dynamic-Link Library")
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
# PROP Target_Last_Scanned "HtmlEx - Win32 Debug"
RSC=rc.exe
CPP=cl.exe
MTL=mktyplib.exe

!IF  "$(CFG)" == "HtmlEx - Win32 Release"

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

ALL : "$(OUTDIR)\Htmlex.pyd" "$(OUTDIR)\HtmlEx.bsc"

CLEAN : 
	-@erase "$(INTDIR)\ContainerWnd.obj"
	-@erase "$(INTDIR)\ContainerWnd.sbr"
	-@erase "$(INTDIR)\docheader.obj"
	-@erase "$(INTDIR)\docheader.sbr"
	-@erase "$(INTDIR)\docheaders.obj"
	-@erase "$(INTDIR)\docheaders.sbr"
	-@erase "$(INTDIR)\docinput.obj"
	-@erase "$(INTDIR)\docinput.sbr"
	-@erase "$(INTDIR)\docoutput.obj"
	-@erase "$(INTDIR)\docoutput.sbr"
	-@erase "$(INTDIR)\font.obj"
	-@erase "$(INTDIR)\font.sbr"
	-@erase "$(INTDIR)\html.obj"
	-@erase "$(INTDIR)\Html.res"
	-@erase "$(INTDIR)\html.sbr"
	-@erase "$(INTDIR)\Htmlexmodule.obj"
	-@erase "$(INTDIR)\Htmlexmodule.sbr"
	-@erase "$(INTDIR)\htmlform.obj"
	-@erase "$(INTDIR)\htmlform.sbr"
	-@erase "$(INTDIR)\htmlforms.obj"
	-@erase "$(INTDIR)\htmlforms.sbr"
	-@erase "$(OUTDIR)\HtmlEx.bsc"
	-@erase "$(OUTDIR)\Htmlex.exp"
	-@erase "$(OUTDIR)\Htmlex.lib"
	-@erase "$(OUTDIR)\Htmlex.pyd"

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
RSC_PROJ=/l 0x408 /fo"$(INTDIR)/Html.res" /d "NDEBUG" /d "_AFXDLL" 
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/HtmlEx.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\ContainerWnd.sbr" \
	"$(INTDIR)\docheader.sbr" \
	"$(INTDIR)\docheaders.sbr" \
	"$(INTDIR)\docinput.sbr" \
	"$(INTDIR)\docoutput.sbr" \
	"$(INTDIR)\font.sbr" \
	"$(INTDIR)\html.sbr" \
	"$(INTDIR)\Htmlexmodule.sbr" \
	"$(INTDIR)\htmlform.sbr" \
	"$(INTDIR)\htmlforms.sbr"

"$(OUTDIR)\HtmlEx.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /machine:I386 /out:".\release\Htmlex.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:no /pdb:"$(OUTDIR)/Htmlex.pdb" /machine:I386\
 /out:"$(OUTDIR)/Htmlex.pyd" /implib:"$(OUTDIR)/Htmlex.lib" 
LINK32_OBJS= \
	"$(INTDIR)\ContainerWnd.obj" \
	"$(INTDIR)\docheader.obj" \
	"$(INTDIR)\docheaders.obj" \
	"$(INTDIR)\docinput.obj" \
	"$(INTDIR)\docoutput.obj" \
	"$(INTDIR)\font.obj" \
	"$(INTDIR)\html.obj" \
	"$(INTDIR)\Html.res" \
	"$(INTDIR)\Htmlexmodule.obj" \
	"$(INTDIR)\htmlform.obj" \
	"$(INTDIR)\htmlforms.obj"

"$(OUTDIR)\Htmlex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
    $(LINK32) @<<
  $(LINK32_FLAGS) $(LINK32_OBJS)
<<

!ELSEIF  "$(CFG)" == "HtmlEx - Win32 Debug"

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

ALL : "$(OUTDIR)\Htmlex.pyd" "$(OUTDIR)\HtmlEx.bsc"

CLEAN : 
	-@erase "$(INTDIR)\ContainerWnd.obj"
	-@erase "$(INTDIR)\ContainerWnd.sbr"
	-@erase "$(INTDIR)\docheader.obj"
	-@erase "$(INTDIR)\docheader.sbr"
	-@erase "$(INTDIR)\docheaders.obj"
	-@erase "$(INTDIR)\docheaders.sbr"
	-@erase "$(INTDIR)\docinput.obj"
	-@erase "$(INTDIR)\docinput.sbr"
	-@erase "$(INTDIR)\docoutput.obj"
	-@erase "$(INTDIR)\docoutput.sbr"
	-@erase "$(INTDIR)\font.obj"
	-@erase "$(INTDIR)\font.sbr"
	-@erase "$(INTDIR)\html.obj"
	-@erase "$(INTDIR)\Html.res"
	-@erase "$(INTDIR)\html.sbr"
	-@erase "$(INTDIR)\Htmlexmodule.obj"
	-@erase "$(INTDIR)\Htmlexmodule.sbr"
	-@erase "$(INTDIR)\htmlform.obj"
	-@erase "$(INTDIR)\htmlform.sbr"
	-@erase "$(INTDIR)\htmlforms.obj"
	-@erase "$(INTDIR)\htmlforms.sbr"
	-@erase "$(INTDIR)\vc40.idb"
	-@erase "$(INTDIR)\vc40.pdb"
	-@erase "$(OUTDIR)\HtmlEx.bsc"
	-@erase "$(OUTDIR)\Htmlex.exp"
	-@erase "$(OUTDIR)\Htmlex.ilk"
	-@erase "$(OUTDIR)\Htmlex.lib"
	-@erase "$(OUTDIR)\Htmlex.pdb"
	-@erase "$(OUTDIR)\Htmlex.pyd"

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
RSC_PROJ=/l 0x408 /fo"$(INTDIR)/Html.res" /d "_DEBUG" /d "_AFXDLL" 
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
BSC32_FLAGS=/nologo /o"$(OUTDIR)/HtmlEx.bsc" 
BSC32_SBRS= \
	"$(INTDIR)\ContainerWnd.sbr" \
	"$(INTDIR)\docheader.sbr" \
	"$(INTDIR)\docheaders.sbr" \
	"$(INTDIR)\docinput.sbr" \
	"$(INTDIR)\docoutput.sbr" \
	"$(INTDIR)\font.sbr" \
	"$(INTDIR)\html.sbr" \
	"$(INTDIR)\Htmlexmodule.sbr" \
	"$(INTDIR)\htmlform.sbr" \
	"$(INTDIR)\htmlforms.sbr"

"$(OUTDIR)\HtmlEx.bsc" : "$(OUTDIR)" $(BSC32_SBRS)
    $(BSC32) @<<
  $(BSC32_FLAGS) $(BSC32_SBRS)
<<

LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:windows /dll /debug /machine:I386
# ADD LINK32 Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows /dll /debug /machine:I386 /out:".\debug\Htmlex.pyd"
# SUBTRACT LINK32 /pdb:none /nodefaultlib
LINK32_FLAGS=Python.Lib win32ui.lib /nologo /base:0x1e240000 /subsystem:windows\
 /dll /incremental:yes /pdb:"$(OUTDIR)/Htmlex.pdb" /debug /machine:I386\
 /out:"$(OUTDIR)/Htmlex.pyd" /implib:"$(OUTDIR)/Htmlex.lib" 
LINK32_OBJS= \
	"$(INTDIR)\ContainerWnd.obj" \
	"$(INTDIR)\docheader.obj" \
	"$(INTDIR)\docheaders.obj" \
	"$(INTDIR)\docinput.obj" \
	"$(INTDIR)\docoutput.obj" \
	"$(INTDIR)\font.obj" \
	"$(INTDIR)\html.obj" \
	"$(INTDIR)\Html.res" \
	"$(INTDIR)\Htmlexmodule.obj" \
	"$(INTDIR)\htmlform.obj" \
	"$(INTDIR)\htmlforms.obj"

"$(OUTDIR)\Htmlex.pyd" : "$(OUTDIR)" $(DEF_FILE) $(LINK32_OBJS)
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

# Name "HtmlEx - Win32 Release"
# Name "HtmlEx - Win32 Debug"

!IF  "$(CFG)" == "HtmlEx - Win32 Release"

!ELSEIF  "$(CFG)" == "HtmlEx - Win32 Debug"

!ENDIF 

################################################################################
# Begin Source File

SOURCE=.\Html.rc
DEP_RSC_HTML_=\
	".\res\cmif.ico"\
	".\res\cmif.rc2"\
	".\res\pause.ico"\
	".\res\play.ico"\
	".\RES\python.ico"\
	".\res\stop.ico"\
	

"$(INTDIR)\Html.res" : $(SOURCE) $(DEP_RSC_HTML_) "$(INTDIR)"
   $(RSC) $(RSC_PROJ) $(SOURCE)


# End Source File
################################################################################
# Begin Source File

SOURCE=.\Htmlexmodule.cpp

!IF  "$(CFG)" == "HtmlEx - Win32 Release"

DEP_CPP_HTMLE=\
	"..\..\..\python1.4\Src\Include\config.h"\
	"..\..\..\python1.4\Src\Include\myproto.h"\
	".\ContainerWnd.h"\
	".\font.h"\
	".\html.h"\
	".\htmlex.h"\
	".\StdAfx.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	

"$(INTDIR)\Htmlexmodule.obj" : $(SOURCE) $(DEP_CPP_HTMLE) "$(INTDIR)"

"$(INTDIR)\Htmlexmodule.sbr" : $(SOURCE) $(DEP_CPP_HTMLE) "$(INTDIR)"


!ELSEIF  "$(CFG)" == "HtmlEx - Win32 Debug"

DEP_CPP_HTMLE=\
	"..\..\..\python1.4\Src\Include\accessobject.h"\
	"..\..\..\python1.4\Src\Include\bltinmodule.h"\
	"..\..\..\python1.4\Src\Include\ceval.h"\
	"..\..\..\python1.4\Src\Include\classobject.h"\
	"..\..\..\python1.4\Src\Include\cobject.h"\
	"..\..\..\python1.4\Src\Include\complexobject.h"\
	"..\..\..\python1.4\Src\Include\config.h"\
	"..\..\..\python1.4\Src\Include\fileobject.h"\
	"..\..\..\python1.4\Src\Include\floatobject.h"\
	"..\..\..\python1.4\Src\Include\funcobject.h"\
	"..\..\..\python1.4\Src\Include\import.h"\
	"..\..\..\python1.4\Src\Include\intobject.h"\
	"..\..\..\python1.4\Src\Include\intrcheck.h"\
	"..\..\..\python1.4\Src\Include\listobject.h"\
	"..\..\..\python1.4\Src\Include\longobject.h"\
	"..\..\..\python1.4\Src\Include\mappingobject.h"\
	"..\..\..\python1.4\Src\Include\methodobject.h"\
	"..\..\..\python1.4\Src\Include\moduleobject.h"\
	"..\..\..\python1.4\Src\Include\mymalloc.h"\
	"..\..\..\python1.4\Src\Include\myproto.h"\
	"..\..\..\python1.4\Src\Include\object.h"\
	"..\..\..\python1.4\Src\Include\objimpl.h"\
	"..\..\..\python1.4\Src\Include\pydebug.h"\
	"..\..\..\python1.4\Src\Include\pyerrors.h"\
	"..\..\..\python1.4\Src\Include\pythonrun.h"\
	"..\..\..\python1.4\Src\Include\rangeobject.h"\
	"..\..\..\python1.4\Src\Include\rename2.h"\
	"..\..\..\python1.4\Src\Include\sliceobject.h"\
	"..\..\..\python1.4\Src\Include\stringobject.h"\
	"..\..\..\python1.4\Src\Include\sysmodule.h"\
	"..\..\..\python1.4\Src\Include\thread.h"\
	"..\..\..\python1.4\Src\Include\traceback.h"\
	"..\..\..\python1.4\Src\Include\tupleobject.h"\
	".\ContainerWnd.h"\
	".\font.h"\
	".\html.h"\
	".\htmlex.h"\
	".\StdAfx.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	{$(INCLUDE)}"\win32assoc.h"\
	{$(INCLUDE)}"\win32cmd.h"\
	{$(INCLUDE)}"\Win32ui.h"\
	{$(INCLUDE)}"\win32win.h"\
	

"$(INTDIR)\Htmlexmodule.obj" : $(SOURCE) $(DEP_CPP_HTMLE) "$(INTDIR)"

"$(INTDIR)\Htmlexmodule.sbr" : $(SOURCE) $(DEP_CPP_HTMLE) "$(INTDIR)"


!ENDIF 

# End Source File
################################################################################
# Begin Source File

SOURCE=.\docoutput.cpp
DEP_CPP_DOCOU=\
	".\docheaders.h"\
	".\docoutput.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\docoutput.obj" : $(SOURCE) $(DEP_CPP_DOCOU) "$(INTDIR)"

"$(INTDIR)\docoutput.sbr" : $(SOURCE) $(DEP_CPP_DOCOU) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\docheaders.cpp
DEP_CPP_DOCHE=\
	".\docheader.h"\
	".\docheaders.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\docheaders.obj" : $(SOURCE) $(DEP_CPP_DOCHE) "$(INTDIR)"

"$(INTDIR)\docheaders.sbr" : $(SOURCE) $(DEP_CPP_DOCHE) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\htmlform.cpp
DEP_CPP_HTMLF=\
	".\htmlform.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\htmlform.obj" : $(SOURCE) $(DEP_CPP_HTMLF) "$(INTDIR)"

"$(INTDIR)\htmlform.sbr" : $(SOURCE) $(DEP_CPP_HTMLF) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\htmlforms.cpp
DEP_CPP_HTMLFO=\
	".\htmlform.h"\
	".\htmlforms.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\htmlforms.obj" : $(SOURCE) $(DEP_CPP_HTMLFO) "$(INTDIR)"

"$(INTDIR)\htmlforms.sbr" : $(SOURCE) $(DEP_CPP_HTMLFO) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\font.cpp
DEP_CPP_FONT_=\
	".\font.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\font.obj" : $(SOURCE) $(DEP_CPP_FONT_) "$(INTDIR)"

"$(INTDIR)\font.sbr" : $(SOURCE) $(DEP_CPP_FONT_) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\docinput.cpp
DEP_CPP_DOCIN=\
	".\docheaders.h"\
	".\docinput.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\docinput.obj" : $(SOURCE) $(DEP_CPP_DOCIN) "$(INTDIR)"

"$(INTDIR)\docinput.sbr" : $(SOURCE) $(DEP_CPP_DOCIN) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\html.cpp
DEP_CPP_HTML_C=\
	".\docinput.h"\
	".\docoutput.h"\
	".\font.h"\
	".\html.h"\
	".\htmlforms.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\html.obj" : $(SOURCE) $(DEP_CPP_HTML_C) "$(INTDIR)"

"$(INTDIR)\html.sbr" : $(SOURCE) $(DEP_CPP_HTML_C) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\docheader.cpp
DEP_CPP_DOCHEA=\
	".\docheader.h"\
	".\StdAfx.h"\
	

"$(INTDIR)\docheader.obj" : $(SOURCE) $(DEP_CPP_DOCHEA) "$(INTDIR)"

"$(INTDIR)\docheader.sbr" : $(SOURCE) $(DEP_CPP_DOCHEA) "$(INTDIR)"


# End Source File
################################################################################
# Begin Source File

SOURCE=.\ContainerWnd.cpp

!IF  "$(CFG)" == "HtmlEx - Win32 Release"

DEP_CPP_CONTA=\
	"..\..\..\python1.4\Src\Include\config.h"\
	"..\..\..\python1.4\Src\Include\myproto.h"\
	".\ContainerWnd.h"\
	".\html.h"\
	".\htmlex.h"\
	".\htmlform.h"\
	".\htmlforms.h"\
	".\StdAfx.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	

"$(INTDIR)\ContainerWnd.obj" : $(SOURCE) $(DEP_CPP_CONTA) "$(INTDIR)"

"$(INTDIR)\ContainerWnd.sbr" : $(SOURCE) $(DEP_CPP_CONTA) "$(INTDIR)"


!ELSEIF  "$(CFG)" == "HtmlEx - Win32 Debug"

DEP_CPP_CONTA=\
	"..\..\..\python1.4\Src\Include\accessobject.h"\
	"..\..\..\python1.4\Src\Include\bltinmodule.h"\
	"..\..\..\python1.4\Src\Include\ceval.h"\
	"..\..\..\python1.4\Src\Include\classobject.h"\
	"..\..\..\python1.4\Src\Include\cobject.h"\
	"..\..\..\python1.4\Src\Include\complexobject.h"\
	"..\..\..\python1.4\Src\Include\config.h"\
	"..\..\..\python1.4\Src\Include\fileobject.h"\
	"..\..\..\python1.4\Src\Include\floatobject.h"\
	"..\..\..\python1.4\Src\Include\funcobject.h"\
	"..\..\..\python1.4\Src\Include\import.h"\
	"..\..\..\python1.4\Src\Include\intobject.h"\
	"..\..\..\python1.4\Src\Include\intrcheck.h"\
	"..\..\..\python1.4\Src\Include\listobject.h"\
	"..\..\..\python1.4\Src\Include\longobject.h"\
	"..\..\..\python1.4\Src\Include\mappingobject.h"\
	"..\..\..\python1.4\Src\Include\methodobject.h"\
	"..\..\..\python1.4\Src\Include\moduleobject.h"\
	"..\..\..\python1.4\Src\Include\mymalloc.h"\
	"..\..\..\python1.4\Src\Include\myproto.h"\
	"..\..\..\python1.4\Src\Include\object.h"\
	"..\..\..\python1.4\Src\Include\objimpl.h"\
	"..\..\..\python1.4\Src\Include\pydebug.h"\
	"..\..\..\python1.4\Src\Include\pyerrors.h"\
	"..\..\..\python1.4\Src\Include\pythonrun.h"\
	"..\..\..\python1.4\Src\Include\rangeobject.h"\
	"..\..\..\python1.4\Src\Include\rename2.h"\
	"..\..\..\python1.4\Src\Include\sliceobject.h"\
	"..\..\..\python1.4\Src\Include\stringobject.h"\
	"..\..\..\python1.4\Src\Include\sysmodule.h"\
	"..\..\..\python1.4\Src\Include\thread.h"\
	"..\..\..\python1.4\Src\Include\traceback.h"\
	"..\..\..\python1.4\Src\Include\tupleobject.h"\
	".\ContainerWnd.h"\
	".\html.h"\
	".\htmlex.h"\
	".\htmlform.h"\
	".\htmlforms.h"\
	".\StdAfx.h"\
	{$(INCLUDE)}"\abstract.h"\
	{$(INCLUDE)}"\allobjects.h"\
	{$(INCLUDE)}"\modsupport.h"\
	{$(INCLUDE)}"\win32assoc.h"\
	{$(INCLUDE)}"\win32cmd.h"\
	{$(INCLUDE)}"\Win32ui.h"\
	{$(INCLUDE)}"\win32win.h"\
	

"$(INTDIR)\ContainerWnd.obj" : $(SOURCE) $(DEP_CPP_CONTA) "$(INTDIR)"

"$(INTDIR)\ContainerWnd.sbr" : $(SOURCE) $(DEP_CPP_CONTA) "$(INTDIR)"


!ENDIF 

# End Source File
# End Target
# End Project
################################################################################
################################################################################
# Section HtmlEx : {B7FC3551-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTMLForm
# 	2:10:HeaderFile:htmlform.h
# 	2:8:ImplFile:htmlform.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC3555-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTMLForms
# 	2:10:HeaderFile:htmlforms.h
# 	2:8:ImplFile:htmlforms.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC355C-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CHTML
# 	2:10:HeaderFile:html.h
# 	2:8:ImplFile:html.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC3595-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocInput
# 	2:10:HeaderFile:docinput.h
# 	2:8:ImplFile:docinput.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {BEF6E003-A874-101A-8BBA-00AA00300CAB}
# 	2:5:Class:COleFont
# 	2:10:HeaderFile:font.h
# 	2:8:ImplFile:font.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC3590-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocHeader
# 	2:10:HeaderFile:docheader.h
# 	2:8:ImplFile:docheader.cpp
# End Section
################################################################################
################################################################################
# Section OLE Controls
# 	{B7FC355E-8CE7-11CF-9754-00AA00C00908}
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC355E-8CE7-11CF-9754-00AA00C00908}
# 	0:8:Font.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\Font.cpp
# 	0:6:HTML.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTML.h
# 	0:12:DocHeaders.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeaders.h
# 	0:6:Font.h:C:\RESEARCH\users\sol\projects\HtmlEx\Font.h
# 	0:8:HTML.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTML.cpp
# 	0:10:DocInput.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocInput.h
# 	0:13:DocHeader.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeader.cpp
# 	0:10:HTMLForm.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForm.h
# 	0:12:DocInput.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocInput.cpp
# 	0:11:DocOutput.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocOutput.h
# 	0:13:DocOutput.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocOutput.cpp
# 	0:11:HTMLForms.h:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForms.h
# 	0:11:DocHeader.h:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeader.h
# 	0:12:HTMLForm.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForm.cpp
# 	0:13:HTMLForms.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\HTMLForms.cpp
# 	0:14:DocHeaders.cpp:C:\RESEARCH\users\sol\projects\HtmlEx\DocHeaders.cpp
# 	2:21:DefaultSinkHeaderFile:html.h
# 	2:16:DefaultSinkClass:CHTML
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC3597-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocOutput
# 	2:10:HeaderFile:docoutput.h
# 	2:8:ImplFile:docoutput.cpp
# End Section
################################################################################
################################################################################
# Section HtmlEx : {B7FC3592-8CE7-11CF-9754-00AA00C00908}
# 	2:5:Class:CDocHeaders
# 	2:10:HeaderFile:docheaders.h
# 	2:8:ImplFile:docheaders.cpp
# End Section
################################################################################

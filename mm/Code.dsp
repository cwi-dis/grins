# Microsoft Developer Studio Project File - Name="Code" - Package Owner=<4>
# Microsoft Developer Studio Generated Build File, Format Version 5.00
# ** DO NOT EDIT **

# TARGTYPE "Win32 (x86) Console Application" 0x0103

CFG=Code - Win32 Debug
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "Code.mak".
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f "Code.mak" CFG="Code - Win32 Debug"
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE "Code - Win32 Release" (based on "Win32 (x86) Console Application")
!MESSAGE "Code - Win32 Debug" (based on "Win32 (x86) Console Application")
!MESSAGE 

# Begin Project
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe
RSC=rc.exe

!IF  "$(CFG)" == "Code - Win32 Release"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD CPP /nologo /W3 /GX /O2 /D "WIN32" /D "NDEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD BASE RSC /l 0x408 /d "NDEBUG"
# ADD RSC /l 0x408 /d "NDEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /machine:I386
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /machine:I386

!ELSEIF  "$(CFG)" == "Code - Win32 Debug"

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
# ADD BASE CPP /nologo /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD CPP /nologo /W3 /Gm /GX /Zi /Od /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_MBCS" /YX /FD /c
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG"
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LINK32=link.exe
# ADD BASE LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept
# ADD LINK32 kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /nologo /subsystem:console /debug /machine:I386 /pdbtype:sept

!ENDIF 

# Begin Target

# Name "Code - Win32 Release"
# Name "Code - Win32 Debug"
# Begin Group "Common"

# PROP Default_Filter ""
# Begin Group "motif"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\common\motif\PlayerDialog.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\common\AnchorDefs.py
# End Source File
# Begin Source File

SOURCE=.\common\ArmStates.py
# End Source File
# Begin Source File

SOURCE=.\common\Channel.py
# End Source File
# Begin Source File

SOURCE=.\common\ChannelMap.py
# End Source File
# Begin Source File

SOURCE=.\common\ChannelThread.py
# End Source File
# Begin Source File

SOURCE=.\common\CmifChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ExternalChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\GLLock.py
# End Source File
# Begin Source File

SOURCE=.\common\GraphChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\HDTL.py
# End Source File
# Begin Source File

SOURCE=.\common\HtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\HyperVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ImageChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\LabelChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\LayoutChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MACVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MidiChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MovieChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MpegChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\MPEGVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\NullChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\NullChannel.pyc
# End Source File
# Begin Source File

SOURCE=.\common\parsehtml.py
# End Source File
# Begin Source File

SOURCE=.\common\PseudoHtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\PythonChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\rtpool.py
# End Source File
# Begin Source File

SOURCE=.\common\Scheduler.py
# End Source File
# Begin Source File

SOURCE=.\common\Selecter.py
# End Source File
# Begin Source File

SOURCE=.\common\Selecter.pyc
# End Source File
# Begin Source File

SOURCE=.\common\SGIVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\ShellChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\SocketChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\SoundChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\TextChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\Timing.py
# End Source File
# Begin Source File

SOURCE=.\common\VcrChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\VideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\common\WordChannel.py
# End Source File
# End Group
# Begin Group "Editor"

# PROP Default_Filter ""
# Begin Group "motif No. 1"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\editor\motif\AnchorEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\ArcInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\AttrEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\ChannelViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\HierarchyViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\LinkEditDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\MainDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\motif\NodeInfoDialog.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\editor\AnchorEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\AnchorEditorDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\ArcInfo.py
# End Source File
# Begin Source File

SOURCE=.\editor\AttrEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\AttrEdit.pyc
# End Source File
# Begin Source File

SOURCE=.\editor\AttrEdit.pyc.old
# End Source File
# Begin Source File

SOURCE=.\editor\Attredit.pyv
# End Source File
# Begin Source File

SOURCE=.\editor\AttrEditorDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\ChannelView.py
# End Source File
# Begin Source File

SOURCE=.\editor\cmifed.py
# End Source File
# Begin Source File

SOURCE=.\editor\Gl_wiahv.py
# End Source File
# Begin Source File

SOURCE=.\editor\GL_window.py
# End Source File
# Begin Source File

SOURCE=.\editor\Help.py
# End Source File
# Begin Source File

SOURCE=.\editor\HierarchyView.py
# End Source File
# Begin Source File

SOURCE=.\editor\LevelInfoDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\LinkEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\main.py
# End Source File
# Begin Source File

SOURCE=.\editor\NodeEdit.py
# End Source File
# Begin Source File

SOURCE=.\editor\NodeInfo.py
# End Source File
# Begin Source File

SOURCE=.\editor\Player.py
# End Source File
# Begin Source File

SOURCE=.\editor\PlayerCore.py
# End Source File
# Begin Source File

SOURCE=.\editor\TopLevel.py
# End Source File
# Begin Source File

SOURCE=.\editor\ViewDialog.py
# End Source File
# Begin Source File

SOURCE=.\editor\X_window.py
# End Source File
# End Group
# Begin Group "GRiNS"

# PROP Default_Filter ""
# Begin Group "motif GRiNS"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\grins1\motif\MainDialog.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\grins1\Duration.py
# End Source File
# Begin Source File

SOURCE=.\grins1\grins.py
# End Source File
# Begin Source File

SOURCE=.\grins1\mac_window.py
# End Source File
# Begin Source File

SOURCE=.\grins1\Player.py
# End Source File
# Begin Source File

SOURCE=.\grins1\PlayerCore.py
# End Source File
# Begin Source File

SOURCE=.\grins1\TopLevel.py
# End Source File
# Begin Source File

SOURCE=.\grins1\X_window.py
# End Source File
# End Group
# Begin Group "Lib"

# PROP Default_Filter ""
# Begin Group "motif Lib"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\lib\motif\Win32_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\WIN32_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\windowinterface.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\X_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\motif\X_windowbase.py
# End Source File
# End Group
# Begin Source File

SOURCE=.\lib\Attrdefs.py
# End Source File
# Begin Source File

SOURCE=.\lib\Attrdefs.pyc
# End Source File
# Begin Source File

SOURCE=.\lib\calcwmcorr.py
# End Source File
# Begin Source File

SOURCE=.\lib\chkcmif.py
# End Source File
# Begin Source File

SOURCE=.\lib\Clipboard.py
# End Source File
# Begin Source File

SOURCE=.\lib\cmif.py
# End Source File
# Begin Source File

SOURCE=.\lib\cmif.pyc
# End Source File
# Begin Source File

SOURCE=.\lib\ColorSelector.py
# End Source File
# Begin Source File

SOURCE=.\lib\dummy_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\Duration.py
# End Source File
# Begin Source File

SOURCE=.\lib\EditMgr.py
# End Source File
# Begin Source File

SOURCE=.\lib\fastimp.py
# End Source File
# Begin Source File

SOURCE=.\lib\FileCache.py
# End Source File
# Begin Source File

SOURCE=.\lib\FontStuff.py
# End Source File
# Begin Source File

SOURCE=.\lib\GL_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\GL_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\glwindow.py
# End Source File
# Begin Source File

SOURCE=.\lib\Hlinks.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\mac_windowbase.py
# End Source File
# Begin Source File

SOURCE=.\lib\MACVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\MainDialogRC.py
# End Source File
# Begin Source File

SOURCE=.\lib\MenuMaker.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMAttrdefs.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMCache.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMExc.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMNode.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMNodeBase.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMParser.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMPlayerTree.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMRead.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMStat.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMTree.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMTypes.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMurl.py
# End Source File
# Begin Source File

SOURCE=.\lib\MMWrite.py
# End Source File
# Begin Source File

SOURCE=.\lib\MovieDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\MpegDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\MPEGVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\multchoice.py
# End Source File
# Begin Source File

SOURCE=.\lib\NTVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\settings.py
# End Source File
# Begin Source File

SOURCE=.\lib\SGIVideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\Sizes.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMIL.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTree.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTreeRead.py
# End Source File
# Begin Source File

SOURCE=.\lib\SMILTreeWrite.py
# End Source File
# Begin Source File

SOURCE=.\lib\smpte.py
# End Source File
# Begin Source File

SOURCE=.\lib\SoundDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\SR.py
# End Source File
# Begin Source File

SOURCE=".\lib\StringStuff-scroll.py"
# End Source File
# Begin Source File

SOURCE=.\lib\StringStuff.py
# End Source File
# Begin Source File

SOURCE=.\lib\trace.py
# End Source File
# Begin Source File

SOURCE=.\lib\VideoDuration.py
# End Source File
# Begin Source File

SOURCE=.\lib\watchcursor.py
# End Source File
# Begin Source File

SOURCE=.\lib\WMEVENTS.py
# End Source File
# Begin Source File

SOURCE=.\lib\X_WINDO.PY
# End Source File
# Begin Source File

SOURCE=.\lib\X_window.py
# End Source File
# Begin Source File

SOURCE=.\lib\X_windowbase.py
# End Source File
# End Group
# Begin Group "Win32"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\win32\CloseDialogRC.py
# End Source File
# Begin Source File

SOURCE=.\win32\HtmlChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\ImageChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\LabelChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\LayoutChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\MpegChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\NTVideoChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\PythonChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\ShellChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\SoundChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\TextChannel.py
# End Source File
# Begin Source File

SOURCE=.\win32\WordChannel.py
# End Source File
# End Group
# Begin Group "Scripts"

# PROP Default_Filter ""
# Begin Source File

SOURCE=.\Scripts\exec_cmif.py
# End Source File
# Begin Source File

SOURCE=.\Scripts\exec_ed.py
# End Source File
# End Group
# End Target
# End Project

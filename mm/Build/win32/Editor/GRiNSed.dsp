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

!ELSEIF  "$(CFG)" == "GRiNSed - Win32 Debug"

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
# ADD BASE CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /YX /FD /GZ /c
# ADD CPP /nologo /W3 /Gm /GX /ZI /Od /D "WIN32" /D "_DEBUG" /D "_WINDOWS" /D "_MBCS" /D "BUILD_FREEZE" /YX /FD /GZ /c
# ADD BASE MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD MTL /nologo /D "_DEBUG" /mktyplib203 /win32
# ADD BASE RSC /l 0x408 /d "_DEBUG"
# ADD RSC /l 0x408 /d "_DEBUG"
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
# Begin Source File

SOURCE=.\frozen.c
# End Source File
# Begin Source File

SOURCE=.\frozen_extensions.c
# End Source File
# Begin Source File

SOURCE=.\M___main__.c
# End Source File
# Begin Source File

SOURCE=.\M__CmifView.c
# End Source File
# Begin Source File

SOURCE=.\M__LayoutView.c
# End Source File
# Begin Source File

SOURCE=.\M__LinkView.c
# End Source File
# Begin Source File

SOURCE=.\M__PreferencesDialog.c
# End Source File
# Begin Source File

SOURCE=.\M__SourceView.c
# End Source File
# Begin Source File

SOURCE=.\M_adornpref.c
# End Source File
# Begin Source File

SOURCE=.\M_afxexttb.c
# End Source File
# Begin Source File

SOURCE=.\M_afxres.c
# End Source File
# Begin Source File

SOURCE=.\M_AnchorDefs.c
# End Source File
# Begin Source File

SOURCE=.\M_AnchorEdit.c
# End Source File
# Begin Source File

SOURCE=.\M_AnchorEditDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_AnchorEditForm.c
# End Source File
# Begin Source File

SOURCE=.\M_appcon.c
# End Source File
# Begin Source File

SOURCE=.\M_AppGlobals.c
# End Source File
# Begin Source File

SOURCE=.\M_AppToplevel.c
# End Source File
# Begin Source File

SOURCE=.\M_ArcInfo.c
# End Source File
# Begin Source File

SOURCE=.\M_ArcInfoDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_ArcInfoForm.c
# End Source File
# Begin Source File

SOURCE=.\M_ArmStates.c
# End Source File
# Begin Source File

SOURCE=.\M_Attrdefs.c
# End Source File
# Begin Source File

SOURCE=.\M_AttrEdit.c
# End Source File
# Begin Source File

SOURCE=.\M_AttrEditDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_AttrEditForm.c
# End Source File
# Begin Source File

SOURCE=.\M_audio.c
# End Source File
# Begin Source File

SOURCE=.\M_audioaifc.c
# End Source File
# Begin Source File

SOURCE=.\M_audioau.c
# End Source File
# Begin Source File

SOURCE=.\M_audioconvert.c
# End Source File
# Begin Source File

SOURCE=.\M_audiofile.c
# End Source File
# Begin Source File

SOURCE=.\M_audioformat.c
# End Source File
# Begin Source File

SOURCE=.\M_audiowav.c
# End Source File
# Begin Source File

SOURCE=.\M_audiowhat.c
# End Source File
# Begin Source File

SOURCE=.\M_base64.c
# End Source File
# Begin Source File

SOURCE=.\M_bdb.c
# End Source File
# Begin Source File

SOURCE=.\M_bisect.c
# End Source File
# Begin Source File

SOURCE=.\M_Channel.c
# End Source File
# Begin Source File

SOURCE=.\M_ChannelMap.c
# End Source File
# Begin Source File

SOURCE=.\M_ChannelView.c
# End Source File
# Begin Source File

SOURCE=.\M_ChannelViewDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_Clipboard.c
# End Source File
# Begin Source File

SOURCE=.\M_cmd.c
# End Source File
# Begin Source File

SOURCE=.\M_cmif.c
# End Source File
# Begin Source File

SOURCE=.\M_CmifChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_cmifed.c
# End Source File
# Begin Source File

SOURCE=.\M_cmifwnd.c
# End Source File
# Begin Source File

SOURCE=.\M_commctrl.c
# End Source File
# Begin Source File

SOURCE=.\M_components.c
# End Source File
# Begin Source File

SOURCE=.\M_copy.c
# End Source File
# Begin Source File

SOURCE=.\M_DisplayList.c
# End Source File
# Begin Source File

SOURCE=.\M_DrawTk.c
# End Source File
# Begin Source File

SOURCE=.\M_Duration.c
# End Source File
# Begin Source File

SOURCE=.\M_EditMgr.c
# End Source File
# Begin Source File

SOURCE=.\M_exceptions.c
# End Source File
# Begin Source File

SOURCE=.\M_exec_cmif.c
# End Source File
# Begin Source File

SOURCE=.\M_FileCache.c
# End Source File
# Begin Source File

SOURCE=.\M_Font.c
# End Source File
# Begin Source File

SOURCE=.\M_FormServer.c
# End Source File
# Begin Source File

SOURCE=.\M_ftplib.c
# End Source File
# Begin Source File

SOURCE=.\M_GenWnd.c
# End Source File
# Begin Source File

SOURCE=.\M_getopt.c
# End Source File
# Begin Source File

SOURCE=.\M_getpass.c
# End Source File
# Begin Source File

SOURCE=.\M_GLLock.c
# End Source File
# Begin Source File

SOURCE=.\M_gopherlib.c
# End Source File
# Begin Source File

SOURCE=.\M_GraphChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_grins_app_core.c
# End Source File
# Begin Source File

SOURCE=.\M_grinsRC.c
# End Source File
# Begin Source File

SOURCE=.\M_HDTL.c
# End Source File
# Begin Source File

SOURCE=.\M_Help.c
# End Source File
# Begin Source File

SOURCE=.\M_HierarchyView.c
# End Source File
# Begin Source File

SOURCE=.\M_HierarchyViewDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_Hlinks.c
# End Source File
# Begin Source File

SOURCE=.\M_HtmlChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_httplib.c
# End Source File
# Begin Source File

SOURCE=.\M_ImageChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_LabelChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_LayoutChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_LayoutView.c
# End Source File
# Begin Source File

SOURCE=.\M_LayoutViewDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_license.c
# End Source File
# Begin Source File

SOURCE=.\M_linecache.c
# End Source File
# Begin Source File

SOURCE=.\M_LinkEdit.c
# End Source File
# Begin Source File

SOURCE=.\M_LinkEditDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_macurl2path.c
# End Source File
# Begin Source File

SOURCE=.\M_MainDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_MainFrame.c
# End Source File
# Begin Source File

SOURCE=.\M_MenuTemplate.c
# End Source File
# Begin Source File

SOURCE=.\M_mimetools.c
# End Source File
# Begin Source File

SOURCE=.\M_mimetypes.c
# End Source File
# Begin Source File

SOURCE=.\M_MMAttrdefs.c
# End Source File
# Begin Source File

SOURCE=.\M_MMCache.c
# End Source File
# Begin Source File

SOURCE=.\M_MMExc.c
# End Source File
# Begin Source File

SOURCE=.\M_MMNode.c
# End Source File
# Begin Source File

SOURCE=.\M_MMParser.c
# End Source File
# Begin Source File

SOURCE=.\M_MMRead.c
# End Source File
# Begin Source File

SOURCE=.\M_mmsystem.c
# End Source File
# Begin Source File

SOURCE=.\M_MMTree.c
# End Source File
# Begin Source File

SOURCE=.\M_MMTypes.c
# End Source File
# Begin Source File

SOURCE=.\M_MMurl.c
# End Source File
# Begin Source File

SOURCE=.\M_MMWrite.c
# End Source File
# Begin Source File

SOURCE=.\M_MPEGVideoDuration.c
# End Source File
# Begin Source File

SOURCE=.\M_NodeEdit.c
# End Source File
# Begin Source File

SOURCE=.\M_NodeInfo.c
# End Source File
# Begin Source File

SOURCE=.\M_NodeInfoDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_NodeInfoForm.c
# End Source File
# Begin Source File

SOURCE=.\M_ntpath.c
# End Source File
# Begin Source File

SOURCE=.\M_nturl2path.c
# End Source File
# Begin Source File

SOURCE=.\M_NTVideoChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_NTVideoDuration.c
# End Source File
# Begin Source File

SOURCE=.\M_NullChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_os.c
# End Source File
# Begin Source File

SOURCE=.\M_patchlevel.c
# End Source File
# Begin Source File

SOURCE=.\M_pdb.c
# End Source File
# Begin Source File

SOURCE=.\M_Player.c
# End Source File
# Begin Source File

SOURCE=.\M_PlayerCore.c
# End Source File
# Begin Source File

SOURCE=.\M_PlayerDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_posixpath.c
# End Source File
# Begin Source File

SOURCE=.\M_pprint.c
# End Source File
# Begin Source File

SOURCE=.\M_Preferences.c
# End Source File
# Begin Source File

SOURCE=.\M_PreferencesDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_PseudoHtmlChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_PythonChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__dialogs.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__dialogs__list.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__app.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__cmdline.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__help.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__interact.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__intpyapp.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__scriptutils.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__toolmenu.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__framework__winout.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__afxres.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__dialog.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__docview.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__object.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__thread.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__mfc__window.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__tools.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__tools__browser.c
# End Source File
# Begin Source File

SOURCE=.\M_pywin__tools__hierlist.c
# End Source File
# Begin Source File

SOURCE=.\M_Queue.c
# End Source File
# Begin Source File

SOURCE=.\M_quopri.c
# End Source File
# Begin Source File

SOURCE=.\M_random.c
# End Source File
# Begin Source File

SOURCE=.\M_rbtk.c
# End Source File
# Begin Source File

SOURCE=.\M_re.c
# End Source File
# Begin Source File

SOURCE=.\M_regsub.c
# End Source File
# Begin Source File

SOURCE=.\M_regutil.c
# End Source File
# Begin Source File

SOURCE=.\M_repr.c
# End Source File
# Begin Source File

SOURCE=.\M_rfc822.c
# End Source File
# Begin Source File

SOURCE=.\M_sched.c
# End Source File
# Begin Source File

SOURCE=.\M_Scheduler.c
# End Source File
# Begin Source File

SOURCE=.\M_Selecter.c
# End Source File
# Begin Source File

SOURCE=.\M_settings.c
# End Source File
# Begin Source File

SOURCE=.\M_site.c
# End Source File
# Begin Source File

SOURCE=.\M_Sizes.c
# End Source File
# Begin Source File

SOURCE=.\M_SMIL.c
# End Source File
# Begin Source File

SOURCE=.\M_SMILTreeRead.c
# End Source File
# Begin Source File

SOURCE=.\M_SMILTreeWrite.c
# End Source File
# Begin Source File

SOURCE=.\M_smpte.c
# End Source File
# Begin Source File

SOURCE=.\M_socket.c
# End Source File
# Begin Source File

SOURCE=.\M_SocketChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_SoundChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_SoundDuration.c
# End Source File
# Begin Source File

SOURCE=.\M_SR.c
# End Source File
# Begin Source File

SOURCE=.\M_stat.c
# End Source File
# Begin Source File

SOURCE=.\M_staticlicense.c
# End Source File
# Begin Source File

SOURCE=.\M_string.c
# End Source File
# Begin Source File

SOURCE=.\M_StringIO.c
# End Source File
# Begin Source File

SOURCE=.\M_StringStuff.c
# End Source File
# Begin Source File

SOURCE=.\M_sysmetrics.c
# End Source File
# Begin Source File

SOURCE=.\M_tempfile.c
# End Source File
# Begin Source File

SOURCE=.\M_TextChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_Timing.c
# End Source File
# Begin Source File

SOURCE=.\M_token.c
# End Source File
# Begin Source File

SOURCE=.\M_tokenize.c
# End Source File
# Begin Source File

SOURCE=.\M_TopLevel.c
# End Source File
# Begin Source File

SOURCE=.\M_TopLevelDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_trace.c
# End Source File
# Begin Source File

SOURCE=.\M_traceback.c
# End Source File
# Begin Source File

SOURCE=.\M_types.c
# End Source File
# Begin Source File

SOURCE=.\M_urllib.c
# End Source File
# Begin Source File

SOURCE=.\M_urlparse.c
# End Source File
# Begin Source File

SOURCE=.\M_usercmd.c
# End Source File
# Begin Source File

SOURCE=.\M_usercmdui.c
# End Source File
# Begin Source File

SOURCE=.\M_UserDict.c
# End Source File
# Begin Source File

SOURCE=.\M_uu.c
# End Source File
# Begin Source File

SOURCE=.\M_version.c
# End Source File
# Begin Source File

SOURCE=.\M_VideoChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_VideoDuration.c
# End Source File
# Begin Source File

SOURCE=.\M_ViewDialog.c
# End Source File
# Begin Source File

SOURCE=.\M_ViewServer.c
# End Source File
# Begin Source File

SOURCE=.\M_wc.c
# End Source File
# Begin Source File

SOURCE=.\M_whrandom.c
# End Source File
# Begin Source File

SOURCE=.\M_win32con.c
# End Source File
# Begin Source File

SOURCE=.\M_win32menu.c
# End Source File
# Begin Source File

SOURCE=.\M_win32modules.c
# End Source File
# Begin Source File

SOURCE=.\M_win32mu.c
# End Source File
# Begin Source File

SOURCE=.\M_win32traceutil.c
# End Source File
# Begin Source File

SOURCE=.\M_windowinterface.c
# End Source File
# Begin Source File

SOURCE=.\M_winerror.c
# End Source File
# Begin Source File

SOURCE=.\M_WMEVENTS.c
# End Source File
# Begin Source File

SOURCE=.\M_wndusercmd.c
# End Source File
# Begin Source File

SOURCE=.\M_WordChannel.c
# End Source File
# Begin Source File

SOURCE=.\M_xmllib.c
# End Source File
# End Group
# Begin Group "Resource Files"

# PROP Default_Filter "ico;cur;bmp;dlg;rc2;rct;bin;rgs;gif;jpg;jpeg;jpe"
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

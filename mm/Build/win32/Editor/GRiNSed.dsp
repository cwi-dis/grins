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
# Begin Source File

SOURCE=..\GRiNS\frozen.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\frozen_extensions.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M___main__.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__CmifView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__LayoutView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__LinkView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__PreferencesDialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__SourceView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M__UsergroupView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_afxexttb.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_afxres.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_AnchorDefs.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_AnchorEditForm.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_appcon.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_AppToplevel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ArcInfoForm.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ArmStates.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ASXParser.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Attrdefs.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_AttrEditForm.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Attrgrs.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__aifc.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__au.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__convert.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__file.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__format.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__wav.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_audio__what.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_base64.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_bdb.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_bisect.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Channel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ChannelMap.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_chunk.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_cmd.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_cmif.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_CmifChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_cmifwnd.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_colors.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_commctrl.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_components.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_copy.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_DisplayList.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_DrawTk.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_DropTarget.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Duration.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_exceptions.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_exec_cmif.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_FileCache.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_flags.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Font.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_FormServer.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ftplib.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_GenFormView.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_GenWnd.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_getopt.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_getpass.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_GLLock.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_gopherlib.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_GraphChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_grins.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_grins_app_core.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_grins_mimetypes.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_grinsRC.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_HDTL.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Help.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Hlinks.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_HtmlChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_httplib.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ImageChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_keyword.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_LabelChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_LayoutChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_linecache.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_longpath.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_macurl2path.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MainDialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MainFrame.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MediaChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MenuTemplate.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MidiChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_mimetools.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_mimetypes.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMAttrdefs.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMCache.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMExc.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMNode.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMParser.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMRead.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMTypes.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMurl.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MMWrite.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_MPEGVideoDuration.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_NodeInfoForm.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ntpath.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_nturl2path.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_NTVideoChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_NTVideoDuration.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_NullChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_os.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_patchlevel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pdb.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Player.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_PlayerCore.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_PlayerDialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_posixpath.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pprint.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Preferences.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_PreferencesDialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_PseudoHtmlChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_PythonChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__debugger.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__debugger__dbgcon.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__debugger__dbgpyapp.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__debugger__debugger.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__debugger__DebuggerResourcesCon.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__dialogs.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__dialogs__ideoptions.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__dialogs__list.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__app.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__cmdline.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__color.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__color__coloreditor.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__color__scintillacon.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__configui.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__document.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__editor__template.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__help.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__interact.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__intpyapp.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__intpydde.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__scriptutils.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__toolmenu.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__framework__winout.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__afxres.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__dialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__docview.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__object.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__thread.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__mfc__window.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__tools.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__tools__browser.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_pywin__tools__hierlist.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Queue.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_quopri.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_random.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_rbtk.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_re.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealAudioChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealPixChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_realsupport.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealTextChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealVideoChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_RealWindowChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_regsub.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_regutil.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_repr.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_rfc822.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_sched.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Scheduler.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Selecter.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_settings.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_site.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Sizes.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SMIL.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SMILTreeRead.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SMILTreeWrite.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_smpte.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_socket.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SocketChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SoundChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SoundDuration.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_splash.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_SR.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_stat.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_string.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_StringIO.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_StringStuff.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_sysmetrics.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_tempfile.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_TextChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_Timing.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_token.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_tokenize.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_TopLevel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_TopLevelDialog.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_trace.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_traceback.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_types.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_urlcache.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_urllib.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_urlparse.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_usercmd.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_usercmdui.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_UserDict.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_uu.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_version.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_VideoChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_VideoDuration.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_ViewServer.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_wc.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_whrandom.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_win32con.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_win32ig.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_win32menu.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_win32mu.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_win32traceutil.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_windowinterface.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_winerror.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_WMEVENTS.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_wndusercmd.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_WordChannel.c
# End Source File
# Begin Source File

SOURCE=..\GRiNS\M_xmllib.c
# End Source File
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

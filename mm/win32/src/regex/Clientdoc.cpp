// clientDoc.cpp : implementation of the CClientDoc class
//

#include "stdafx.h"
#include "client.h"

#include "clientDoc.h"
#include "Clientsocket.h"
#include "ConDialog.h"
#include "DisconDialog.h"
#include "SendDlg.h"
#include "DisjoinDialog.h"
#include "JoinDialog.h"
#include "msg.h"
#include "ListClientView.h"
#include "ChatSendView.h"
#include "ChatRecvView.h"
#include "capture.h"
#include "ProgressDlg.h"
#include "Video.h"
#include "Settings.h"
#include "AudioIn.h"
#include "AudioOut.h"

#include "FileTrans.h"
#include "FileRecv.h"
#include "ClipTrans.h"
#include "ClipRecv.h"
#include "ClipWnd.h"

#include "drawobj.h"
#include "DrWnd.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#undef THIS_FILE
static char THIS_FILE[] = __FILE__;
#endif

///////////////////////////
// Globals
CEvent	g_Kill;
CEvent	g_KillAck;
HWND	g_ListHwnd, g_RecvHwnd;
int g_frames, g_framessent, g_framesplayed;

/////////////////////////////////////////////////////////////////////////////
// CClientDoc

IMPLEMENT_DYNCREATE(CClientDoc, CDocument)

BEGIN_MESSAGE_MAP(CClientDoc, CDocument)
	//{{AFX_MSG_MAP(CClientDoc)
	ON_COMMAND(ID_NETWORK_CONNECT, OnNetworkConnect)
	ON_COMMAND(ID_NETWORK_DISCONNECT, OnNetworkDisconnect)
	ON_UPDATE_COMMAND_UI(ID_NETWORK_CONNECT, OnUpdateNetworkConnect)
	ON_UPDATE_COMMAND_UI(ID_NETWORK_DISCONNECT, OnUpdateNetworkDisconnect)
	ON_COMMAND(ID_NETWORK_SENDPACKET, OnNetworkSendpacket)
	ON_UPDATE_COMMAND_UI(ID_NETWORK_SENDPACKET, OnUpdateNetworkSendpacket)
	ON_COMMAND(ID_GROUPS_DISJOIN, OnGroupsDisjoin)
	ON_UPDATE_COMMAND_UI(ID_GROUPS_DISJOIN, OnUpdateGroupsDisjoin)
	ON_COMMAND(ID_GROUPS_GET, OnGroupsGet)
	ON_COMMAND(ID_GROUPS_JOIN, OnGroupsJoin)
	ON_UPDATE_COMMAND_UI(ID_GROUPS_GET, OnUpdateGroupsGet)
	ON_UPDATE_COMMAND_UI(ID_GROUPS_JOIN, OnUpdateGroupsJoin)
	ON_COMMAND(ID_VIDEO_INFO, OnVideoInfo)
	ON_COMMAND(ID_VIDEO_CAPTUREAS_AVI, OnVideoCaptureasAvi)
	ON_COMMAND(ID_VIDEO_CAPTUREAS_DIB, OnVideoCaptureasDib)
	ON_COMMAND(ID_VIDEO_CAPTUREAS_WAV, OnVideoCaptureasWav)
	ON_COMMAND(ID_VIDEO_CLOSE, OnVideoClose)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_CLOSE, OnUpdateVideoClose)
	ON_COMMAND(ID_VIDEO_OPEN, OnVideoOpen)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_OPEN, OnUpdateVideoOpen)
	ON_COMMAND(ID_VIDEO_SETCAPTUREPARAMETERS, OnVideoSetcaptureparameters)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_SETCAPTUREPARAMETERS, OnUpdateVideoSetcaptureparameters)
	ON_COMMAND(ID_VIDEO_VIDEODISPLAY, OnVideoVideodisplay)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_VIDEODISPLAY, OnUpdateVideoVideodisplay)
	ON_COMMAND(ID_VIDEO_VIDEOFORMAT, OnVideoVideoformat)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_VIDEOFORMAT, OnUpdateVideoVideoformat)
	ON_COMMAND(ID_VIDEO_VIDEOSOURCE, OnVideoVideosource)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_VIDEOSOURCE, OnUpdateVideoVideosource)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_CAPTUREAS_AVI, OnUpdateVideoCaptureasAvi)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_CAPTUREAS_DIB, OnUpdateVideoCaptureasDib)
	ON_UPDATE_COMMAND_UI(ID_VIDEO_CAPTUREAS_WAV, OnUpdateVideoCaptureasWav)
	ON_COMMAND(ID_USER_SENDVIDEO, OnUserSendvideo)
	ON_UPDATE_COMMAND_UI(ID_USER_SENDVIDEO, OnUpdateUserSendvideo)
	ON_COMMAND(ID_NETWORK_SETTINGS, OnNetworkSettings)
	ON_COMMAND(ID_VIDEO_PLAY_AVI, OnVideoPlayAvi)
	ON_COMMAND(ID_VIDEO_PLAY_WAV, OnVideoPlayWav)
	ON_COMMAND(ID_AUDIO_ENABLEAUDIO, OnAudioEnableaudio)
	ON_UPDATE_COMMAND_UI(ID_AUDIO_ENABLEAUDIO, OnUpdateAudioEnableaudio)
	ON_COMMAND(ID_AUDIO_SETAUDIOPARAMETERS, OnAudioSetaudioparameters)
	ON_COMMAND(ID_AUDIO_ENABLEPLAYBACK, OnAudioEnableplayback)
	ON_UPDATE_COMMAND_UI(ID_AUDIO_ENABLEPLAYBACK, OnUpdateAudioEnableplayback)
	ON_COMMAND(ID_NETWORK_COMPRESSIONINFO, OnNetworkCompressioninfo)
	ON_COMMAND(ID_VIEW_WHITEBOARD, OnViewWhiteboard)
	ON_UPDATE_COMMAND_UI(ID_VIEW_WHITEBOARD, OnUpdateViewWhiteboard)
	//}}AFX_MSG_MAP
END_MESSAGE_MAP()

/////////////////////////////////////////////////////////////////////////////
// CClientDoc construction/destruction

CClientDoc::CClientDoc()
{
	int i;
	// Pointers - globals
	g_frames = g_framesrecv = g_framessent = g_framesplayed = 0;
	g_pDoc = this;
	m_pSocket = NULL;
	m_pProcMsgThread = NULL;
	m_pListView = NULL;
	m_pChatSendView = NULL;
	m_pChatRecvView = NULL;
	// State Variables
	m_bTryConnect = FALSE;
	m_bconnected = FALSE;
	m_bjoined = FALSE;
	// Identity
	m_id = 0;
	m_strusr.Empty();
	m_strpassw.Empty();
	m_strgroup.Empty();
	// User & Group Lists
	m_nlength1=0;		m_nlength2=0;
	m_bnewlist=FALSE;	m_bnewgrlist=FALSE;
	m_nDBLen = 0;		m_buserDB = FALSE;
	// Chat Data
	m_strchat.Empty();
	// File Transfer Data
	m_fileidcount = 0;		m_recvfilecount = 0;
	for (i = 0; i < MAX_FILES; i++) {
		 Trans[i] = NULL;	 Recv[i] = NULL;
	}
	// ClipBoard Transfer Data
	ClipTrans = NULL;
	for (i = 0; i < MAX_FILES; i++) {
		 ClipRecv[i] = NULL;
	}
	
	for (i = 0; i < MAX_FILES; i++) {
		 ClipWnd[i] = NULL;
	}
	PointerClip = NULL;
	PointerWnd = NULL;

	// Video Data
	icmgr = new CICMgr;
	m_videoList = new CVideo;
	m_videoList->m_bFirstVideo = FALSE;
	m_bVideoOpen = FALSE;

	// Audio Data
	m_bAudio = FALSE;
	m_bAudioPlay = FALSE;
	m_pAudioIn = new CAudioIn(this); 
	m_pAudioOut = new CAudioOut(this);
	m_TimeMark = m_MarkArrived = 0;

	InitializeCriticalSection(&m_csusr);
	InitializeCriticalSection(&m_csgr);
	InitializeCriticalSection(&m_csdr);

	m_bEnd = FALSE;

	// Whiteboard info
	m_nMapMode = MM_ANISOTROPIC;
	m_pDrWnd = NULL;	
}

CClientDoc::~CClientDoc()
{
	BYTE i;
	for (i = 0; i < MAX_FILES; i++) {
		 if (ClipWnd[i] != NULL)
			 ClipWnd[i]->DestroyWindow();
	}
	if (PointerWnd != NULL)
		PointerWnd->DestroyWindow();
	delete m_videoList;
	delete icmgr;
	delete m_pAudioIn;
	delete m_pAudioOut;
	DeleteCriticalSection(&m_csusr);
	DeleteCriticalSection(&m_csgr);
	DeleteCriticalSection(&m_csdr);
}

void CClientDoc::DeleteContents()
{
	TRACE("DeleteContents\n");
	// If thread is running
	if (m_bconnected || m_bTryConnect) {			
		g_Kill.SetEvent();		// Kill thread
		WaitForSingleObject(g_KillAck.m_hObject, INFINITE);
								// Wait for Ack so as to delete socket
		m_bconnected = FALSE;		
	}
	// Delete Lists (Group Users - Groups - User DB)
	DumpOldUsrlist();
	DestroyOldGroupList();
	DestroyUserDB();
	
	// Empty contents of INI file
	CString IniPath; char WinDir[MAX_PATH];
	if (m_bEnd) {		// if program exits
		GetWindowsDirectory(WinDir, MAX_PATH);
		IniPath.GetBuffer(MAX_PATH);
		IniPath.Format("%s", WinDir);
		IniPath += "\\Client.ini";
		TRACE("Path = %s\n", IniPath);
		FILE* fp;
		if (fp = fopen((LPCTSTR) IniPath, "wt"))
			fclose(fp);
		// Destroy server list and write to INI file
		DestroyServerList();
		// Write settings to IN file
		DestroySettings();
	}
	
	// Destroy whiteboard elements
	if (m_objects.GetCount() > 0 ) {
		POSITION pos = m_objects.GetHeadPosition();
		while (pos != NULL)
			delete m_objects.GetNext(pos);
	}
	if (m_pDrWnd != NULL){
		if (m_pDrWnd->GetSafeHwnd() != NULL)
			m_pDrWnd->DestroyWindow();
		m_pDrWnd = NULL;
	}

	// Destroy Socket
	if (m_pSocket != NULL)	{
		delete m_pSocket;
		m_pSocket = NULL;
	}

	m_strusr.Empty(); m_strpassw.Empty(); m_strchat.Empty();

	if (!m_bEnd)		// if first time called, make m_bEnd = TRUE,
		m_bEnd = TRUE;	// next time program exits
	CDocument::DeleteContents();
}



//////////////////////////////////////////////////////////////////////
// DestroySettings()
//////////////////////////////////////////////////////////////////////
// Saves the latest settings when user destroys document by writing them
// in an .INI file. This function is called by DeleteContents()
//////////////////////////////////////////////////////////////////////  
void CClientDoc::DestroySettings()
{	
	// Save various settings
	AfxGetApp()->WriteProfileInt("Packets", "File", m_FilePack);
	AfxGetApp()->WriteProfileInt("Packets", "Clip", m_ClipPack);
	AfxGetApp()->WriteProfileInt("Threads", "Proc", m_priorProcThread);
	AfxGetApp()->WriteProfileInt("Threads", "File", m_priorFileThread);
	AfxGetApp()->WriteProfileInt("Threads", "Clip", m_priorClipThread);
	AfxGetApp()->WriteProfileInt("Confirms", "File", m_bFileRecv);
	AfxGetApp()->WriteProfileInt("Confirms", "DisConf", m_bDisConf);
	AfxGetApp()->WriteProfileInt("Confirms", "Pack", m_bPackRecv);
	AfxGetApp()->WriteProfileInt("Confirms", "Join/Disjoin Messages", m_bJoinMsg);
	AfxGetApp()->WriteProfileInt("Pointer", "Sens", m_nPointer);
	AfxGetApp()->WriteProfileInt("Compress", "Comp", m_bCompress);
	// Save Chat Text Format
	// Get Chat Text Format
	m_cf.cbSize = sizeof(CHARFORMAT);
	m_cf.dwMask = CFM_BOLD | CFM_COLOR | CFM_FACE | CFM_ITALIC | CFM_SIZE |
				  CFM_UNDERLINE | CFM_STRIKEOUT | CFM_CHARSET;
	CString strEffect; CString strColor;
	strEffect.Format("%d", m_cf.dwEffects);
	AfxGetApp()->WriteProfileString("Chat Text", "Effects", strEffect);
	AfxGetApp()->WriteProfileInt("Chat Text", "Height", m_cf.yHeight);
	AfxGetApp()->WriteProfileInt("Chat Text", "Offset", m_cf.yOffset);
	strColor.Format("%d", m_cf.crTextColor);
	AfxGetApp()->WriteProfileString("Chat Text", "Color", strColor);
	AfxGetApp()->WriteProfileInt("Chat Text", "Char Set", m_cf.bCharSet);
	AfxGetApp()->WriteProfileInt("Chat Text", "Pitch & Family", m_cf.bPitchAndFamily);
	AfxGetApp()->WriteProfileString("Chat Text", "Font", m_cf.szFaceName);
	// Save Layout Parameters
	AfxGetApp()->WriteProfileString("Layout", "Position", m_strLayout);
	AfxGetApp()->WriteProfileInt("Layout", "Iconized", m_bIconic);
	AfxGetApp()->WriteProfileInt("Layout", "Maximized", m_bMaximized);
	// Save Splitter Parameters
	AfxGetApp()->WriteProfileInt("Splitter", "s1r0", m_split1r0);
	AfxGetApp()->WriteProfileInt("Splitter", "s1c0", m_split1c0);
	AfxGetApp()->WriteProfileInt("Splitter", "s1c1", m_split1c1);
	AfxGetApp()->WriteProfileInt("Splitter", "s2r0", m_split2r0);
	AfxGetApp()->WriteProfileInt("Splitter", "s2r1", m_split2r1);
	AfxGetApp()->WriteProfileInt("Splitter", "s2c0", m_split2c0);
}


BOOL CClientDoc::OnNewDocument()
{
	if (!CDocument::OnNewDocument())
		return FALSE;

	// Read from INI file
	InitSettings();
	InitializeServerList();

	return TRUE;
}

///////////////////////////////////////////////////////////////////////////
// InitSettings()
///////////////////////////////////////////////////////////////////////////
// Initialises Settings that determine a user's profile, by reading them
// from the proper .INI file. This function is called by OnNewDocument()
/////////////////////////////////////////////////////////////////////////// 
void CClientDoc::InitSettings()
{
	// Get various settings
	m_FilePack = AfxGetApp()->GetProfileInt("Packets", "File", 32768);
	m_ClipPack = AfxGetApp()->GetProfileInt("Packets", "Clip", 32768);
	m_priorProcThread = AfxGetApp()->GetProfileInt("Threads", "Proc", THREAD_PRIORITY_NORMAL);
	m_priorFileThread = AfxGetApp()->GetProfileInt("Threads", "File", THREAD_PRIORITY_NORMAL);
	m_priorClipThread = AfxGetApp()->GetProfileInt("Threads", "Clip", THREAD_PRIORITY_NORMAL);
	m_bFileRecv = AfxGetApp()->GetProfileInt("Confirms", "File", TRUE);
	m_bDisConf = AfxGetApp()->GetProfileInt("Confirms", "DisConf", TRUE);
	m_bPackRecv = AfxGetApp()->GetProfileInt("Confirms", "Pack", TRUE);
	m_bJoinMsg = AfxGetApp()->GetProfileInt("Confirms", "Join/Disjoin Messages", TRUE);
	m_nPointer = AfxGetApp()->GetProfileInt("Pointer", "Sens", 20);
	m_bCompress = AfxGetApp()->GetProfileInt("Compress", "Comp", TRUE);
	
	// Get Chat Text Format
	m_cf.cbSize = sizeof(CHARFORMAT);
	m_cf.dwMask = CFM_BOLD | CFM_COLOR | CFM_FACE | CFM_ITALIC | CFM_SIZE |
				  CFM_UNDERLINE | CFM_STRIKEOUT | CFM_CHARSET;
	CString strEffect = AfxGetApp()->GetProfileString("Chat Text", "Effects", "1073741825");
	m_cf.dwEffects = (DWORD) atol((LPCTSTR) strEffect);
	m_cf.yHeight = AfxGetApp()->GetProfileInt("Chat Text", "Height", 195);
	m_cf.yOffset = AfxGetApp()->GetProfileInt("Chat Text", "Offset", 0);
	CString strColor = AfxGetApp()->GetProfileString("Chat Text", "Color", "0");
	m_cf.crTextColor = (COLORREF) atol((LPCTSTR) strColor);
	m_cf.bCharSet = AfxGetApp()->GetProfileInt("Chat Text", "Char Set", 0);
	m_cf.bPitchAndFamily = AfxGetApp()->GetProfileInt("Chat Text", "Pitch & Family", 34);
	strcpy(m_cf.szFaceName, 
		   (LPCTSTR) AfxGetApp()->GetProfileString("Chat Text", "Font", "System"));
	// Set Chat Text Format
	m_pChatSendView->GetRichEditCtrl().SetDefaultCharFormat(m_cf);
	m_pChatRecvView->GetRichEditCtrl().SetDefaultCharFormat(m_cf);
}


///////////////////////////////////////////////////////////////////////////
// InitializeServerList()
///////////////////////////////////////////////////////////////////////////
// Constructs a list of availiable servers (added previously by a user)
// by reading from INI file
///////////////////////////////////////////////////////////////////////////
void CClientDoc::InitializeServerList()
{
	// Read Servers from INI file
	CString Entry("Server "), Server; UINT j = 0;
	do {
		j++; Entry.SetAt(6,(char) j+48);	// "Serverj"
		Server = AfxGetApp()->GetProfileString("Servers", Entry, NULL);
		// Add to server list
		if (!Server.IsEmpty())  {
			CString* pServ = new CString(Server);
			m_serverList.AddTail(pServ);
			TRACE("Added %s to server List\n", *pServ);
		}
	} while (!Server.IsEmpty());
}


///////////////////////////////////////////////////////////////////////////
// DestroyServerList()
///////////////////////////////////////////////////////////////////////////
// Destroys the list of available  servers
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DestroyServerList()
{
	CString Entry("Server "); UINT i = 1;
	while (!m_serverList.IsEmpty()) {
		CString* pServ = (CString*) m_serverList.RemoveHead();
		Entry.SetAt(6, (char)(i+48));
		AfxGetApp()->WriteProfileString("Servers", Entry, *pServ);
		i++;
		delete pServ;
	}
}

/////////////////////////////////////////////////////////////////////////////
// CClientDoc serialization

void CClientDoc::Serialize(CArchive& ar)
{
	if (ar.IsStoring())
	{
		// TODO: add storing code here
	}
	else
	{
		// TODO: add loading code here
	}
}

/////////////////////////////////////////////////////////////////////////////
// CClientDoc diagnostics

#ifdef _DEBUG
void CClientDoc::AssertValid() const
{
	CDocument::AssertValid();
}

void CClientDoc::Dump(CDumpContext& dc) const
{
	CDocument::Dump(dc);
}
#endif //_DEBUG

/////////////////////////////////////////////////////////////////////////////
// CClientDoc commands
///////////////////////////////////////////////////////////////////////////
// NETWORK MENU Commands
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// OnNetworkConnect()
///////////////////////////////////////////////////////////////////////////
// Shows the dialog that prompts for connection, gathers the requisite 
// elements and invokes the connection process
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnNetworkConnect() 
{
	CConDialog Dialog(this, NULL);
	Dialog.m_straddr ="";
	Dialog.m_strusr  ="";
	Dialog.m_strpassw="";

	if (Dialog.DoModal()== IDOK)
	{
		m_strusr = Dialog.m_strusr;
		m_strpassw = Dialog.m_strpassw;
		m_straddr = Dialog.m_straddr;
		ConnectSocket(Dialog.m_straddr);
	}
}

///////////////////////////////////////////////////////////////////////////
// OnNetworkDisconnect()
///////////////////////////////////////////////////////////////////////////
// Disconnects user and implements tasks that are consequent to this
// disonnection 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnNetworkDisconnect() 
{
	CDisconDialog Dialog; int ret;
	if (m_bDisConf)
		ret = Dialog.DoModal();
	else
		ret = IDOK;

	if ( ret == IDOK){
		if (m_bconnected) {			// if thread is running
			g_Kill.SetEvent();		// Kill thread
			WaitForSingleObject(g_KillAck.m_hObject, INFINITE);
								// Wait for Ack so as to delete socket
			AfxGetMainWnd()->SetWindowText("Multimedia Client Application");
			m_pSocket->Close();
			delete m_pSocket;
			m_pSocket = NULL;
			m_bconnected = m_bjoined = m_bTryConnect = FALSE;
			m_strgroup.Empty(); m_strusr.Empty();
			DumpOldUsrlist();
			DestroyUserDB();
			m_nlength1=0;	m_bnewlist=FALSE;
			m_nDBLen = 0;	m_buserDB = FALSE;
		
			SetModifiedFlag(TRUE);
			UpdateAllViews(NULL);
			SetModifiedFlag(FALSE);
			AfxMessageBox(IDS_CONNECTIONCLOSED);
		}
	}

}

///////////////////////////////////////////////////////////////////////////
// OnNetworkSendpacket()
///////////////////////////////////////////////////////////////////////////
// Sends dummy packets. Used merely for network testing purposes
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnNetworkSendpacket() 
{
	LPBYTE Packet;
	
	CSendDlg Dlg;
	Dlg.m_Copies = 1;
		
	if (Dlg.DoModal() == IDOK) {
		SendMsg(0, Dlg.m_RecvID);
		for (Dlg.m_Copies > 0; Dlg.m_Copies--;) {
			Packet = (LPBYTE) MemAlloc(NULL, Dlg.m_Length + HEADER_LENGTH, 
									   MEM_COMMIT, PAGE_READWRITE);
			Packet[SEND_POS] = m_id;
			Packet[RECV_POS] = Dlg.m_RecvID;
			Packet[TYPE_POS] = 1;
			*((LPDWORD) (Packet + LEN_POS)) = Dlg.m_Length;
		
			m_pSocket->BufferOut->AddTail((LPSTR) Packet, Dlg.m_Length + HEADER_LENGTH, NO_COMP);
			MemFree(Packet, Dlg.m_Length + HEADER_LENGTH, MEM_DECOMMIT|MEM_RELEASE);
			TRACE("Packet added to BufferOut\n");
		}
	}
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnNetworkCompressioninfo()
// PUPROSE:	   Displays Compression Information
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnNetworkCompressioninfo() 
{
	if (!m_pSocket) return;
	CString str;
	LONG ratio = 100 - 100 * m_pSocket->BufferOut->m_cl / m_pSocket->BufferOut->m_ol;
	str.Format("Original Length: %d\nCompressed Length: %d\nCompression Ratio: %d%%",
				m_pSocket->BufferOut->m_ol, m_pSocket->BufferOut->m_cl, ratio);
	AfxMessageBox(str);	
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnNetworkSettings()
// PUPROSE:	   Displays dialog to set various settings and preferences 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnNetworkSettings() 
{
	CSetSheet Dlg("Settings"); UINT i;

	Dlg.m_page2.m_FilePack = m_FilePack;
	Dlg.m_page2.m_ClipPack = m_ClipPack;
	switch (m_priorProcThread) {
		case THREAD_PRIORITY_NORMAL: Dlg.m_page2.m_ProcThread = "Normal"; break;
		case THREAD_PRIORITY_BELOW_NORMAL: Dlg.m_page2.m_ProcThread = "Below Normal"; break;
		case THREAD_PRIORITY_LOWEST: Dlg.m_page2.m_ProcThread = "Lowest"; break;
	}
	switch (m_priorFileThread) {
		case THREAD_PRIORITY_NORMAL: Dlg.m_page2.m_FileThread = "Normal"; break;
		case THREAD_PRIORITY_BELOW_NORMAL: Dlg.m_page2.m_FileThread = "Below Normal"; break;
		case THREAD_PRIORITY_LOWEST: Dlg.m_page2.m_FileThread = "Lowest"; break;
	}
	switch (m_priorClipThread) {
		case THREAD_PRIORITY_NORMAL: Dlg.m_page2.m_ClipThread = "Normal"; break;
		case THREAD_PRIORITY_BELOW_NORMAL: Dlg.m_page2.m_ClipThread = "Below Normal"; break;
		case THREAD_PRIORITY_LOWEST: Dlg.m_page2.m_ClipThread = "Lowest"; break;
	}
	Dlg.m_page3.m_bFileRecv = m_bFileRecv;
	Dlg.m_page3.m_bDisConf = m_bDisConf;
	Dlg.m_page3.m_bPackRecv = m_bPackRecv;
	Dlg.m_page3.m_bJoinMsg = m_bJoinMsg;
	Dlg.m_page3.m_nPointer = m_nPointer;
	Dlg.m_page3.m_bCompress = m_bCompress;
	
	Dlg.DoModal();

	m_FilePack = Dlg.m_page2.m_FilePack;
	m_ClipPack = Dlg.m_page2.m_ClipPack;
	if (Dlg.m_page2.m_ProcThread == "Normal") 
		m_priorProcThread = THREAD_PRIORITY_NORMAL;
	if (Dlg.m_page2.m_ProcThread == "Below Normal") 
		m_priorProcThread = THREAD_PRIORITY_BELOW_NORMAL;
	if (Dlg.m_page2.m_ProcThread == "Lowest") 
		m_priorProcThread = THREAD_PRIORITY_LOWEST;

	if (m_pProcMsgThread != NULL)
		m_pProcMsgThread->SetThreadPriority(m_priorProcThread);
		
	if (Dlg.m_page2.m_FileThread == "Normal") 
		m_priorFileThread = THREAD_PRIORITY_NORMAL;
	if (Dlg.m_page2.m_FileThread == "Below Normal") 
		m_priorFileThread = THREAD_PRIORITY_BELOW_NORMAL;
	if (Dlg.m_page2.m_FileThread == "Lowest") 
		m_priorFileThread = THREAD_PRIORITY_LOWEST;
	
	for (i = 0; i < MAX_FILES; i++)
		if (Trans[i] != NULL) 
			Trans[i]->m_pThread->SetThreadPriority(m_priorFileThread);

	if (Dlg.m_page2.m_ClipThread == "Normal") 
		m_priorClipThread = THREAD_PRIORITY_NORMAL;
	if (Dlg.m_page2.m_ClipThread == "Below Normal") 
		m_priorClipThread = THREAD_PRIORITY_BELOW_NORMAL;
	if (Dlg.m_page2.m_ClipThread == "Lowest") 
		m_priorClipThread = THREAD_PRIORITY_LOWEST;

	if (ClipTrans != NULL)
		ClipTrans->m_pThread->SetThreadPriority(m_priorClipThread);
	
	m_bFileRecv = Dlg.m_page3.m_bFileRecv;
	m_bDisConf = Dlg.m_page3.m_bDisConf;
	m_bPackRecv = Dlg.m_page3.m_bPackRecv;
	m_bJoinMsg = Dlg.m_page3.m_bJoinMsg;
	m_nPointer = Dlg.m_page3.m_nPointer;
	m_bCompress = Dlg.m_page3.m_bCompress;
}



///////////////////////////////////////////////////////////////////////////
// ConnectSocket()
///////////////////////////////////////////////////////////////////////////
// Establishes connection to a socket within a server
// Called by OnNetworkConnect
///////////////////////////////////////////////////////////////////////////
BOOL CClientDoc::ConnectSocket(LPCTSTR lpszaddr)
{
	m_pSocket = new CClientSocket(this);

	if (!m_pSocket->Create(0, SOCK_STREAM, FD_WRITE | FD_READ | FD_CONNECT | FD_CLOSE)) 
		if (m_pSocket->GetLastError() != WSAEWOULDBLOCK) {
			delete m_pSocket;
			m_pSocket = NULL;
			AfxMessageBox(IDS_CREATEFAILED);
			return FALSE;
		}
	m_bTryConnect = TRUE;	// Trying to connect - disable Connect CmdUI
	m_pSocket->Connect(lpszaddr, 700);
	
	return TRUE;
}
	
///////////////////////////////////////////////////////////////////////////
// ProcessConnect()
///////////////////////////////////////////////////////////////////////////
// Called by ClientSocket::OnConnect(). Responds to possible errors or 
// (if no error occurs) performs operations that follow a client's
// connection (starts Msg processing thread and requests id)
///////////////////////////////////////////////////////////////////////////
BOOL CClientDoc::ProcessConnect(int nErrorCode)
{
	if (nErrorCode == 0) {
		TRACE("Socket connected\n");
		// Get Handles to view windows
		g_ListHwnd = m_pListView->GetSafeHwnd();	
		g_RecvHwnd = m_pChatRecvView->GetSafeHwnd();		
		TRACE("Got List handle %X\n", g_ListHwnd);
		TRACE("Got Recv handle %X\n", g_RecvHwnd);
		
		// Begin Thread
		m_pProcMsgThread = AfxBeginThread(MsgThreadProc, this, m_priorProcThread/*THREAD_PRIORITY_LOWEST*/);
		TRACE("Thread has just begun\n");
		MsgSendId();	// SEND_ID message
		// Change Main Window title
		CString str;
		str.Format("Multimedia Client Application [%s]", m_strusr);
		AfxGetMainWnd()->SetWindowText(str);
		return TRUE;
	}
	else {
		AfxMessageBox(IDS_ERRORCONNECT); 
		m_bTryConnect = FALSE;
		delete m_pSocket;
		m_pSocket = NULL;	
		return FALSE;
	}
}

///////////////////////////////////////////////////////////////////////////
// ProcessClose()
///////////////////////////////////////////////////////////////////////////
// Called by sockets :OnClose, or when connection is refused by server
// in order to close client's socket and set control variables
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ProcessClose()
{
	if (m_bconnected || m_bTryConnect) {	// if thread is running
		g_Kill.SetEvent();		// Kill thread
		WaitForSingleObject(g_KillAck.m_hObject, INFINITE);
								// Wait for Ack so as to delete socket
		AfxGetMainWnd()->SetWindowText("Multimedia Client Application");
		m_pSocket->Close();	
		delete m_pSocket;
		m_pSocket = NULL;
		m_strgroup.Empty(); m_strusr.Empty();
		DumpOldUsrlist();		
		DestroyUserDB();
		m_nlength1=0;	m_bnewlist=FALSE;
		m_nDBLen = 0;	m_buserDB = FALSE;
		
		SetModifiedFlag(TRUE);
		UpdateAllViews(NULL);
		SetModifiedFlag(FALSE);
		if (!m_bTryConnect)		// if user had been connected
			AfxMessageBox(IDS_CONNECTIONCLOSED);
		m_bconnected = m_bjoined = m_bTryConnect = FALSE;
	}
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// SEND MESSAGE FUNCTIONS
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// MsgSendId()
///////////////////////////////////////////////////////////////////////////
// Sends a SEND_ID msg to server requesting the specific client's
// unique identifier (id)
///////////////////////////////////////////////////////////////////////////  
void CClientDoc::MsgSendId()
{
	BYTE msg[MSG_LENGTH]; LPCTSTR temp; UINT i;
	memset((LPBYTE) msg, 0, MSG_LENGTH);

	msg[PAT_BEG] = MSG_ID;     // SEND_ID msg is formed 
	msg[PAT_END] = MSG_ID;
	msg[ID] = SEND_ID;         
	msg[SEND] = 0;
	msg[RECV] = SERVER_ID;

	temp = (LPCTSTR) m_strusr;
	for (i = 0; i < 8 && temp[i] != '\0'; i++)
		msg[i + USR_BEG] = (BYTE) temp[i];
	
	temp = (LPCTSTR) m_strpassw;
	for (i = 0; i < 8 && temp[i] != '\0'; i++)
		msg[i + PASSW_BEG] = (BYTE) temp[i];
	
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
	TRACE("message has been added to buffertail\n");
}


///////////////////////////////////////////////////////////////////////////
// JoinGroup()
///////////////////////////////////////////////////////////////////////////
// Sends a JOIN_GROUP msg to server in order the client to join a group
///////////////////////////////////////////////////////////////////////////
void CClientDoc::JoinGroup(const char* group_name)
{
	BYTE msg[MSG_LENGTH]; UINT i;
	memset((LPBYTE) msg, 0, MSG_LENGTH);

	// Proper message for joining group is formed and sent
	msg[PAT_BEG] = MSG_ID;		
	msg[PAT_END] = MSG_ID;
	msg[ID] = JOIN_GROUP;
	msg[SEND] = m_id;
	msg[RECV] =SERVER_ID;

	LPCTSTR temp;
	temp = (LPCTSTR) group_name;
	TRACE("Client wants to join group: %s\n", temp);
	for (i = 0; i < 16  && temp[i] != '\0'; i++)
		msg[i + GROUP_NAME] = (BYTE) temp[i];

	m_strgroup = (CString) group_name;
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////
// SendDisjoinMsg()
///////////////////////////////////////////////////////////////////////////
// Sends a DISJOIN msg to server to disjoin client from its current group
/////////////////////////////////////////////////////////////////////////// 
void CClientDoc::SendDisjoinMsg(CString group_name)
{
	BYTE msg[MSG_LENGTH]; UINT i;
	memset((LPBYTE) msg, 0, MSG_LENGTH);
	
	//Proper message for disjoining group is formed and sent
	TRACE("Disjoin message is sent\n");
	msg[PAT_BEG] = MSG_ID;		
	msg[PAT_END] = MSG_ID;
	msg[ID] = DISJOIN;
	msg[SEND] = m_id;
	msg[RECV] =SERVER_ID;

	LPCTSTR temp;
	temp = (LPCTSTR) group_name;
	TRACE("Group Name :%s", temp);
	for (i = 0; i < 16 && temp[i] != '\0'; i++)
		msg[i + GROUP_NAME] = (BYTE) temp[i];

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}	

///////////////////////////////////////////////////////////////////////////
// SendMsg()
///////////////////////////////////////////////////////////////////////////
// Function used to send generic messages of specific code to a specific
// receiver (but no parameter can be send)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendMsg(BYTE msg_code, BYTE receiver)
{
	BYTE msg[MSG_LENGTH]; 
	memset((LPBYTE) msg, 0, MSG_LENGTH);

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = msg_code;
	msg[SEND] = m_id;
	msg[RECV] = receiver;

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}	

///////////////////////////////////////////////////////////////////////////
// SendFileAck()
///////////////////////////////////////////////////////////////////////////
// Sends Acknowledge (FILE_ACK) msg to a client that sends a file, 
// in order to notify of normal reception of a file packet
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendFileAck(BYTE fileid, WORD TransNr)
{
	BYTE msg[MSG_LENGTH]; UINT i; BYTE ndx;
	memset((LPBYTE) msg, 0, MSG_LENGTH);

	for (i = 0; i < MAX_FILES; i++) {
		if (Recv[i] != NULL)
			if (Recv[i]->m_recvfileid == fileid)
				ndx = (BYTE) i;
	}
		
	msg[PAT_BEG] = MSG_ID;	msg[PAT_END] = MSG_ID;
	msg[ID] = FILE_ACK;
	msg[SEND] = m_id;
	msg[RECV] = Recv[ndx]->m_fsendid;
	msg[4] = fileid;
	*((LPWORD) (msg + 5)) = TransNr;

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////////////////////////////
// SendClipMsg()
///////////////////////////////////////////////////////////////////////////
// Sends a SEND_CLIPBOARD msg to another client indicate that
// the sender of the msg is going to send a clipboard image. 
// Parameters related to the image are incorporated within the msg
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendClipMsg(BYTE recvid, DWORD TotalLen, DWORD ImageLen, BOOL Pointer)
{
	BYTE msg[MSG_LENGTH];
	memset((LPBYTE) msg, 0, MSG_LENGTH);

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = SEND_CLIPBOARD;
	msg[SEND] = m_id;
	msg[RECV] = recvid;

	*((LPDWORD) (msg + 4)) = TotalLen;
	*((LPDWORD) (msg + 8)) = ImageLen;
	if (Pointer)
		msg[POINT_POS] = 1;

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////////////////////////////
// SendClipAck()
///////////////////////////////////////////////////////////////////////////
// Send a CLIP_ACK msg to a client that sends a clipboard or pointer
// window image to notify of succesful image packet reception
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendClipAck(BYTE sendid, WORD TransNr)
{
	BYTE msg[MSG_LENGTH];
	memset((LPBYTE) msg, 0, MSG_LENGTH);
	
	msg[PAT_BEG] = MSG_ID;	
	msg[PAT_END] = MSG_ID;
	msg[ID] = CLIP_ACK;
	msg[SEND] = m_id;
	msg[RECV] = sendid;
	*((LPWORD) (msg+5)) = TransNr;

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////////////////////////////
// DeleteClipWnd()
///////////////////////////////////////////////////////////////////////////
// Deletes a Clipboard or pointer Window object
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DeleteClipWnd(CClipWnd* pWnd)
{
	int i;
	for (i = 0; i < MAX_FILES; i++)
	{
		if (ClipWnd[i] == pWnd) {
			delete ClipWnd[i];
			ClipWnd[i] = NULL;
			delete ClipRecv[i];
			ClipRecv[i] = NULL;
		}
	}
	if (PointerWnd == pWnd) {
		delete PointerWnd;
		PointerWnd = NULL;
		if (PointerClip)
			delete PointerClip;
		PointerClip = NULL;
	}
}

///////////////////////////////////////////////////////////////////////////
// DeleteProgressDlg() 
///////////////////////////////////////////////////////////////////////////
// Deletes a Dialog object indicating transfer progress in case
// it hasn't been updated for a long time
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DeleteProgressDlg(CProgressDlg* pDlg)
{
	int i;
	for (i = 0; i < MAX_FILES; i++) {
		if (Recv[i] != NULL) {
			if (Recv[i]->m_dlg == pDlg) {
				Recv[i]->m_dlg->DestroyWindow();
				Recv[i]->m_dlg = NULL;
				Recv[i]->m_recvfile.Close(); //closes destination file
				CString messg;
				messg.Format("Transfer of %s has blocked\n", Recv[i]->m_strrecvfile);
				TRACE("%s\n", messg);
				AfxMessageBox(messg);
				delete Recv[i];
				Recv[i] = NULL;
			}
		}
	}
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// FILE TRANSFER PACKETS Functions
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// SendFileName()
///////////////////////////////////////////////////////////////////////////
// Sends the first packet of a file transfer sequence, containing
// the file's name
/////////////////////////////////////////////////////////////////////////// 
void CClientDoc::SendFileName(BYTE fileid)
{
	TRACE("SendFileName called\n");
	LPBYTE FilePacket; DWORD Len, i, k;
	k = (DWORD) Trans[fileid]->m_strfile.GetLength();

	Len = max ((DWORD)k, MSG_LENGTH-HEADER_LENGTH);
	
	FilePacket = (LPBYTE) MemAlloc(NULL, HEADER_LENGTH + Len,
	   								   MEM_COMMIT, PAGE_READWRITE);
	for (i=0; i<HEADER_LENGTH + Len; i++)
		FilePacket[i] = 0;

	//Form packet header
	FilePacket[SEND_POS] = m_id;
	FilePacket[RECV_POS] = Trans[fileid]->m_frecvid;
	FilePacket[TYPE_POS] = FILE_TRANSFER + fileid;
	*((LPDWORD) (FilePacket + LEN_POS)) = Len;  TRACE("Packet length = %d\n",*((LPDWORD) (FilePacket + LEN_POS)));
	// Trans. Nr. = 0
	*((LPWORD) (FilePacket + TRANSNO)) = Trans[fileid]->m_sendpacket;
	LPCTSTR temp = (LPCTSTR) Trans[fileid]->m_strfile;
	for (i = 0; i < (DWORD) Trans[fileid]->m_strfile.GetLength(); i++)
		FilePacket[HEADER_LENGTH + i] = temp[i];
	
	m_pSocket->BufferOut->AddTail((LPSTR) FilePacket, HEADER_LENGTH+Len, m_bCompress);
	MemFree(FilePacket, HEADER_LENGTH + Len, MEM_DECOMMIT|MEM_RELEASE);
}
	
///////////////////////////////////////////////////////////////////////////
// MakebufferPacket()
///////////////////////////////////////////////////////////////////////////
// Sends file transfer packet, containing the file's data contents
/////////////////////////////////////////////////////////////////////////// 
LPBYTE CClientDoc::MakebufferPacket(LPBYTE buffer, DWORD length, BYTE fileid)
{
	LPBYTE FilePacket; DWORD Len, i;

	Len = max(length, MSG_LENGTH-HEADER_LENGTH);
	
	FilePacket = (LPBYTE) MemAlloc(NULL, HEADER_LENGTH + Len,
										MEM_COMMIT, PAGE_READWRITE);

	for (i=0; i<HEADER_LENGTH + Len; i++)
			FilePacket[i] = 0;

	//Form packet header
	FilePacket[SEND_POS]= m_id;
	FilePacket[RECV_POS]= Trans[fileid]->m_frecvid;
	FilePacket[TYPE_POS]= FILE_TRANSFER + fileid;
	TRACE("TYPE_POS byte : %d\n", FilePacket[TYPE_POS]); 
	*((LPDWORD) (FilePacket + LEN_POS)) = Len;
	BYTE SeqNr = Trans[fileid]->m_SeqNr << 4;		// e.g. 00000001 => 00010000
	FilePacket[SEQ_POS] |= SeqNr;
	*((LPWORD) (FilePacket + TRANSNO)) = Trans[fileid]->m_sendpacket;
	TRACE("File Packet length = %d, Receiver = %d\n",*((LPDWORD) (FilePacket + LEN_POS)) & 0x000FFFFF, FilePacket[RECV_POS]);

	for (i=0; i<length; i++)
		FilePacket[i + HEADER_LENGTH] = buffer[i];

	return FilePacket;
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// THREAD FUNCTION MsgThreadProc()
///////////////////////////////////////////////////////////////////////////
// Controlling function for the thread that is responsible for:
// (a) picking up msgs or packets and calling proper processing procedures
// (b) picking up msgs or packets and sending them   
///////////////////////////////////////////////////////////////////////////
UINT MsgThreadProc (LPVOID pParam)
{
	CClientDoc* pDoc = (CClientDoc*) pParam;
	DWORD length=0;
	LPSTR buffer=NULL; LPSTR vidbuff = NULL;
	char messbuff[80];

	while (pDoc->m_bconnected || pDoc->m_bTryConnect)
	{
		// if Killed by DeleteContents
		if (WaitForSingleObject(g_Kill.m_hObject, 0) == WAIT_OBJECT_0) {
			g_KillAck.SetEvent();	// Ack kill so that DeleteContents may proceed
			return 0;
		}

	//---MESSAGES---
		while (	//pDoc->m_pSocket->m_SendFlag == SEND_MSG &&
				!pDoc->m_pSocket->m_LeftMsg	&& // i.e. Message was not blocked
				!pDoc->m_pSocket->m_LeftData && 
				!pDoc->m_pSocket->MsgBufferOut->BufferIsEmpty()) 
			{
				TRACE("Send procedure began\n");
				pDoc->m_pSocket->m_SendMsgBuffer
					= pDoc->m_pSocket->MsgBufferOut->RemoveHead(&length, NO_DECOMP);
				pDoc->m_pSocket->m_LeftMsg = length;
				pDoc->m_pSocket->m_SendFlag = SEND_MSG;
				EnterCriticalSection(&(pDoc->m_pSocket->m_csLeft));
				pDoc->m_pSocket->SendMsg();
				LeaveCriticalSection(&(pDoc->m_pSocket->m_csLeft));
				TRACE("Msg sent to server\n");
			}
		if (!pDoc->m_pSocket->m_LeftMsg)	// if exit with BufferIsEmpty
			pDoc->m_pSocket->m_SendFlag = SEND_DATA;

		while ( //pDoc->m_pSocket != NULL && //Not disconnected
				!pDoc->m_pSocket->MsgBufferIn->BufferIsEmpty()) 
		{
			TRACE("Read a message from buffer\n");
			buffer =(LPSTR) pDoc->m_pSocket->MsgBufferIn->RemoveHead(&length, NO_DECOMP);
			pDoc->ProcessMsg(buffer);
			MemFree(buffer, length, MEM_DECOMMIT|MEM_RELEASE);
		}

		// if (pDoc->m_pSocket != NULL) {	// Not disconnected

		//---PACKETS---
		// Get 1st packet from BufferIn
		if (!pDoc->m_pSocket->BufferIn->BufferIsEmpty()) 
		{
			buffer = pDoc->m_pSocket->BufferIn->RemoveHead(&length, DECOMP);
			sprintf(messbuff,"Get Packet %d bytes from BufferIn from Client %d", length, buffer[SEND_POS]);
			TRACE("%s\n",messbuff);
			if (pDoc->m_bPackRecv) {
				sprintf(messbuff,"Get Packet %d bytes from BufferIn from Client %s", length, pDoc->GetNameByID(buffer[SEND_POS]));
				AfxMessageBox(messbuff);
			}
			// Do Header processing here to see what you should do with the Packet
			pDoc->ProcessPacket(buffer, length-HEADER_LENGTH);
			MemFree(buffer, length, MEM_DECOMMIT|MEM_RELEASE);
		}
		// Get 1st packet from VideoBufferIn
		if (!pDoc->m_pSocket->VideoBufferIn->BufferIsEmpty()) 
		{
			if (!pDoc->m_videoList->m_bFirstVideo) {
				pDoc->icmgr->DriverOpen();
				pDoc->m_videoList->m_bFirstVideo = TRUE;
			}
			else {
				buffer = pDoc->m_pSocket->VideoBufferIn->RemoveHead(&length, DECOMP);
				g_framesplayed++;
				
				VIDEO* Video = pDoc->m_videoList->GetPtrByID((BYTE) buffer[SEND_POS]);
				// If first video packet from this user, create its window
				if (Video == NULL) {
					pDoc->m_videoList->AddVideoUser((BYTE) buffer[SEND_POS]);
					::PostMessage(g_ListHwnd, WM_VIDEORECV, (BYTE) buffer[SEND_POS], 0);
				}
				else {
					HWND hwnd = NULL;
					if (Video->pWnd != NULL)
						hwnd = Video->pWnd->GetSafeHwnd();
					if (hwnd != NULL) {
						DWORD VideoLen = *((LPDWORD) (buffer+LEN_POS)) & 0x000FFFFF;
						pDoc->icmgr->DriverBeginDraw(hwnd);
						pDoc->icmgr->DriverWindow(hwnd);
						pDoc->icmgr->DriverDraw((LPBYTE)(buffer+HEADER_LENGTH), VideoLen);
						pDoc->icmgr->DriverEndDraw();
					}
				}
				TRACE("VInRmv %d bytes - VIDEO - Video Buffer packs=%d - Video Free space=%d\n",
					   length, pDoc->m_pSocket->VideoBufferIn->GetCount(), pDoc->m_pSocket->VideoBufferIn->GetFreeBufSpace());
				MemFree(buffer, length, MEM_DECOMMIT|MEM_RELEASE);
			}
		}

		// Get 1st packet from AudioBufferIn
		/*if (!pDoc->m_pSocket->AudioBufferIn->BufferIsEmpty()) 
		{
			buffer = pDoc->m_pSocket->VideoBufferIn->RemoveHead(&length, DECOMP);
			::PostMessage(g_ListHwnd, WM_AUDIORECV, 0, 0);
			MemFree(buffer, length, MEM_DECOMMIT|MEM_RELEASE);
		}*/
		// Get 1st Packet from BufferOut and begin Send
		// if finished previous packet, 
		EnterCriticalSection(&(pDoc->m_pSocket->m_csLeft));
		if (pDoc->m_pSocket->m_SendFlag == SEND_DATA && 
			pDoc->m_pSocket->m_LeftData == 0 &&
			!pDoc->m_pSocket->BufferOut->BufferIsEmpty()) 
		{
			pDoc->m_pSocket->m_SendDataBuffer 
				= pDoc->m_pSocket->BufferOut->RemoveHead(&length, NO_DECOMP);
			pDoc->m_pSocket->m_LeftData = length;
			pDoc->m_pSocket->m_SendLength = length;
			// begin sending the packet
			TRACE("Sending packet to %d\n", pDoc->m_pSocket->m_SendDataBuffer[RECV_POS]);
			pDoc->m_pSocket->SendData();
		}
		LeaveCriticalSection(&(pDoc->m_pSocket->m_csLeft));
		//if (!pDoc->m_pSocket->m_LeftData)	// if finished packet
		//	pDoc->m_pSocket->m_SendFlag = SEND_MSG;
			
		//}	 // Not Disconnected
	}
	AfxMessageBox("Thread Returned");
	return 0;    //ends the thread
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// PROCESSING FUNCTIONS (OF MSGS AND PACKETS)
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// ProcessMsg()
/////////////////////////////////////////////////////////////////////////// 
// Processes the various msgs which are received by a client, by updating
// necessary data and responding properly when required
// Called by the processing thread
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ProcessMsg(LPSTR msg)
{
	BYTE mess[MSG_LENGTH];	UINT i; BYTE m, ndx;

	TRACE("Processing msg !!\n");
	switch(msg[ID]) {
	case CONNECT_OK:
		m_id = (BYTE) msg[RECV];		// ID Assignment
		m_bconnected = TRUE; m_bTryConnect = FALSE;
		AfxMessageBox(IDS_CONNECTOK);   // connect_ok
		break;
	case CONNECT_REF:			
		AfxMessageBox(IDS_CONNECTREF);   //connect_refused
		::PostMessage(g_ListHwnd, WM_CONNECTREFUSED, 0, 0);
		break;
	case CLOSE_CON:		
		m_pSocket->Close();
		delete m_pSocket;
		m_pSocket = NULL;
		m_bconnected = FALSE;
		AfxMessageBox(IDS_CONNECTIONCLOSED);  //connect_closed
		break;
	case JOIN_OK:
		m_bjoined=TRUE;
		SendWhBrdReq();
		m_bnewlist = TRUE;
		m_nlength2 = msg[LENGTH_POS];
		//AfxMessageBox(IDS_GROUPJOINED);
		break;
	case GROUP_LIST_MES:
		m_nlength1 = msg[LENGTH_POS];
		m_bnewgrlist = TRUE;
		AfxMessageBox(IDS_NEWGRLIST);
		break;
	case NEW_LIST:
		//AfxMessageBox(IDS_NEWLIST);
		m_nlength2 = msg[LENGTH_POS];		
		m_bnewlist = TRUE;
		break;
	case USERDB_OK:
		m_nDBLen = *((LPDWORD) (msg+4));
		m_buserDB = TRUE;
		break;
	case SEND_FILE_REQ:	{
		int ret;
		DWORD length = *((LPDWORD) (msg + 4));
		BYTE  sender = msg[SEND];
		CString strmesg;
		strmesg.Format("Do you want to receive %d bytes file from user %s",
						length, GetNameByID(sender));
		if (m_bFileRecv)
			ret = AfxMessageBox(strmesg, MB_YESNO);
		else
			ret = IDYES;

		if ((ret == IDYES) && (Recv[m_recvfilecount] == NULL)) 
		{
			Recv[m_recvfilecount] = new CFileRecv;
			Recv[m_recvfilecount]->m_fsendid = sender;
			Recv[m_recvfilecount]->m_recvfileid = msg[FILE_ID_POS];
			Recv[m_recvfilecount]->m_frecvlen = length;
			Recv[m_recvfilecount]->m_recvpacket = 0;
			m_recvfilecount = (m_recvfilecount + 1) % MAX_FILES;
			// SEND_FILE_OK for this fileid
			for (i=0; i<MSG_LENGTH; ++i) //initialisation
				mess[i]=0;   
			mess[PAT_BEG] = mess[PAT_END] = MSG_ID;
			mess[ID] = SEND_FILE_OK;
			mess[SEND] = m_id;	mess[RECV] = sender;
			mess[FILE_ID_POS] = msg[FILE_ID_POS];
			m_pSocket->MsgBufferOut->AddTail((LPSTR) mess, MSG_LENGTH, NO_COMP);
		}
		else {
			// SEND_FILE_REF
			for (i=0; i<MSG_LENGTH; ++i) //initialisation
				mess[i]=0;   
			mess[PAT_BEG] = mess[PAT_END] = MSG_ID;
			mess[ID] = SEND_FILE_REF;
			mess[SEND] = m_id;	mess[RECV] = sender;
			mess[FILE_ID_POS] = (BYTE) msg[FILE_ID_POS];
			m_pSocket->MsgBufferOut->AddTail((LPSTR) mess, MSG_LENGTH, NO_COMP);
		}
	}	break;
	case SEND_FILE_OK: {
		BYTE id1 = (BYTE) msg[FILE_ID_POS];
		CString mb1;
		mb1.Format("User accepts file %s", Trans[id1]->m_strfile);
		AfxMessageBox(mb1);
		// pass fileid to message handler
		//::PostMessage(g_ListHwnd, WM_SENDFILE, (UINT) id1, 0);
		//TRACE("Message Posted to view\n");
		Trans[id1]->m_Ok = TRUE;
	}	break;
	case SEND_FILE_REF: {
		BYTE id2 = (BYTE) msg[FILE_ID_POS];
		CString mb2;
		mb2.Format("User rejects file %s", Trans[id2]->m_strfile);
		AfxMessageBox(mb2);
		Trans[id2]->m_dlg->m_bcancel = TRUE;
		//delete Trans[id2];
		//Trans[id2] = NULL;
	}	break;
	case FILE_ACK: {
		BYTE id3 = (BYTE) msg[4];
		TRACE("Received FILE ACK %d, %d\n", (BYTE) msg[FILE_ID_POS], *((LPWORD) (msg+5)));
		if (Trans[id3]==NULL)
			break;    //in case Trans object was destroyed unexpectedly
		if (*((LPWORD) (msg+5)) > Trans[id3]->m_sendpacket) {
			Trans[id3]->m_sendpacket++;								// Trans. Nr
			Trans[id3]->m_SeqNr = (Trans[id3]->m_SeqNr + 1) % 16;	// Seq. Nr. mod-16
			Trans[id3]->m_MaySendFile = TRUE;
		}
	}	break;
	case SEND_CLIPBOARD: {
		// Pointer window image
		if ((BYTE) msg[POINT_POS] == 1) {
			if (PointerClip == NULL) {
				PointerClip = new CClipRecv;
				PointerClip->m_sendid = (BYTE) msg[SEND];
				PointerClip->m_TotalLen = *((LPDWORD) (msg+4));
				PointerClip->m_ImageLen = *((LPDWORD) (msg+8));
				PointerClip->m_recvlen = 0;
				PointerClip->m_recvpacket = 0;
				PointerClip->m_buff = (LPBYTE) MemAlloc(NULL, 
											PointerClip->m_TotalLen, MEM_COMMIT, PAGE_READWRITE);
				SendMsg(SEND_CLIP_OK, (BYTE) msg[SEND]);
			}
			break;
		}

		ndx = MAX_FILES;
		for (m = 0; m < MAX_FILES && ndx == MAX_FILES; m++)
			if (ClipRecv[m] == NULL)
				ndx = m;
		if (ndx != MAX_FILES) {
			// Create clipRecv object and get data from msg
			ClipRecv[ndx] = new CClipRecv;
			ClipRecv[ndx]->m_sendid = (BYTE) msg[SEND];
			ClipRecv[ndx]->m_TotalLen = *((LPDWORD) (msg+4));
			ClipRecv[ndx]->m_ImageLen = *((LPDWORD) (msg+8));
			ClipRecv[ndx]->m_recvlen = 0;
			ClipRecv[ndx]->m_recvpacket = 0;
			ClipRecv[ndx]->m_buff = (LPBYTE) 
				MemAlloc(NULL, ClipRecv[ndx]->m_TotalLen, MEM_COMMIT, PAGE_READWRITE);
			SendMsg(SEND_CLIP_OK, (BYTE) msg[SEND]);
		}
		else
			AfxMessageBox("Cannot receive another Clipboard Object");
	}	break;
	case SEND_CLIP_OK: {
		if (ClipTrans == NULL)
			break;    //in case Trans object was destroyed unexpectedly		
		if (ClipTrans->m_recvid == (BYTE) msg[SEND] || ClipTrans->m_recvid == ALLGROUP) {
			ClipTrans->m_Ok = TRUE;
		}
	} break;
	case CLIP_ACK: {
		if (ClipTrans == NULL)
			break;    //in case Trans object was destroyed unexpectedly
		if (*((LPWORD) (msg+5)) > ClipTrans->m_sendpacket) {
			ClipTrans->m_sendpacket++;									// Trans. Nr
			ClipTrans->m_SeqNr = (ClipTrans->m_SeqNr + 1) % MAX_FILES;	// Seq. Nr. mod-16
			ClipTrans->m_MaySendClip = TRUE;
		}
	}	break;
	case OPERATION_OK:
		AfxMessageBox("Operation completed successfully");
		break;
	case OPERATION_DEN:
		AfxMessageBox("You have no authority to perform this operation. Access Denied");
		break;
	case POINTERMSG:
		if (PointerWnd != NULL) {
			TRACE("Received Coordinates\n");
			int xparam = *((LPINT) (msg + XPOS));
			int yparam = *((LPINT) (msg + YPOS));
			PointerWnd->PostMessage(WM_NEWCOORD, (UINT) xparam, (LONG) yparam);
		}
		break;
	case TIME_MARK:	// Time Mark from Server
		m_MarkArrived = NowSecs();
		m_TimeMark = (time_t) *((LPDWORD) (msg + 4));
		break;
	case ADD_OBJECT:
		AddObject(msg);
		break;
	case REMOVE_OBJECT:
		RemoveObject(msg);
		break;
	case MOVE_OBJECT:
		MoveObject(msg);
		break;
	case COLOR_OBJECT:
		ChangeColor(msg);
		break;
	default:
		AfxMessageBox("Received message.");
		break;
	}
}

///////////////////////////////////////////////////////////////////////////
// ProcessPacket()
///////////////////////////////////////////////////////////////////////////
// Processes teh various packet that are received by a client
// Called by the processing thread
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ProcessPacket(LPSTR buffer, DWORD length)
{
	TRACE("Process Packet called\n");
	if (buffer[SEND_POS] == SERVER_ID){		// control packet sent by server
		TRACE("Processing server packet\n");
		switch ((BYTE) buffer[TYPE_POS]) {
				 
		case GR_USR_LIST: {
			TRACE("List of Users has arrived\n");
			if (m_bnewlist) {
			    TRACE("List length expected: %d\n", m_nlength2);
				DumpOldUsrlist();
				BYTE j = DATA_BEG;	//j indicates the starting position of a new user record in the packet 
				EnterCriticalSection(&m_csusr);
				while (j - DATA_BEG < m_nlength2)
				{	
					USER* User = (USER*) malloc(sizeof(USER));
					BYTE i;
					for(i=0; i<9; i++)
						User->UserName[i] = '\0';						
					User->UserID = (BYTE) buffer[j];
					for (i=0; i<8; i++)
						User->UserName[i] = buffer[j+1+i]; // +1 because of ID
					TRACE("User ID: %d\n", User->UserID); TRACE("User Name:%s\n", User->UserName);
									
					m_userslist.AddTail(User);
					
					j+=9;	// move to next user record in packet
				}
				LeaveCriticalSection(&m_csusr);
				m_bnewlist=FALSE;  //new list has been used (is not expected)
			}
			::PostMessage(g_ListHwnd, WM_UPDATEVIEWS, 0, 0);
			TRACE("Posted message to View\n");
		}	break;
		case GROUP_LIST: {
			TRACE("List of groups has arrived\n");
			if (m_bnewgrlist) {
				TRACE("Packet length: %d\n", m_nlength1);
				DestroyOldGroupList();
				BYTE l = DATA_BEG;		//l is indicating the starting position of a new user record in the packet 
				EnterCriticalSection(&m_csgr);
				while (l - DATA_BEG < m_nlength1)
				{
					GROUP* Group = (GROUP*) malloc(sizeof(GROUP));
					BYTE k;
					for (k=0; k<17; k++)
						Group->GroupName[k] = '\0';
					Group->GroupID = (BYTE) buffer[l];
					for(k=0; k<16; k++)
						Group->GroupName[k] = buffer[l+1+k]; // +1 because of ID
					TRACE("Group ID:%d\n", Group->GroupID);	TRACE("Group Name:%s\n", Group->GroupName);
					
					m_grouplist.AddTail(Group);

					l+=17; // move to next group record in packet
				}
				LeaveCriticalSection(&m_csgr);
				m_bnewgrlist = FALSE;
			}
		}	break;
		case USERDB_TYPE: {
			TRACE("User DB List has arrived\n"); TRACE("Packet length: %d\n", m_nDBLen);
			DestroyUserDB();

			DWORD l = HEADER_LENGTH;
			while (l - HEADER_LENGTH < m_nDBLen)
			{
				USERDB* User = (USERDB*) malloc(sizeof(USERDB));
				BYTE k;
				for (k=0; k<9; k++)	
					User->UserName[k] = User->Password[k] = '\0';
				for(k = 0; k < 8; k++) {
					User->UserName[k] = buffer[l+k]; 
					User->Password[k] = buffer[l+k+8];
				}
				User->UserType = (BYTE) buffer[l+16];
				User->bVideo = (BYTE) buffer[l+17];
				User->bAudio = (BYTE) buffer[l+18];
				User->bChat = (BYTE) buffer[l+19];
				User->bWhisper = (BYTE) buffer[l+20];
				User->bFile = (BYTE) buffer[l+21];
				User->bClipboard = (BYTE) buffer[l+22];
				User->bPointer = (BYTE) buffer[l+23];
				User->bWhiteboard = (BYTE) buffer[l+24];
				User->bSlides = (BYTE) buffer[l+25];
				m_userDBList.AddTail(User);
				l+=26; // move to next record in userDB packet
			}
			m_buserDB = TRUE;
		}	break;
		default: break;
		} // switch
	}	
	
	BYTE type = ((BYTE) buffer[TYPE_POS]) & 0xF0;
	TRACE("Packet type: %d\n", type);

	switch (type) { //packet from client

	case CHAT:	{
		TRACE("Processing Chat Packet\n");
		DWORD Len = *((LPDWORD) (buffer + LEN_POS));
		LPSTR temp = (LPSTR) calloc((int)Len, sizeof(char));
		UINT i;
		for (i = DATA_BEG; i < DATA_BEG + Len; i++)	{
			temp[i-DATA_BEG] = buffer[i];
		}
		// Update CHAT member variable
		m_strchat.GetBuffer((int)Len + 11);
		CString sender;	sender.GetBuffer(9);
		if ((BYTE) buffer[SEND_POS] != SERVER_ID) {
			sender = GetNameByID((BYTE) buffer[SEND_POS]);
			m_strchat.Format("%s : %s", (LPCTSTR) sender, (LPCTSTR) temp);
			::PostMessage(g_ListHwnd, WM_UPDATECHAT, 0, 0);
		}
		else if (m_bJoinMsg) {
			m_strchat.Format(">> %s", (LPCTSTR) temp);
			::PostMessage(g_ListHwnd, WM_UPDATECHAT, 2, 0);
		}
		free(temp);
	}	break;
		
	case WHISPER_TYPE:	{
		TRACE("Processing Whisper Packet\n");
		DWORD Len = *((LPDWORD) (buffer + LEN_POS));
		LPSTR temp = (LPSTR) calloc((int)Len, sizeof(char));
		UINT i;
		for (i = DATA_BEG; i < DATA_BEG + Len; i++)	{
			temp[i-DATA_BEG] = buffer[i];
		}
		// Update CHAT member variable
		m_strchat.GetBuffer((int)Len + 11);
		CString sender;
		sender.GetBuffer(9);
		sender = GetNameByID((BYTE) buffer[SEND_POS]);
		m_strchat.Format("%s : %s", (LPCTSTR) sender, (LPCTSTR) temp);
		
		::PostMessage(g_ListHwnd, WM_UPDATECHAT, 1, 0);
		free(temp);
	}	break;

	case FILE_TRANSFER: {
		BYTE fileid = ((BYTE) buffer[TYPE_POS]) & 0x0F;
		BYTE sendid = (BYTE) buffer[SEND_POS];
		TRACE("Processing file %d transfer packet\n", fileid);
		// Find position in Recv[MAX_FILES] tables
		BYTE m, ndx;
		for (m = 0; m < MAX_FILES; m++) {
			if (Recv[m] != NULL)
				if (Recv[m]->m_recvfileid == fileid && 
					Recv[m]->m_fsendid == sendid)
					ndx = m;	
		}
		if (Recv[ndx]==NULL)
			break;
		// Check if correct packet
		if ( *((LPWORD) (buffer+TRANSNO)) == Recv[ndx]->m_recvpacket) {
			TRACE("Correct Trans. Nr. %d\n", *((LPWORD) (buffer+TRANSNO)));

			if ( *((LPWORD) (buffer+TRANSNO)) == 0) {
				TRACE("Processing first packet of transfer sequence\n");
				
				DWORD Len = *((LPDWORD) (buffer + LEN_POS)) & 0x000FFFFF;
				char temp[256]; UINT i;	// Temporary filename storage
				for (i = 0; i < 256; i++) temp[i] = 0;
				for (i  = 0; i < Len; i++)
					temp[i] = buffer[i + HEADER_LENGTH];
				Recv[ndx]->m_strrecvfile = (CString) temp;
				TRACE("File that is transferred: %s\n", Recv[ndx]->m_strrecvfile);
				// Post message to view to display File Save Dialog
				::PostMessage(g_ListHwnd, WM_RECVFILEDLG, (UINT) ndx, 0);
			}
			else if(Recv[ndx]->m_dlg != NULL) 
				//processing packet other than the first one
			{ 
				// ACK packet as soon as possible
				Recv[ndx]->m_recvpacket++;
				SendFileAck(Recv[ndx]->m_recvfileid, Recv[ndx]->m_recvpacket);
				// Write data to file
				DWORD Len = *((LPDWORD) (buffer + LEN_POS)) & 0x000FFFFF;
				TRACE("Packet length: %d\n", Len);
				Recv[ndx]->m_recvfile.Write((LPSTR) buffer + HEADER_LENGTH, Len);
				TRACE("Bytes written %d\n", Len);
				Recv[ndx]->m_frecvlen -= Len;
				TRACE("Remaining length %d\n", Recv[ndx]->m_frecvlen);
				// Update progress dialog
				Recv[ndx]->m_dlg->Update((UINT)(Recv[ndx]->m_totallength-Recv[ndx]->m_frecvlen), (UINT)Recv[ndx]->m_totallength);
				CEdit* pEdit = (CEdit*)Recv[ndx]->m_dlg->GetDlgItem(IDC_PROGRESS_EDIT);
				CString label;
				label.Format("Remaining length: %d bytes of %d", 
				     		  Recv[ndx]->m_frecvlen, Recv[ndx]->m_totallength);
				pEdit->SetWindowText(label);
				// Updates dlg's caption
				CString caption;
				int perc = 100*(Recv[ndx]->m_totallength-Recv[ndx]->m_frecvlen)/Recv[ndx]->m_totallength;
				caption.Format("Transferred: %d%c", perc, '%');
				Recv[ndx]->m_dlg->SetWindowText(caption);

				// End Of File
				if (Recv[ndx]->m_frecvlen<=0 || Recv[ndx]->m_dlg->m_bcancel) {		  
					BOOL cancelled = Recv[ndx]->m_dlg->m_bcancel;
					Recv[ndx]->m_frecvlen=0;
					::PostMessage(g_ListHwnd, WM_DESTROYWND2, (UINT)ndx, 0);
					while (Recv[ndx]->m_dlg != NULL)
					{;}  //do nothing before modeless is destroyed
					Recv[ndx]->m_recvfile.Close(); //closes destination file
					CString messg;
					if (cancelled) {
						messg.Format("Transfer of %s has blocked\n", Recv[ndx]->m_strrecvfile);
						TRACE("%s\n", messg);
						AfxMessageBox(messg);
					}
					else {
						messg.Format("File %s received\n", Recv[ndx]->m_strrecvfile);
						TRACE("%s\n", messg);
						AfxMessageBox(messg);
					}
					delete Recv[ndx];
					Recv[ndx] = NULL;
				}		  
			}
		} 
	}	break;
	case CLIP_TYPE: {
		BYTE sendid = ((BYTE) buffer[SEND_POS]);
		// If data is for Pointer Window
		if (PointerClip != NULL) {
			if (PointerClip->m_sendid == sendid) {
				// Check if correct packet
				if ( *((LPWORD) (buffer+TRANSNO)) == PointerClip->m_recvpacket) {
					// Create window if 1st packet
					if (PointerClip->m_recvpacket == 0)
						::PostMessage(g_ListHwnd, WM_CREATECLIPWND, MAX_FILES, MAX_FILES);
					// ACK packet as soon as possible
					PointerClip->m_recvpacket++;
					SendClipAck(PointerClip->m_sendid, PointerClip->m_recvpacket);
					// Copy to bitmap buffer
					DWORD Len2 = *((LPDWORD) (buffer + LEN_POS)) & 0x000FFFFF;
					memcpy((LPBYTE) PointerClip->m_buff + PointerClip->m_recvlen,
						   (LPBYTE) buffer + HEADER_LENGTH, Len2);
					// Update window
					::PostMessage(g_ListHwnd, WM_UPDATECLIP, MAX_FILES, (DWORD) Len2);
					PointerClip->m_recvlen += Len2;	
					//if (PointerClip->m_recvlen >= PointerClip->m_TotalLen){}
				}
			}
		}

		// Find position in ClipRecv[MAX_FILES] table
		BYTE m1, ndx1 = MAX_FILES;
		for (m1 = 0; m1 < MAX_FILES; m1++) {
			if (ClipRecv[m1] != NULL)
				if (ClipRecv[m1]->m_sendid == sendid)
					ndx1 = m1;	
		}
		if (ClipRecv[ndx1]==NULL || ndx1 == MAX_FILES)
			break;
		// Check if correct packet
		if ( *((LPWORD) (buffer+TRANSNO)) == ClipRecv[ndx1]->m_recvpacket) {
			// Create window if 1st packet
			if (ClipRecv[ndx1]->m_recvpacket == 0)
				::PostMessage(g_ListHwnd, WM_CREATECLIPWND, (BYTE)ndx1, (BYTE)ndx1);
			// ACK packet as soon as possible
			ClipRecv[ndx1]->m_recvpacket++;
			SendClipAck(ClipRecv[ndx1]->m_sendid, ClipRecv[ndx1]->m_recvpacket);
			// Copy to bitmap buffer
			DWORD Len1 = *((LPDWORD) (buffer + LEN_POS)) & 0x000FFFFF;
			memcpy((LPBYTE) ClipRecv[ndx1]->m_buff + ClipRecv[ndx1]->m_recvlen,
				   (LPBYTE) buffer + HEADER_LENGTH, Len1);
			// Update Window
			::PostMessage(g_ListHwnd, WM_UPDATECLIP, (BYTE) ndx1, (DWORD) Len1);
			ClipRecv[ndx1]->m_recvlen += Len1;
			
			//if (ClipRecv[ndx1]->m_recvlen >= ClipRecv[ndx1]->m_TotalLen){}		  
		}
	}	break;
	case ADD_TXT:
		AddTxtObj(buffer);
		break;
	case CHG_TXT:
		ChgTxt(buffer);
		break;
	default:
		break;
	}//switch
}


///////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////
// SEARCH FUNCTIONS
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// GetNameByID()
///////////////////////////////////////////////////////////////////////////
// Finds a client's name using its id
///////////////////////////////////////////////////////////////////////////
CString CClientDoc::GetNameByID(BYTE UserID)
{
	CString notfound("");
	EnterCriticalSection(&m_csusr);
	for (POSITION pos = m_userslist.GetHeadPosition(); pos != NULL;) {
		USER* User = (USER*) m_userslist.GetNext(pos);
		if (UserID == User->UserID) {
			LeaveCriticalSection(&m_csusr);
			return ((CString) User->UserName);
		}
	}
	LeaveCriticalSection(&m_csusr);
	return notfound;
}


///////////////////////////////////////////////////////////////////////////
// GetIDByName()
///////////////////////////////////////////////////////////////////////////
// Finds a client's id using its name
///////////////////////////////////////////////////////////////////////////
BYTE CClientDoc::GetIDByName(LPCTSTR Name)
{
	EnterCriticalSection(&m_csusr);
	for (POSITION pos = m_userslist.GetHeadPosition(); pos != NULL;) {
		USER* User = (USER*) m_userslist.GetNext(pos);
		if (strcmp(Name, User->UserName) == 0) {
			LeaveCriticalSection(&m_csusr);
			return (User->UserID);
		}
	}
	LeaveCriticalSection(&m_csusr);
	if (strcmp(m_strgroup, Name) == 0)	// Selected Group icon => Broadcast!!!
		return ALLGROUP;
	return NO_ID;
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
//Functions for destruction of lists (involving usernames and groups)
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// DumpOldUsrlist()
///////////////////////////////////////////////////////////////////////////
// Destroys list of Users (called when list is out of scope or no
// longer valid)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DumpOldUsrlist()
{
	TRACE("Old List of users is being destroyed\n");
	EnterCriticalSection(&m_csusr);
	while (!m_userslist.IsEmpty())
	{
		USER* User = (USER*) m_userslist.RemoveHead();
		free(User);
		TRACE("User destructed\n");
	}
	LeaveCriticalSection(&m_csusr);
	
}


///////////////////////////////////////////////////////////////////////////
// DumpOldGroupList()
///////////////////////////////////////////////////////////////////////////
// Destroys list of Group (called when list is out of scope or no
// longer valid)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DestroyOldGroupList()
{
	TRACE("Old list of groups is being destroyed\n"); 
	EnterCriticalSection(&m_csgr);
	while (!m_grouplist.IsEmpty())
	{
		GROUP* Group = (GROUP*) m_grouplist.RemoveHead();
		free(Group);
		TRACE("Group destructed\n");
	}
	LeaveCriticalSection(&m_csgr);	
}



///////////////////////////////////////////////////////////////////////////
// DumpUserDB()
///////////////////////////////////////////////////////////////////////////
// Destroys Database of all Users (called when DB is out of scope or no
// longer valid or necessary)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::DestroyUserDB()
{
	while (!m_userDBList.IsEmpty())
	{
		USERDB* User = (USERDB*) m_userDBList.RemoveHead();
		free(User);
	}
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// GROUP MENU Commands
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// OnGroupsDisjoin()
///////////////////////////////////////////////////////////////////////////
// Called when a client chooses to disjoin group and performs
// tasks consequent to a disjoin procedure (chiefly destruction of objects
// that are meaninful only within a group)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnGroupsDisjoin() 
{
	CDisjoinDialog Dialog; int ret;
	if (m_bDisConf)
		ret = Dialog.DoModal();
	else
		ret = IDOK;
	if (ret == IDOK) {
		m_bjoined = FALSE;
		SendDisjoinMsg(m_strgroup); // send msg to server to disjoin
		AfxMessageBox(IDS_DISJOIN);
		m_strgroup.Empty();
		
		// Update userlist list-box
		while(!m_userslist.IsEmpty()) {	
			USER* User = (USER*) m_userslist.RemoveHead();
			free(User);
		}

		// Destroy whiteboard elements
		POSITION pos = m_objects.GetHeadPosition();
		while (pos != NULL)
			delete m_objects.GetNext(pos);
		m_objects.RemoveAll();

		TRACE("NUMBER OF OBJECTS:%d\n", m_objects.GetCount());
		
		if (m_pDrWnd != NULL) {
			m_pDrWnd->DestroyWindow();
			m_pDrWnd = NULL;
		}

		SetModifiedFlag(TRUE);
		UpdateAllViews(NULL);
		SetModifiedFlag(FALSE);
	}
}


///////////////////////////////////////////////////////////////////////////
// On GroupsGet()
///////////////////////////////////////////////////////////////////////////
// Issues a request to get a group list calling function to send
// the proper msg
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnGroupsGet() 
{
	SendMsg(LIST_GROUPS, SERVER_ID); //issue request to get a list of available groups 
}


///////////////////////////////////////////////////////////////////////////
// OnGroupsJoin()
///////////////////////////////////////////////////////////////////////////
// Displays Join Dialog and lets the Dialog objects to perform
// the join tasks
/////////////////////////////////////////////////////////////////////////// 
void CClientDoc::OnGroupsJoin() 
{
	CJoinDialog Dialog(this, NULL);
	TRACE("Join Groups Dialog\n");

	int ret = Dialog.DoModal();
	TRACE("Dialog returned %d\n", ret);
}


///////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////
// VIDEO MENU Commands
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////



///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoInfo()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Displayes information about sent, received and played frames
// ///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoInfo()
{
	icmgr->DriverInfo();
	CString msg;
	msg.Format("captured %d - sent %d - received %d - played %d", g_frames, g_framessent, g_framesrecv, g_framesplayed);
	AfxMessageBox(msg);
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoCaptureasAvi()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Captures Video in an AVI File
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoCaptureasAvi() 
{
	CapWnd->CaptureFile();
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoCaptureasDib()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Captures Video as DIB
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoCaptureasDib() 
{
	CapWnd->CaptureDIB();
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoCaptureasWav()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoCaptureasWav() 
{
	// TODO: Add your command handler code here
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoClose()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Closes Video Driver and destroys video window
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoClose() 
{
	CapWnd->DestroyWindow();
	m_bVideoOpen = FALSE;
	g_frames = 0; g_framessent = 0;
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoOpen()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Connects video driver and constucts video window
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoOpen() 
{
	CapWnd = new CCapture("Video Window", WS_OVERLAPPEDWINDOW | WS_THICKFRAME, 0, 0, 384, 288, 
						((CListClientView*)m_viewList.GetHead())->GetSafeHwnd(), 0);
	CapWnd->ConnectDriver(0);
	m_bVideoOpen = TRUE;
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoSetcaptureparameters()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Displays Capture parameters dialog
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoSetcaptureparameters() 
{
	CapWnd->DlgVideoCaptureParms();	
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoDisplay()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Displays video display dialog
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoVideodisplay() 
{
	CapWnd->DlgVideoDisplay();
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoVideoformat()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Displays video format dialog
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoVideoformat() 
{
	CapWnd->DlgVideoFormat();
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoVideoSource()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Displays video source dialog
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoVideosource() 
{
	CapWnd->DlgVideoSource();
}


///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////
// VIDEO PLAY Pop-Up Menu Commands
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoPlayAvi()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Plays an AVI file
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoPlayAvi() 
{
	static char filter[] = "AVI Files (*.AVI)|*.AVI|All Files (*.*)|*.*||";
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					filter, NULL);
	Dlg.m_ofn.lpstrTitle = "Play AVI File";

	int ret=Dlg.DoModal();
		if (ret==IDOK)
			//g_ListHwnd = ((CClientView*) m_viewList.GetHead())->GetSafeHwnd();
			MCIWndCreate(NULL, AfxGetApp()->m_hInstance, MCIWNDF_SHOWALL, Dlg.GetPathName());
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnVideoPlayWAV()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Plays a WAV file
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnVideoPlayWav() 
{
	CFileDialog Dlg(TRUE, NULL, NULL, OFN_HIDEREADONLY|OFN_OVERWRITEPROMPT, 
					"WAV Files (*.WAV)|*.WAV|All Files (*.*)|*.*||", NULL);
	Dlg.m_ofn.lpstrTitle = "Play WAV File";

	int ret=Dlg.DoModal();
		if (ret==IDOK)
			//g_ListHwnd = ((CClientView*) m_viewList.GetHead())->GetSafeHwnd();
			MCIWndCreate(NULL, AfxGetApp()->m_hInstance, MCIWNDF_SHOWALL, Dlg.GetPathName());
}



///////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////
// USER MENU SEND VIDEO
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnUserSendvideo()
///////////////////////////////////////////////////////////////////////////
// PURPOSE:  Begin a thread in order to send video to another client
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnUserSendvideo() 
{
	BYTE usrID = GetIDByName((LPCTSTR) ((CListClientView*) m_viewList.GetHead())->m_strUser);
	if (usrID != NO_ID) {
		m_VideoRecvID = usrID;
		AfxBeginThread(VideoThreadProc,this,THREAD_PRIORITY_NORMAL);
	}
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// FUNCTION: VideoThreadProc()
// PURPOSE:  Controling function for the thread that captures and sends
//			 video to a client
// PARAMETER: A CClientDoc pointer 		
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
UINT VideoThreadProc(LPVOID pParam)
{
	CClientDoc* pDoc = (CClientDoc*) pParam;
	pDoc->CapWnd->SetErrorCallBack(OnCaptureError);
	pDoc->CapWnd->SetVideoCallBack(OnVideoFrame);
	pDoc->CapWnd->SetYieldCallBack(OnYield);
	pDoc->CapWnd->CaptureMem();
	//AfxMessageBox("CaptureMem returned");
	TRACE("CaptureMem returned\n");
	return 0;
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Update Menu Items Functions
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnUpdateNetworkConnect(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(!m_bconnected && !m_bTryConnect);
}

void CClientDoc::OnUpdateNetworkDisconnect(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bconnected && !m_bjoined);
}

void CClientDoc::OnUpdateNetworkSendpacket(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bconnected);
}

void CClientDoc::OnUpdateGroupsDisjoin(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bjoined && m_bconnected);
}

void CClientDoc::OnUpdateGroupsGet(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bconnected);
}

void CClientDoc::OnUpdateGroupsJoin(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(!m_bjoined && m_bconnected);
}

void CClientDoc::OnUpdateVideoCaptureasAvi(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoCaptureasDib(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoCaptureasWav(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoVideosource(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoVideoformat(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoVideodisplay(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoSetcaptureparameters(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoClose(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen);
}

void CClientDoc::OnUpdateVideoOpen(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(!m_bVideoOpen);
}

void CClientDoc::OnUpdateUserSendvideo(CCmdUI* pCmdUI) 
{
	pCmdUI->Enable(m_bVideoOpen && m_bjoined && m_bconnected);	
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Video Capture CALLBACK Functions
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// FUNCTION: OnYield
// PUPROSE:	 Allows message processing while callback functions work	
///////////////////////////////////////////////////////////////////////////
LRESULT CALLBACK OnYield(HWND hWnd)
{
	do {
		;
	} while(ShoutBlockingHook());
	return(TRUE);
}

int ShoutBlockingHook (void)
{
	MSG msg;
	int ret=PeekMessage(&msg, NULL, 0, 0, PM_REMOVE);
	if (ret) {
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}
	return ret;
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnVideoFrame()
// PUPROSE:    Forms Video packet and sends it
// PARAMETERS: Handle hWnd, lpVHdr structure containing video packet info  
///////////////////////////////////////////////////////////////////////////
LRESULT CALLBACK OnVideoFrame(HWND hWnd, LPVIDEOHDR lpVHdr)
{
	LPBYTE VideoPack = NULL;
	DWORD VideoLen = lpVHdr->dwBytesUsed; DWORD i;
	//do {
	//	;
	//} while(ShoutBlockingHook());

	// SEND AT ONCE
	VideoPack = (LPBYTE) MemAlloc(NULL, VideoLen+HEADER_LENGTH, MEM_COMMIT, PAGE_READWRITE);
	if (VideoPack == NULL)
		return (TRUE);

	for (i = 0; i < VideoLen + HEADER_LENGTH; i++)
		VideoPack[i] = 0;
	VideoPack[SEND_POS] = g_pDoc->m_id;
	VideoPack[RECV_POS] = g_pDoc->m_VideoRecvID;
	VideoPack[TYPE_POS] = VIDEO_TYPE;
	*((LPDWORD) (VideoPack + LEN_POS)) = VideoLen;
	memcpy((LPBYTE) (VideoPack+HEADER_LENGTH), (LPBYTE) lpVHdr->lpData, VideoLen);
	
	g_frames++;
	
	//g_pDoc->m_pSocket->BufferOut->AddTail((LPSTR)VideoPack, VideoLen + HEADER_LENGTH, NO_COMP);
	//MemFree(VideoPack, HEADER_LENGTH + VideoLen, MEM_DECOMMIT|MEM_RELEASE);
	
	if (g_pDoc->m_pSocket != NULL) {		// if socket not closed
		EnterCriticalSection(&(g_pDoc->m_pSocket->m_csLeft));
		if (g_pDoc->m_pSocket->m_LeftData == 0)
		{
			g_framessent++;
			g_pDoc->m_pSocket->m_SendDataBuffer = (LPSTR) VideoPack;
			g_pDoc->m_pSocket->m_SendLength = VideoLen + HEADER_LENGTH;
			g_pDoc->m_pSocket->m_LeftData = VideoLen + HEADER_LENGTH;
			g_pDoc->m_pSocket->SendData();
		}
		else
			MemFree(VideoPack, HEADER_LENGTH + VideoLen, MEM_DECOMMIT|MEM_RELEASE);
		LeaveCriticalSection(&(g_pDoc->m_pSocket->m_csLeft));
	}
	else
		MemFree(VideoPack, HEADER_LENGTH + VideoLen, MEM_DECOMMIT|MEM_RELEASE);
	
	return(TRUE);
}

LRESULT CALLBACK OnCaptureError(HWND hwnd, int nID, LPCSTR lpsz)
{
	//AfxMessageBox(lpsz);
	return(TRUE);
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// SERVER REMOTE ADMINISTRATION MESSAGES
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   SendAddUsr()
// PUPROSE:	   Sends ADD_USR msg to add user 
// PARAMETERS: const char* entry containing user-name and password
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendAddUsr(const char* entry)
{
	BYTE msg[MSG_LENGTH]; int i;
	for (i=0; i<MSG_LENGTH; i++) //initialisation
		msg[i]=0;   
 	TRACE("Entry in message %s \n", entry);
	msg[PAT_BEG] = MSG_ID;      
	msg[PAT_END] = MSG_ID;
	msg[ID] = ADD_USR;         
	msg[SEND] = m_id;
	msg[RECV] = 0;
	for (i=0; i < 26; i++)
		msg[i+4] = (BYTE) entry[i];
		
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
	TRACE("message has been added to buffertail\n");
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   SendDelUsr()
// PUPROSE:	   Sends DEL_USR msg to delete user
// PARAMETERS: const char* UserName the name of user to delete 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendDelUsr(const char* UserName)
{
	BYTE msg[MSG_LENGTH]; int i;
	for (i=0; i<MSG_LENGTH; i++) //initialisation
		msg[i]=0;   
 	msg[PAT_BEG] = MSG_ID;     
	msg[PAT_END] = MSG_ID;
	msg[ID] = DEL_USR;         
	msg[SEND] = m_id;
	msg[RECV] = 0;
	for (i = 0; i < 8 && UserName[i] != '\0'; i++)
		msg[i+4] = UserName[i];
		
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
	TRACE("message has been added to buffertail\n");
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION:   SendModUsr()
// PUPROSE:	   Sends MOD_USR msg to modify user 
// PARAMETERS: const char* entry containing modified user-name and password
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendModUsr(const char* entry)
{
	BYTE msg[MSG_LENGTH]; int i;
	for (i=0; i<MSG_LENGTH; i++) //initialisation
		msg[i]=0;   
 	TRACE("Entry in message %s \n", entry);
	msg[PAT_BEG] = MSG_ID;      
	msg[PAT_END] = MSG_ID;
	msg[ID] = MOD_USR;         
	msg[SEND] = m_id;
	msg[RECV] = 0;
	for (i=0; i<26; i++)
		msg[i+4] = (BYTE) entry[i];
		
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
	TRACE("message has been added to buffertail\n");
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION:   SendAddGroup()
// PUPROSE:	   Sends ADD_GROUP msg to add user 
// PARAMETERS: const char* name containing new group's name
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendAddGroup(const char* name)
{
	BYTE msg[MSG_LENGTH]; int i;
	for (i=0; i<MSG_LENGTH; i++) //initialisation
		msg[i]=0;   
 	TRACE("String in message %s \n", name);
	msg[PAT_BEG] = MSG_ID;      
	msg[PAT_END] = MSG_ID;
	msg[ID] = ADD_GROUP;         
	msg[SEND] = m_id;
	msg[RECV] = 0;
	for (i=0; i<17; i++)
		msg[i+4] = (BYTE) name[i];
	
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
	TRACE("message has been added to buffertail\n");
}

 
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   SaveModified()
// PUPROSE:	   Declares that Document has changed
///////////////////////////////////////////////////////////////////////////
BOOL CClientDoc::SaveModified() 
{
	SetModifiedFlag(FALSE);
	return TRUE; //CDocument::SaveModified();
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// AUDIO MENU
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnAudioEnableAudio()
// PUPROSE:	   Enables Audio Recording and Transmission
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnAudioEnableaudio() 
{
	// Enable Audio - Start Recording
	if (!m_bAudio) {
		MMRESULT res = m_pAudioIn->AudioInOpen();
		switch (res) {
		case MMSYSERR_NOERROR:  TRACE("Format OK\n"); 
			m_bAudio = TRUE; 
			break;
		case MMSYSERR_NODRIVER:	TRACE("Audio-In Driver does not exist\n");
		case WAVERR_BADFORMAT:	TRACE("Bad Format\n"); 
			AfxMessageBox("There is no Audio Device able to record in this format"); 
			break;
		case MMSYSERR_ALLOCATED:TRACE("Audio Device Allocated\n"); 
			AfxMessageBox("Audio-In Device already allocated.\nCheck to see if it is used by another application."); 
			break;
		case MMSYSERR_NOMEM:	TRACE("Not enough memory\n"); 
			AfxMessageBox("Not enough memory to open Audio Device.");
			break;
		case MMSYSERR_BADDEVICEID:	TRACE("Bad ID\n"); 
			break;
		}
	}
	// Disable Audio - Stop Recording
	else {
		if (m_pAudioIn->AudioInClose())
			m_bAudio = FALSE;
	}
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnAudioSetaudioparameters()
// PUPROSE:	   Sets Audio parameters 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnAudioSetaudioparameters() 
{
	m_pAudioIn->AudioParamsDlg();	
}


void CClientDoc::OnUpdateAudioEnableaudio(CCmdUI* pCmdUI) 
{
	pCmdUI->SetCheck(m_bAudio);	
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:   OnAudioEnableplayback()
// PUPROSE:	   Enables Audio and starts playback. Checks for errors at first
///////////////////////////////////////////////////////////////////////////
void CClientDoc::OnAudioEnableplayback() 
{
	// Enable Audio - Start Playback
	if (!m_bAudioPlay) {
		MMRESULT res = m_pAudioOut->AudioOutOpen();
		switch (res) {
		case MMSYSERR_NOERROR: TRACE("Format OK\n"); 
			m_bAudioPlay = TRUE; 
			break;
		case MMSYSERR_NODRIVER:TRACE("Driver does not exist\n");
		case WAVERR_BADFORMAT: TRACE("Bad Format\n"); 
			AfxMessageBox("There is no Audio Device able to play in this format"); 
			break;
		case MMSYSERR_ALLOCATED:	
			TRACE("Device Allocated\n"); 
			AfxMessageBox("Audio-Out Device already allocated.\nCheck to see if it is used by another application."); 
			break;
		case MMSYSERR_NOMEM:		
			TRACE("Not enough memory\n"); 
			AfxMessageBox("Not enough memory to open Audio Device.");
			break;
		case MMSYSERR_BADDEVICEID:	TRACE("Bad ID\n"); 
			break;
		}
	}
	// Disable Audio - Stop Playback
	else {
		if (m_pAudioOut->AudioOutClose())
			m_bAudioPlay = FALSE;
	}
}

void CClientDoc::OnUpdateAudioEnableplayback(CCmdUI* pCmdUI) 
{
	pCmdUI->SetCheck(m_bAudioPlay);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:  GetTimeStamp()
// PURPOSE:   Calculates time stamp for transmitted packets
///////////////////////////////////////////////////////////////////////////
time_t CClientDoc::GetTimeStamp()
{
	return( m_TimeMark + NowSecs() - m_MarkArrived );
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// WHITEBOARD FUNCTIONS - Implementation
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// FUNCTION:  Draw()
// PURPOSE:   Calls functions to Draw all existing whiteboard objects
//			  on the whiteboard window according to each object's type			
///////////////////////////////////////////////////////////////////////////
void CClientDoc::Draw(CDC* pDC, CDrWnd* pDrWnd)
{
	TRACE("ClientDoc Draw called\n");
	EnterCriticalSection(&m_csdr);
	POSITION pos = m_objects.GetHeadPosition();
	while (pos != NULL)
	{
		TRACE("Num of Objects %d\n", m_objects.GetCount());
		CDrawObj* pObj = m_objects.GetNext(pos);
		TRACE("Object's position top %ld \n", pObj->m_position.top);
		TRACE("Object type: %d \n", pObj->m_type);
		if (pObj->m_type == 1 || pObj->m_type == 2 || 
			pObj->m_type == 3 || pObj->m_type == 4 )
		{
			pObj->Draw(pDC);
			if (pDrWnd->m_bActive && !pDC->IsPrinting() && pDrWnd->IsSelected(pObj))
				pObj->DrawTracker(pDC, CDrawObj::selected);
		}
		
		if (pObj->m_type == 5)
		{
			CTextObj* pTxt = (CTextObj*) pObj;
			pTxt->Draw(pDC);
		}
		
	}
	LeaveCriticalSection(&m_csdr);
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION:  Add()
// PURPOSE:   Adds a drawing object to whiteboard objects list
//			  and instigates sending of addition message when necessary 	 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::Add(CDrawObj* pObj)
{
	EnterCriticalSection(&m_csdr);
	m_objects.AddTail(pObj);
	LeaveCriticalSection(&m_csdr);

	if (pObj->m_type != TEXT_OBJ)
		SendAddObj((CDrawRect*) pObj);
	else
		SendAddTxtObj((CTextObj*) pObj);

	pObj->m_pDocument = this;
	SetModifiedFlag();
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:  Remove()
// PURPOSE:   Removes a drawing object from whiteboard objects list
//			  and instigates sending of removal message when necessary 	 
///////////////////////////////////////////////////////////////////////////
void CClientDoc::Remove(CDrawObj* pObj)
{
	// Find and remove from document
	EnterCriticalSection(&m_csdr);
	POSITION pos = m_objects.Find(pObj);
	if (pos != NULL)
		m_objects.RemoveAt(pos);
	LeaveCriticalSection(&m_csdr);

	if (pObj->m_type != TEXT_OBJ)
		SendRemvObj((CDrawRect*) pObj, NULL);
	else
		SendRemvObj(NULL,(CTextObj*) pObj);
	
	// set document modified flag
	SetModifiedFlag();
	m_pDrWnd->Remove(pObj);	
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION:  ObjectAt()
// PURPOSE:   Tests if some drawing object exists at a specified point
////////////////////////////////////////////////////////////////////////////
CDrawObj* CClientDoc::ObjectAt(const CPoint& point)
{
	CRect rect(point, CSize(1, 1));
	POSITION pos = m_objects.GetTailPosition();
	while (pos != NULL)
	{
		CDrawObj* pObj = m_objects.GetPrev(pos);
		if (pObj->Intersects(rect))
			return pObj;
	}
	return NULL;
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// VIEW MENU COMMAND
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// FUNCTION:  OnViewWhiteboard()
// PURPOSE:   Displays Whiteboard window if not visible
////////////////////////////////////////////////////////////////////////////
void CClientDoc::OnViewWhiteboard() 
{
	if (m_pDrWnd == NULL){
		m_pDrWnd = new CDrWnd(this);
		CMenu Menu;
		Menu.LoadMenu(IDR_MENUDR);

		m_pDrWnd->CreateEx(0, AfxRegisterWndClass(CS_HREDRAW|CS_VREDRAW|CS_DBLCLKS),
			    		   "Whiteboard", WS_OVERLAPPEDWINDOW, 0, 100, 400, 350, NULL, Menu.m_hMenu, NULL);	
		Menu.Detach();
			
		m_pDrWnd->ShowWindow(SW_SHOW);
		m_pDrWnd->UpdateWindow();
		m_pDrWnd->InvalidateRect(NULL, TRUE);
	}	
	else {
		m_pDrWnd->DestroyWindow();
		m_pDrWnd = NULL;
	}
}

void CClientDoc::OnUpdateViewWhiteboard(CCmdUI* pCmdUI) 
{
	BOOL b = (m_pDrWnd != NULL);
	pCmdUI->SetCheck(b);
	pCmdUI->Enable(m_bconnected && m_bjoined);
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Functions for Sending Whiteboard Messages
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendWhBrdReq
// PURPOSE:  Sends a WHITEBOARD_REQ message to server issuing a request
//			 to get all whiteboard objects
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendWhBrdReq()
{
	BYTE msg[MSG_LENGTH];
	
	UINT i;
	for (i=0; i<MSG_LENGTH; ++i) //initialisation
		msg[i]=0;   

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = WHITEBOARD_REQ;
	msg[SEND] = m_id;
	msg[RECV] = SERVER_ID;

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendAddObj()
// PURPOSE:  Sends an ADD_OBJECT message to add a new drawing object
//			 to the group's whiteboard
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendAddObj(CDrawRect* pObj)
{
	TRACE("Msg for Object addition sent\n");
	BYTE msg[MSG_LENGTH];

	UINT i;
	for (i=0; i<MSG_LENGTH; ++i) //initialisation
		msg[i]=0;   

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = ADD_OBJECT;
	msg[SEND] = m_id;
	msg[RECV] = SERVER_ID;
	
	msg[OBJECT_TYPE_POS] = pObj->m_type;
	//send object's position
	*((LPDWORD) (msg + 5)) = pObj->m_position.top;		//4 bytes
	*((LPDWORD) (msg + 9)) = pObj->m_position.left;		//4 bytes
	*((LPDWORD) (msg + 13)) = pObj->m_position.bottom;	//4 bytes
	*((LPDWORD) (msg + 17)) = pObj->m_position.right;	//2 bytes
	//send drawing pen info
	msg[21] = pObj->m_bPen;
	*((LPWORD) (msg+22)) = pObj->m_logpen.lopnStyle;
	*((LPDWORD) (msg+24)) = pObj->m_logpen.lopnWidth.x;
	*((LPDWORD) (msg+28)) = pObj->m_logpen.lopnWidth.y;
	*((LPDWORD) (msg+32)) = pObj->m_logpen.lopnColor;
	msg[36] = pObj->m_bBrush;

	// send brush
	*((LPWORD) (msg+37)) = pObj->m_logbrush.lbStyle;
	*((LPDWORD)(msg+39)) = pObj->m_logbrush.lbColor;
	*((LPDWORD)(msg+43)) = pObj->m_logbrush.lbHatch;
		
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendRemvObj()
// PURPOSE:  Sends an REMOVE_OBJECT message to remove a drawing object
//			 from the group's whiteboard
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendRemvObj(CDrawRect* pObj, CTextObj* pTxt)
{
	BYTE msg[MSG_LENGTH];

	UINT i;
	for (i=0; i<MSG_LENGTH; ++i) //initialisation
		msg[i]=0;   

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = REMOVE_OBJECT;
	msg[SEND] = m_id;
	msg[RECV] = SERVER_ID;
	
	if (pTxt == NULL) {	//other object than text
		msg[OBJECT_TYPE_POS] = pObj->m_type;
		//send object's position
		*((LPDWORD) (msg + 5)) = pObj->m_position.top;		//4 bytes
		*((LPDWORD) (msg + 9)) = pObj->m_position.left;		//4 bytes
		*((LPDWORD) (msg + 13)) = pObj->m_position.bottom;	//4 bytes
		*((LPDWORD) (msg + 17)) = pObj->m_position.right;	//2 bytes
	}
	else {			//send text's position
		msg[OBJECT_TYPE_POS] = pTxt->m_type;
		*((LPDWORD) (msg + 5)) = pTxt->m_pos.x; //4 bytes
		*((LPDWORD) (msg + 9)) = pTxt->m_pos.y; //4 bytes
	}

	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendObjMove()
// PURPOSE:  Sends a MOVE_OBJECT message to move a drawing object
//			 on the group's whiteboard
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendObjMove(CRect Oldpos, CRect Newpos, BYTE type)
{
	TRACE("Msg for Object move sent\n");
	BYTE msg[MSG_LENGTH];

	UINT i;
	for (i=0; i<MSG_LENGTH; ++i) //initialisation
		msg[i]=0;   

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = MOVE_OBJECT;
	msg[SEND] = m_id;
	msg[RECV] = SERVER_ID;
	msg[OBJECT_TYPE_POS] = type;

	if (type != TEXT_OBJ) {		// non-text object
		//send old position
		*((LPDWORD) (msg + 5)) = Oldpos.top;	//4 bytes
		*((LPDWORD) (msg + 9)) = Oldpos.left;	//4 bytes
		*((LPDWORD) (msg + 13)) = Oldpos.bottom;//4 bytes
		*((LPDWORD) (msg + 17)) = Oldpos.right;	//2 bytes

		//send new position
		*((LPDWORD) (msg + 21)) = Newpos.top;	//4 bytes
		*((LPDWORD) (msg + 25)) = Newpos.left;	//4 bytes
		*((LPDWORD) (msg + 29)) = Newpos.bottom;//4 bytes
		*((LPDWORD) (msg + 33)) = Newpos.right;	//2 bytes
	}
	else {		// text object
		*((LPDWORD) (msg + 5)) = Newpos.left;	//4 bytes
		*((LPDWORD) (msg + 9)) = Newpos.top;	//4 bytes
		*((LPDWORD) (msg + 13)) = Newpos.right; //4 bytes
		*((LPDWORD) (msg + 17)) = Newpos.bottom;//2 bytes
	}
	
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendObjColor()
// PURPOSE:  Sends an COLOR_OBJECT message to change either the object's
//			 color (brush), or the object's drawing line (pen)
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendObjColor(CRect position, BYTE type, COLORREF brcolor, COLORREF pncolor)
{
	BYTE msg[MSG_LENGTH];

	UINT i;
	for (i=0; i<MSG_LENGTH; ++i) //initialisation
		msg[i]=0;   

	msg[PAT_BEG] = MSG_ID;
	msg[PAT_END] = MSG_ID;
	msg[ID] = COLOR_OBJECT;
	msg[SEND] = m_id;
	msg[RECV] = SERVER_ID;
	msg[OBJECT_TYPE_POS] = type;

	//send object's position
	*((LPDWORD) (msg + 5)) = position.top; 
	*((LPDWORD) (msg + 9)) = position.left; 
	*((LPDWORD) (msg + 13)) = position.bottom;
	*((LPDWORD) (msg + 17)) = position.right; 
	//send new color
	*((LPDWORD) (msg + 21)) = brcolor;
	*((LPDWORD) (msg + 25)) = pncolor;
			
	m_pSocket->MsgBufferOut->AddTail((LPSTR) msg, MSG_LENGTH, NO_COMP);
}

///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Functions for Sending Whiteboard Text Packets
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendAddTxtObj()
// PURPOSE:  Sends an ADD_TXT packet to add a new text object
//			 to the group's whiteboard
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendAddTxtObj(CTextObj* pTxt)
{
	TRACE("SendAddTxtObj called\n");
	LPBYTE TextPacket; DWORD Len, i, TxtLen;
	TxtLen = (DWORD) pTxt->m_strtext.GetLength();

	// TxtLen bytes text, 8 bytes position, 1 byte object type
	Len = max ((DWORD)(TxtLen + 9) , MSG_LENGTH-HEADER_LENGTH);
	
	TextPacket = (LPBYTE) MemAlloc(NULL, HEADER_LENGTH + Len, MEM_COMMIT, PAGE_READWRITE);
	for (i = 0; i < HEADER_LENGTH + Len; i++)
		TextPacket[i] = 0;

	// Form packet header
	TextPacket[SEND_POS] = m_id;
	TextPacket[RECV_POS] = SERVER_ID;
	TextPacket[TYPE_POS] = ADD_TXT;
	*((LPDWORD) (TextPacket + LEN_POS)) = Len; 
	// Packet data
	TextPacket[HEADER_LENGTH] = pTxt->m_type;
	*((LPDWORD) (TextPacket + HEADER_LENGTH + 1)) = pTxt->m_pos.x;
	*((LPDWORD) (TextPacket + HEADER_LENGTH + 5)) = pTxt->m_pos.y;
	LPCTSTR temp = (LPCTSTR) pTxt->m_strtext;
	for (i = 0; i < TxtLen; i++)
		TextPacket[HEADER_LENGTH + i + 9] = temp[i];
	// No Compression because it will be processed by the server	
	m_pSocket->BufferOut->AddTail((LPSTR) TextPacket, HEADER_LENGTH+Len, NO_COMP);
	MemFree(TextPacket, HEADER_LENGTH + Len, MEM_DECOMMIT|MEM_RELEASE);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: SendChgTxtObj()
// PURPOSE:  Sends an CHG_TXT packet to change a text's  object text
///////////////////////////////////////////////////////////////////////////
void CClientDoc::SendChgTxtObj(CTextObj* pTxt)
{
	TRACE("SendChgTxtObj called\n");
	LPBYTE TextPacket; DWORD Len, i, TxtLen;
	TxtLen = (DWORD) pTxt->m_strtext.GetLength();

	// TxtLen bytes text, 1 byte object type, 8 bytes position
	Len = max ((DWORD)(TxtLen + 9) , MSG_LENGTH-HEADER_LENGTH);
	
	TextPacket = (LPBYTE) MemAlloc(NULL, HEADER_LENGTH + Len, MEM_COMMIT, PAGE_READWRITE);
	for (i = 0; i < HEADER_LENGTH + Len; i++)
		TextPacket[i] = 0;

	// Form packet header
	TextPacket[SEND_POS] = m_id;
	TextPacket[RECV_POS] = SERVER_ID;
	TextPacket[TYPE_POS] = CHG_TXT;
	*((LPDWORD) (TextPacket + LEN_POS)) = Len; 
	// Packet Data
	TextPacket[HEADER_LENGTH] = pTxt->m_type;
	*((LPDWORD) (TextPacket + HEADER_LENGTH + 1)) = pTxt->m_pos.x;
	*((LPDWORD) (TextPacket + HEADER_LENGTH + 5)) = pTxt->m_pos.y;
	LPCTSTR temp = (LPCTSTR) pTxt->m_strtext;
	for (i = 0; i < TxtLen; i++)
		TextPacket[HEADER_LENGTH + i + 9] = temp[i];
	// No Compression because it will be processed by the server
	m_pSocket->BufferOut->AddTail((LPSTR) TextPacket, HEADER_LENGTH + Len, NO_COMP);
	MemFree(TextPacket, HEADER_LENGTH + Len, MEM_DECOMMIT|MEM_RELEASE);
}


///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Whiteboard operations instigated by Message Processing
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
// FUNCTION: AddObject()
// PURPOSE:  Called by ProcessMsg on reception of an ADD_OBJECT message
//			 Performs tasks related to object addition
///////////////////////////////////////////////////////////////////////////
void CClientDoc::AddObject(LPSTR msg)
{
	CRect rect;
	CDrawRect* pObj;
	
	// get object's position
	rect.top = (LONG) (*((LPDWORD) (msg + 5)));
	rect.left =(LONG) (*((LPDWORD) (msg + 9))); 
	rect.bottom= (LONG) (*((LPDWORD) (msg + 13)));
	rect.right = (LONG) (*((LPDWORD) (msg + 17)));

	// construct object
	pObj = new CDrawRect(rect);

	switch((BYTE) msg[OBJECT_TYPE_POS])
	{
			case LINE:
				pObj->m_nShape = CDrawRect::line;
				break;
			case RECTANG:
				pObj->m_nShape = CDrawRect::rectangle;
				break;
			case ROUND_RECT:
				pObj->m_nShape = CDrawRect::roundRectangle;
				break;			
			case ELLIPSE:
				pObj->m_nShape = CDrawRect::ellipse;
				break;			
	}

	pObj->m_position = CRect(rect);
	pObj->m_type = (BYTE) msg[OBJECT_TYPE_POS];
	// get drawing pen info
	pObj->m_bPen = (BYTE)msg[21] ;
	pObj->m_logpen.lopnStyle =(UINT) (*((LPWORD) (msg+22))); 
	pObj->m_logpen.lopnWidth.x =(LONG) (*((LPDWORD) (msg+24))); 
	pObj->m_logpen.lopnWidth.y =(LONG) (*((LPDWORD) (msg+28))); 
	pObj->m_logpen.lopnColor =(COLORREF)(*((LPDWORD) (msg+32))); 

	pObj->m_bBrush =(BYTE)msg[36]; 
	// get brush
	pObj->m_logbrush.lbStyle = (UINT)(*((LPWORD) (msg+37)));
	pObj->m_logbrush.lbColor = (COLORREF)(*((LPDWORD)(msg+39)));
	pObj->m_logbrush.lbHatch = (LONG) (*((LPDWORD)(msg+43))); 

	EnterCriticalSection(&m_csdr);
	pObj->m_pDocument = this;
	m_objects.AddTail(pObj);
	LeaveCriticalSection(&m_csdr);

	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: RemoveObject()
// PURPOSE:  Called by  ProcessMsg on reception of an REMOVE_OBJECT msg
//			 Performs tasks related to object removal
///////////////////////////////////////////////////////////////////////////
void CClientDoc::RemoveObject(LPSTR msg)
{
	CRect rect; CPoint objpos;
	BYTE type;
	POSITION pos, posdel;
	type = msg[OBJECT_TYPE_POS];

	if (type != TEXT_OBJ) {	//other than txt object
		// get object's position
		rect.top = (LONG) (*((LPDWORD) (msg + 5)));
		rect.left =(LONG) (*((LPDWORD) (msg + 9))); 
		rect.bottom= (LONG) (*((LPDWORD) (msg + 13)));
		rect.right = (LONG) (*((LPDWORD) (msg + 17)));
	
		EnterCriticalSection(&m_csdr);
		for (pos = m_objects.GetHeadPosition(); pos != NULL;) {
			posdel = pos;
			CDrawObj* pObj =  m_objects.GetNext(pos);
			if (rect == pObj->m_position && type == pObj->m_type) {
				//LeaveCriticalSection(&m_csdr);
				//EnterCriticalSection(&m_csdr);
				//POSITION pos = m_objects.Find(pObj);
				//	if (pos != NULL)
				m_objects.RemoveAt(posdel);
				delete pObj;
				//LeaveCriticalSection(&m_csdr);
				break;
			}	
		}
		LeaveCriticalSection(&m_csdr);
	}
	else {
		//get object's position
		objpos.x = (LONG) (*((LPDWORD) (msg + 5)));
		objpos.y = (LONG) (*((LPDWORD) (msg + 9))); 
			
		EnterCriticalSection(&m_csdr);
		for (pos = m_objects.GetHeadPosition(); pos != NULL;) 
		{
			posdel = pos;
			CDrawObj* pObj =  m_objects.GetNext(pos);
			CTextObj* pTxt =  (CTextObj*) pObj;
			if ( objpos == pTxt->m_pos) 
			{
				m_objects.RemoveAt(posdel);
				delete pObj;
				break;
			}	
		}
		LeaveCriticalSection(&m_csdr);
	}

	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
}

///////////////////////////////////////////////////////////////////////////
// FUNCTION: MoveObject()
// PURPOSE:  Called by ProcessMsg on reception of a MOVE_OBJECT message
//			 Performs tasks related to object moving
///////////////////////////////////////////////////////////////////////////
void CClientDoc::MoveObject(LPSTR msg)
{
	CRect rect1, rect2; CPoint pos1, pos2;
	BYTE type;
		
	type = msg[OBJECT_TYPE_POS];
	if (type != TEXT_OBJ) {
		//get old position
		rect1.top = (LONG) (*((LPDWORD) (msg + 5)));
		rect1.left= (LONG) (*((LPDWORD) (msg + 9))); 
		rect1.bottom = (LONG) (*((LPDWORD) (msg + 13))); 
		rect1.right = (LONG) (*((LPDWORD) (msg + 17))); 
	
		//get new position
		rect2.top = (LONG) (*((LPDWORD) (msg + 21)));
		rect2.left= (LONG) (*((LPDWORD) (msg + 25))); 
		rect2.bottom = (LONG) (*((LPDWORD) (msg + 29))); 
		rect2.right = (LONG) (*((LPDWORD) (msg + 33))); 
					
		EnterCriticalSection(&m_csdr);
		for (POSITION pos = m_objects.GetHeadPosition(); pos != NULL;) {
			CDrawObj* pObj =  m_objects.GetNext(pos);
			if (rect1 == pObj->m_position) 
				pObj->m_position = rect2;						
		}						
		LeaveCriticalSection(&m_csdr);
	}
	else {
		// get positions
		pos1.x = (LONG) (*((LPDWORD) (msg + 5)));
		pos1.y = (LONG) (*((LPDWORD) (msg + 9))); 
		pos2.x = (LONG) (*((LPDWORD) (msg + 13))); 
		pos2.y = (LONG) (*((LPDWORD) (msg + 17))); 
	
		EnterCriticalSection(&m_csdr);
		for (POSITION pos = m_objects.GetHeadPosition(); pos != NULL;) 
		{
			CDrawObj* pObj =  m_objects.GetNext(pos);
			CTextObj* pTxt = (CTextObj*) pObj;
			if (pos1 == pTxt->m_pos) 
				pTxt->m_pos = pos2;						
		}						
		LeaveCriticalSection(&m_csdr);
	}

	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
}


///////////////////////////////////////////////////////////////////////////
// FUNCTION: ChangeColor()
// PURPOSE:  Called by  ProcessMsg on reception of an COLOR_OBJECT message
//			 Performs tasks related to changing an object's color
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ChangeColor(LPSTR msg)
{
	CRect rect;
	BYTE type;
	COLORREF newbrcolor, newpncolor;
		
	type = msg[OBJECT_TYPE_POS];
	//get old position
	rect.top = (LONG) (*((LPDWORD) (msg + 5)));
	rect.left= (LONG) (*((LPDWORD) (msg + 9))); 
	rect.bottom = (LONG) (*((LPDWORD) (msg + 13))); 
	rect.right = (LONG) (*((LPDWORD) (msg + 17))); 
	
	//get new color
	newbrcolor = (COLORREF) (*((LPDWORD) (msg + 21)));
	newpncolor = (COLORREF) (*((LPDWORD) (msg + 25)));					
	
	EnterCriticalSection(&m_csdr);
	for (POSITION pos = m_objects.GetHeadPosition(); pos != NULL;) {
		CDrawObj* pObj =  m_objects.GetNext(pos);
		if (rect == pObj->m_position && type == pObj->m_type) {
			pObj->m_logbrush.lbColor = newbrcolor;
			pObj->m_logpen.lopnColor = newpncolor;
			break;
		}						
	}						
	LeaveCriticalSection(&m_csdr);

	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
		
}

////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Assistant functions for whiteboard text handling
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: ReplaceTextObj()
// PURPOSE:  Replaces a text's object text in the list of objects
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ReplaceTextObj(CTextObj* pTxt)
{
	POSITION pos, posdel;

	EnterCriticalSection(&m_csdr);
	for (pos = m_objects.GetHeadPosition(); pos!=NULL;)
	{
		posdel = pos;
		CTextObj* pTx = (CTextObj*) m_objects.GetNext(pos);
		if (pTx->m_pos == pTxt->m_pos)
		{
			pTx->m_strtext = pTxt->m_strtext;
			break;
		}
	}
	LeaveCriticalSection(&m_csdr);
}


////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////
// Whiteboard operations instigated by Text Packet Processing
///////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////
// FUNCTION: AddTxtObj()
// PURPOSE:  Called by ProcessPacket on reception of an ADD_TXT packet
//			 Performs tasks related to text addition
///////////////////////////////////////////////////////////////////////////
void CClientDoc::AddTxtObj(LPSTR buffer)
{	
	CPoint pos; UINT i;
	TRACE("Processing Packet to add txt\n");
	DWORD Len = *((LPDWORD) (buffer + LEN_POS));
	// Retrieve object position
	pos.x =	(LONG) (*((LPDWORD) (buffer + HEADER_LENGTH + 1)));
	pos.y =	(LONG) (*((LPDWORD) (buffer + HEADER_LENGTH + 5)));
	// Create text object
	CTextObj* pTxt =  new CTextObj(CRect(0,0,0,0), this, TRUE);
	// Retrieve Text
	DWORD TxtLen = Len - 9; // because of text pos
	LPSTR temp = (LPSTR) calloc((int)TxtLen + 1, sizeof(char));
	// + 1 for Null termination
	for (i = DATA_BEG + 9; i < DATA_BEG + 9 + TxtLen; i++)	
		temp[i - DATA_BEG - 9] = buffer[i];
	temp[TxtLen] = '\0';	// Null termination

	// Update CString member variable
	pTxt->m_strtext.Format("%s",  (LPCTSTR) temp);
	free(temp);
	// Update position member variable
	pTxt->m_pos = pos;
	pTxt->m_pDocument = this;
	EnterCriticalSection(&m_csdr);
	m_objects.AddTail(pTxt);
	LeaveCriticalSection(&m_csdr);
	//Add(pTxt);
	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
}



///////////////////////////////////////////////////////////////////////////
// FUNCTION: AddTxtObj()
// PURPOSE:  Called by ProcessPacket on reception of an CHG_TXT packet
//			 Performs tasks related to text changing
///////////////////////////////////////////////////////////////////////////
void CClientDoc::ChgTxt(LPSTR buffer)
{
	CPoint objpos; UINT i;
	TRACE("Processing Packet to change txt\n");
	DWORD Len = *((LPDWORD) (buffer + LEN_POS));
	// Retrieve position
	objpos.x =	(LONG) (*((LPDWORD) (buffer + HEADER_LENGTH + 1)));
	objpos.y =	(LONG) (*((LPDWORD) (buffer + HEADER_LENGTH + 5)));
	// Retrieve Text
	DWORD TxtLen = Len - 9; // because of text pos
	LPSTR temp = (LPSTR) calloc((int)TxtLen + 1, sizeof(char));
	// + 1 for Null termination
	for (i = DATA_BEG + 9; i < DATA_BEG + 9 + TxtLen; i++)
		temp[i - DATA_BEG - 9] = buffer[i];
	temp[TxtLen] = '\0';	// Null termination
	
	EnterCriticalSection(&m_csdr);
	for (POSITION pos = m_objects.GetHeadPosition(); pos!= NULL;)
	{
		CDrawObj* pObj = (CDrawObj*) m_objects.GetNext(pos);
		if (pObj->m_type == TEXT_OBJ)
		{
			CTextObj* pTxt = (CTextObj*) pObj;
			if (pTxt->m_pos == objpos)
			{
				pTxt->m_strtext = CString('\0', 256);
				pTxt->m_strtext.Format("%s",  (LPCTSTR) temp); 
			}
		}
	}	
	LeaveCriticalSection(&m_csdr);

	if (m_pDrWnd != NULL)
		m_pDrWnd->InvalidateRect(NULL, TRUE);
}

///////////////////////////////////////////////////////////////////////////

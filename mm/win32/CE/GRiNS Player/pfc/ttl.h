#ifndef INC_TTL
#define INC_TTL

//
// Trivial Template Library Main Include
// 

#ifdef UNICODE
#define text_strchr wcschr
#define text_strrchr wcsrchr
#else // UNICODE
#define text_strchr strchr
#define text_strrchr strrchr
#endif // UNICODE

#ifndef _WINDOWS_
#include <windows.h>
#endif

#pragma warning(disable: 4786) // long names trunc (debug)
#pragma warning(disable: 4018) // signed/unsigned mismatch
#include <string>

struct ComInitializer
	{
	ComInitializer(){ CoInitialize(NULL);}
	~ComInitializer(){ CoUninitialize();}
	};

template <class charT>
class Application
	{
	public:
	Application(const charT *name)
	:	m_name(name), m_hInstance(NULL)
		{
		}
	bool init(HINSTANCE hInstance)
		{
		m_hInstance = hInstance;
		return true;
		}
	std::basic_string<charT> m_name;
	HINSTANCE m_hInstance;
	};

extern Application<TCHAR> g_application;

inline const Application<TCHAR>& GetApplication()
	{
	return g_application;
	}

inline HINSTANCE GetApplicationInstance()
	{
	return g_application.m_hInstance;
	}

inline TCHAR* GetApplicationName()
	{
	return (TCHAR*)g_application.m_name.c_str();
	}

inline TCHAR* GetApplicationDirectory()
	{
	static TCHAR szBuf[MAX_PATH] = TEXT("");
	if(szBuf[0] == 0)
		{
		GetModuleFileName(NULL, szBuf, sizeof(szBuf));
		TCHAR *p = text_strrchr(szBuf,TCHAR('.'));
		*p = 0;
		}
	return szBuf;
	}

//
template <class charT>
struct WndTraits : public CREATESTRUCT
	{
	WndTraits(const charT *name, LONG wndStyle)
		{
		lpCreateParams = NULL;
		hInstance = GetApplicationInstance();
		hMenu = NULL;
		hwndParent = NULL;
		cy = CW_USEDEFAULT;
		cx = CW_USEDEFAULT;
		y = CW_USEDEFAULT;
		x = CW_USEDEFAULT;
		style = wndStyle;
		lpszName = name;
		lpszClass = NULL;
		dwExStyle = 0;
		}
	};

//
template <class charT>
class MainWndClass
	{
	public:
	MainWndClass(const charT *name, WNDPROC pfnWndProc = DefWindowProc);
	~MainWndClass();
	bool registerClass();
	const charT* getName() const {return m_name.c_str();}
	HWND createWindow(const WndTraits<charT>& traits);

	private:
	WNDCLASS m_wndclass;
	ATOM m_atom;
	std::basic_string<charT> m_name;
	};

template <class charT>
MainWndClass<charT>::MainWndClass(const charT *name, WNDPROC pfnWndProc)
:	m_atom(0), m_name(name)
	{
	m_wndclass.cbSize	   = sizeof (m_wndclass);
	m_wndclass.style	    = CS_HREDRAW | CS_VREDRAW | CS_DBLCLKS;
	m_wndclass.lpfnWndProc   = pfnWndProc;
	m_wndclass.cbClsExtra    = 0;
	m_wndclass.cbWndExtra    = 0;
	m_wndclass.hInstance	= GetApplicationInstance();
	m_wndclass.hIcon	    = LoadIcon (NULL, IDI_APPLICATION);
	m_wndclass.hCursor	  = LoadCursor (NULL, IDC_ARROW);
	m_wndclass.hbrBackground = (HBRUSH) GetStockObject (WHITE_BRUSH);
	m_wndclass.lpszMenuName  = NULL;
	m_wndclass.lpszClassName = m_name.c_str();
	m_wndclass.hIconSm	= LoadIcon (NULL, IDI_APPLICATION);
	}

template <class charT>
inline MainWndClass<charT>::~MainWndClass()
	{
	if(m_atom != 0)
		UnregisterClass(m_name.c_str(), GetApplicationInstance());
	}

template <class charT>
inline bool MainWndClass<charT>::registerClass()
	{
	m_atom = RegisterClassEx(&m_wndclass);
	return m_atom != NULL;
	}

template <class charT>
inline HWND MainWndClass<charT>::createWindow(const WndTraits<charT>& traits)
	{
	HWND hWnd = CreateWindow(
					m_name.c_str(),				// window class name
		            traits.lpszName,			// window caption
                    traits.style,				// window style
                    traits.x,					// initial x position
                    traits.y,					// initial y position
                    traits.cx,					// initial x size
                    traits.cy,					// initial y size
                    traits.hwndParent,          // parent window handle
                    traits.hMenu,               // window menu handle
                    GetApplicationInstance(),   // program instance handle
		            traits.lpCreateParams);		// creation parameters
	return hWnd;
	}

#endif // INC_TTL

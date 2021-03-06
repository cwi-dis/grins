#if !defined(AFX_SVGCTL_H__995BFC13_2FB6_430D_8285_8471F81CC5A9__INCLUDED_)
#define AFX_SVGCTL_H__995BFC13_2FB6_430D_8285_8471F81CC5A9__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// Machine generated IDispatch wrapper class(es) created by Microsoft Visual C++

// NOTE: Do not modify the contents of this file.  If this class is regenerated by
//  Microsoft Visual C++, your modifications will be overwritten.


// Dispatch interfaces referenced by this interface
class CSVGDocument;

/////////////////////////////////////////////////////////////////////////////
// CSVGCtl wrapper class

class CSVGCtl : public CWnd
{
protected:
	DECLARE_DYNCREATE(CSVGCtl)
public:
	CLSID const& GetClsid()
	{
		static CLSID const clsid
			= { 0x6de3f233, 0xdbe6, 0x11d2, { 0xae, 0x81, 0x0, 0xc0, 0x4f, 0x7f, 0xe3, 0xef } };
		return clsid;
	}
	virtual BOOL Create(LPCTSTR lpszClassName,
		LPCTSTR lpszWindowName, DWORD dwStyle,
		const RECT& rect,
		CWnd* pParentWnd, UINT nID,
		CCreateContext* pContext = NULL)
	{ return CreateControl(GetClsid(), lpszWindowName, dwStyle, rect, pParentWnd, nID); }

    BOOL Create(LPCTSTR lpszWindowName, DWORD dwStyle,
		const RECT& rect, CWnd* pParentWnd, UINT nID,
		CFile* pPersist = NULL, BOOL bStorage = FALSE,
		BSTR bstrLicKey = NULL)
	{ return CreateControl(GetClsid(), lpszWindowName, dwStyle, rect, pParentWnd, nID,
		pPersist, bStorage, bstrLicKey); }

// Attributes
public:

// Operations
public:
	CString GetSrc();
	void SetSrc(LPCTSTR lpszNewValue);
	CString getSrc();
	void setSrc(LPCTSTR newVal);
	long GetReadyState();
	void reload();
	CString GetDefaultFontFamily();
	void SetDefaultFontFamily(LPCTSTR lpszNewValue);
	CString getDefaultFontFamily();
	void setDefaultFontFamily(LPCTSTR newVal);
	float GetDefaultFontSize();
	void SetDefaultFontSize(float newValue);
	float getDefaultFontSize();
	void setDefaultFontSize(float newVal);
	long GetDefaultAntialias();
	void SetDefaultAntialias(long nNewValue);
	long getDefaultAntialias();
	void setDefaultAntialias(long newVal);
	CString GetFullscreen();
	void SetFullscreen(LPCTSTR lpszNewValue);
	CString GetUse_svgz();
	void SetUse_svgz(LPCTSTR lpszNewValue);
	CSVGDocument getSVGDocument();
	CString getSVGViewerVersion();
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_SVGCTL_H__995BFC13_2FB6_430D_8285_8471F81CC5A9__INCLUDED_)

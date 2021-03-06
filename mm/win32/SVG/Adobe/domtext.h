#if !defined(AFX_DOMTEXT_H__D8F997E1_35B6_4F43_A75A_60EAE35ED57F__INCLUDED_)
#define AFX_DOMTEXT_H__D8F997E1_35B6_4F43_A75A_60EAE35ED57F__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000
// Machine generated IDispatch wrapper class(es) created by Microsoft Visual C++

// NOTE: Do not modify the contents of this file.  If this class is regenerated by
//  Microsoft Visual C++, your modifications will be overwritten.


// Dispatch interfaces referenced by this interface
class CDOMNode;
class CDOMNodeList;
class CDOMNamedNodeMap;
class CDOMDocument;

/////////////////////////////////////////////////////////////////////////////
// CDOMText wrapper class

class CDOMText : public COleDispatchDriver
{
public:
	CDOMText() {}		// Calls COleDispatchDriver default constructor
	CDOMText(LPDISPATCH pDispatch) : COleDispatchDriver(pDispatch) {}
	CDOMText(const CDOMText& dispatchSrc) : COleDispatchDriver(dispatchSrc) {}

// Attributes
public:

// Operations
public:
	CString GetNodeName();
	VARIANT GetNodeValue();
	void SetNodeValue(const VARIANT& newValue);
	long GetNodeType();
	CDOMNode GetParentNode();
	CDOMNodeList GetChildNodes();
	CDOMNode GetFirstChild();
	CDOMNode GetLastChild();
	CDOMNode GetPreviousSibling();
	CDOMNode GetNextSibling();
	CDOMNamedNodeMap GetAttributes();
	CDOMNode insertBefore(LPDISPATCH newChild, const VARIANT& refChild);
	CDOMNode replaceChild(LPDISPATCH newChild, LPDISPATCH oldChild);
	CDOMNode removeChild(LPDISPATCH childNode);
	CDOMNode appendChild(LPDISPATCH newChild);
	BOOL hasChildNodes();
	CDOMDocument GetOwnerDocument();
	CDOMNode cloneNode(BOOL deep);
	CString GetData();
	void SetData(LPCTSTR lpszNewValue);
	long GetLength();
	CString substringData(long offset, long count);
	void appendData(LPCTSTR data);
	void insertData(long offset, LPCTSTR data);
	void deleteData(long offset, long count);
	void replaceData(long offset, long count, LPCTSTR data);
	CDOMText splitText(long offset);
};

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_DOMTEXT_H__D8F997E1_35B6_4F43_A75A_60EAE35ED57F__INCLUDED_)

#ifndef INC_DROPTARGET
#define INC_DROPTARGET

template <class T>
class CDropTarget : public COleDropTarget
	{
	public:
	virtual DROPEFFECT OnDragEnter(CWnd* pWnd, COleDataObject* pDataObject,
		DWORD dwKeyState, CPoint point)
		{
		ASSERT_VALID(this);
		T *pT=static_cast<T*>(pWnd);
		return pT->OnDragEnter(pDataObject, dwKeyState, point);
		}

	virtual DROPEFFECT OnDragOver(CWnd* pWnd, COleDataObject* pDataObject,
		DWORD dwKeyState, CPoint point)
		{
		ASSERT_VALID(this);
		T *pT=static_cast<T*>(pWnd);
		return pT->OnDragOver(pDataObject, dwKeyState, point);
		}

	virtual BOOL OnDrop(CWnd* pWnd, COleDataObject* pDataObject,
		DROPEFFECT dropEffect, CPoint point)
		{
		ASSERT_VALID(this);
		T *pT=static_cast<T*>(pWnd);
		return pT->OnDrop(pDataObject, dropEffect, point);
		}

	virtual void OnDragLeave(CWnd* pWnd)
		{
		ASSERT_VALID(this);
		T *pT=static_cast<T*>(pWnd);
		pT->OnDragLeave();
		}

	};

inline LPCTSTR GetFileNameData(COleDataObject* p) 
	{
	static CLIPFORMAT cfFileName=NULL;
	static CString str;
	if(!cfFileName)cfFileName = ::RegisterClipboardFormat(_T("FileName"));
	HGLOBAL hObjDesc = p->GetGlobalData(cfFileName);
	if(!hObjDesc)return "";
	LPSTR lpClipMem=(LPSTR)GlobalLock(hObjDesc);
	str=LPCTSTR(lpClipMem);
	::GlobalUnlock(lpClipMem);
	return str;
	}

#endif
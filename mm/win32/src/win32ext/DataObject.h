#ifndef INC_DATAOBJECT
#define INC_DATAOBJECT

class PYW_EXPORT ui_data_object : public ui_assoc_object {
protected:
	ui_data_object(): m_deleteDO(FALSE){}
    ~ui_data_object();
	virtual void DoKillAssoc(BOOL bDestructing = FALSE );
	virtual void *GetGoodCppObject(ui_type *ui_type_check=NULL) const;
public:
	static ui_type type;
	MAKE_PY_CTOR(ui_data_object)
	static COleDataObject *GetDataObject(PyObject *self);
	static CLIPFORMAT GetClipboardFormat(LPCTSTR pszFmt);

	BOOL m_deleteDO;
	static CMap<CString, LPCTSTR, CLIPFORMAT, CLIPFORMAT> fmtMap;
	};

#endif


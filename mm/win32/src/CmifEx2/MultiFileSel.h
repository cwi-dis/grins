#ifndef INC_MULTIFILESEL
#define INC_MULTIFILESEL

class MultiFileSelector
	{
	public:
	MultiFileSelector(LPCTSTR strTitle,LPCTSTR strFn,LPCTSTR strPat);
	~MultiFileSelector();

	bool Open();

	const char* getSrcDir() const;
	void setTitle(LPCTSTR str);

	CString toString() const;

	private:
	POSITION GetStartPosition() const;
	CString GetNextPathName(POSITION& pos) const;
	void setSrcDir();

	OPENFILENAME of;
	char* pszFile;
	char* pszSrcDir;
	char* pszPat;
	enum {SIZEOF_SEL=8*MAX_PATH,SIZEOF_PAT=512};
	};

#endif


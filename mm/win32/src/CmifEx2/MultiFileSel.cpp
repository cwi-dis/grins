#include "stdafx.h"

#include "MultiFileSel.h"


MultiFileSelector::MultiFileSelector(LPCTSTR strTitle,LPCTSTR strFn,LPCTSTR strPat)
	{
	pszFile = new char[SIZEOF_SEL];
	pszFile[0]='\0';
	
	pszPat = new char[SIZEOF_PAT];
	lstrcpy(pszPat,strPat);
	char *psz=pszPat;
	while(*psz){if(*psz=='|')*psz='\0';psz++;}

	pszSrcDir=new char[MAX_PATH];
	pszSrcDir[0]='\0';

	memset(&of,0,sizeof(OPENFILENAME));
    of.lStructSize  = sizeof(OPENFILENAME);
    of.hwndOwner    = AfxGetMainWnd()->m_hWnd;
    of.nFilterIndex = 1;
	of.lpstrTitle=strTitle;
    of.lpstrFile    = pszFile;
    of.nMaxFile     = SIZEOF_SEL;
    of.Flags        = OFN_EXPLORER|OFN_HIDEREADONLY|OFN_FILEMUSTEXIST|OFN_ALLOWMULTISELECT;
	of.lpstrInitialDir =pszSrcDir;
	of.lpstrFilter=pszPat;
	}

MultiFileSelector::~MultiFileSelector()
	{
	delete[] pszFile;
	delete[] pszSrcDir;
	delete[] pszPat;
	}

void MultiFileSelector::setTitle(LPCTSTR str)
	{
	of.lpstrTitle = str;
	}

bool MultiFileSelector::Open()
	{		
    if(!GetOpenFileName(&of))
		return false;

	setSrcDir();

	return true;
    }

void MultiFileSelector::setSrcDir()
	{
	POSITION pos=GetStartPosition();
	if(pos!=NULL)
		{
		lstrcpy(pszSrcDir,GetNextPathName(pos));
		char *p = strrchr(pszSrcDir,'\\');
		if(p) *p='\0';
		}
	}

const char* MultiFileSelector::getSrcDir() const
	{
	return pszSrcDir;
	}

CString MultiFileSelector::toString() const
	{	
	CString str(getSrcDir());
	str+=_T(";");

	char sz[MAX_PATH],*p;	
	POSITION pos=GetStartPosition();
	while(pos!=NULL)
		{
		lstrcpy(sz,GetNextPathName(pos));
		p = strrchr(sz, '\\');
		str+=(p+1);
		if(pos!=NULL)
			str+=(TCHAR)'\n';
		}
	return str;
	}

/*
void MultiFileSelector::getSelFiles(list<CString>& l)
	{
	char sz[MAX_PATH],*p;	
	POSITION pos=GetStartPosition();
	while(pos!=NULL)
		{
		lstrcpy(sz,GetNextPathName(pos));
		p = strrchr(sz, '\\');
		l.push_back(p+1);
		}
	}*/

////////////////////////////////////
POSITION MultiFileSelector::GetStartPosition() const
	{ return (POSITION)of.lpstrFile; }

// returns full path name of next file
CString MultiFileSelector::GetNextPathName(POSITION& pos) const
{
	BOOL bExplorer = of.Flags & OFN_EXPLORER;
	TCHAR chDelimiter;
	if (bExplorer)
		chDelimiter = '\0';
	else
		chDelimiter = ' ';

	LPTSTR lpsz = (LPTSTR)pos;
	if (lpsz == of.lpstrFile) // first time
	{
		if ((of.Flags & OFN_ALLOWMULTISELECT) == 0)
		{
			pos = NULL;
			return of.lpstrFile;
		}

		// find char pos after first Delimiter
		while(*lpsz != chDelimiter && *lpsz != '\0')
			lpsz = _tcsinc(lpsz);
		lpsz = _tcsinc(lpsz);

		// if single selection then return only selection
		if ((lpsz - of.lpstrFile) > of.nFileOffset)
		{
			pos = NULL;
			return of.lpstrFile;
		}
	}

	CString strPath = of.lpstrFile;
	if (!bExplorer)
	{
		LPTSTR lpszPath = of.lpstrFile;
		while(*lpszPath != chDelimiter)
			lpszPath = _tcsinc(lpszPath);
		strPath = strPath.Left(lpszPath - of.lpstrFile);
	}

	LPTSTR lppszFileName = lpsz;
	CString strFileName = lpsz;

	// find char pos at next Delimiter
	while(*lpsz != chDelimiter && *lpsz != '\0')
		lpsz = _tcsinc(lpsz);

	if (!bExplorer && *lpsz == '\0')
		pos = NULL;
	else
	{
		if (!bExplorer)
			strFileName = strFileName.Left(lpsz - lppszFileName);

		lpsz = _tcsinc(lpsz);
		if (*lpsz == '\0') // if double terminated then done
			pos = NULL;
		else
			pos = (POSITION)lpsz;
	}

	// only add '\\' if it is needed
	if (!strPath.IsEmpty())
	{
		// check for last back-slash or forward slash (handles DBCS)
		LPCTSTR lpsz = _tcsrchr(strPath, '\\');
		if (lpsz == NULL)
			lpsz = _tcsrchr(strPath, '/');
		// if it is also the last character, then we don't need an extra
		if (lpsz != NULL &&
			(lpsz - (LPCTSTR)strPath) == strPath.GetLength()-1)
		{
			ASSERT(*lpsz == '\\' || *lpsz == '/');
			return strPath + strFileName;
		}
	}
	return strPath + '\\' + strFileName;
}



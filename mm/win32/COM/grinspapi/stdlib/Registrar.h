#ifndef INC_REGISTRAR
#define INC_REGISTRAR

class Registrar
	{
	public:
	static LONG RegisterServer(HMODULE hModule,            
                       const CLSID& clsid,          
                       const char* szFriendlyName,  
                       const char* szVerIndProgID,  
                       const char* szProgID,
					   bool InProc=true);     
	static LONG UnregisterServer(const CLSID& clsid,
                      const char* szVerIndProgID,   
                      const char* szProgID,
					  bool InProc=true);

	private:
	static bool setKeyAndValue(const char* pszPath,
                    const char* szSubkey,
                    const char* szValue);
	static void CLSIDtochar(const CLSID& clsid, 
                 char* szCLSID,
                 int length);
	static bool SubkeyExists(const char* pszPath,
                  const char* szSubkey);
	static LONG recursiveDeleteKey(HKEY hKeyParent, const char* szKeyChild) ;

	enum {CLSID_STRING_SIZE = 39};
	};

#endif



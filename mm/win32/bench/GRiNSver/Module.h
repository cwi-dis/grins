#ifndef INC_MODULE
#define INC_MODULE

#pragma comment(lib, "version.lib")

class Module : public VS_FIXEDFILEINFO 
	{
	public:
	Module(LPCTSTR strName);
	void reportOn(ostream& os);
	bool hasInfo(){return m_verRes;}

	~Module();

	static void VerifyAll(const char* pstr[],ostream& os);
	static void reportPlatformOn(ostream& os);

	private:
	bool isLoaded() const {return m_hMod!=NULL;}
	bool getFileVersionInfo();

	// reportOn parts
	void reportLangOn(ostream& os);
	void reportFileOSOn(ostream& os);

	struct TRANSLATION 
		{
		WORD langID;        
		WORD charset;
		} m_translation;
	BYTE* m_pVersionInfo;
	HINSTANCE m_hMod;
	string m_strName;
	bool m_verRes;
	string m_modulePathname;
	};

#endif // INC_MODULE

#ifndef INC_GRINS
#define INC_GRINS

namespace grins {

class TopLevel;

class Main 
	{
	public:
	Main(const TCHAR *cmdline);
	~Main();

	bool open_file(const TCHAR *pfilename);
	bool open_url(const TCHAR *purl);
	void close();

	private:
	TopLevel *m_toplevel;
	};

} // namespace grins


extern grins::Main *g_pGRiNSMain;

#endif // INC_GRINS

	
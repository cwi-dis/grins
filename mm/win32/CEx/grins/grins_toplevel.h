#ifndef INC_GRINS_TOPLEVEL
#define INC_GRINS_TOPLEVEL

namespace grins {

class Main;

class TopLevel 
	{
	public:
	TopLevel(Main *pMain, const TCHAR *url);
	~TopLevel();

	private:
	bool read_it();
	
	Main *m_pMain;
	std::basic_string<TCHAR> m_url;
	};

} // namespace grins


#endif // INC_GRINS_TOPLEVEL




#include "stdenv.h"

#include "grins_main.h"

#include "grins_toplevel.h"

namespace grins {

Main::Main(const TCHAR *cmdline)
:	m_toplevel(NULL)
	{
	}

Main::~Main()
	{
	close();
	}

bool Main::open_file(const TCHAR *pfilename)
	{
	m_toplevel = new TopLevel(this, pfilename);
	return true;
	}

bool Main::open_url(const TCHAR *purl)
	{
	return true;
	}

void Main::close()
	{
	if(m_toplevel != NULL)
		{
		delete m_toplevel;
		m_toplevel = NULL;
		}
	}


} // namespace grins


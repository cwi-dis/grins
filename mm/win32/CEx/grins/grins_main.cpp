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
	if(m_toplevel != NULL)
		close();
	}

bool Main::open_file(const TCHAR *pfilename)
	{
	if(m_toplevel != NULL) close();
	m_toplevel = new TopLevel(this, pfilename);
	if(!m_toplevel->read_it())
		{
		delete m_toplevel;
		m_toplevel = NULL;
		return false;
		}
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


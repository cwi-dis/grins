#include "stdenv.h"

#include "grins_toplevel.h"

#include "grins_main.h"

#include <windows.h>

#include "charconv.h"
#include "memfile.h"
#include "xml_parsers.h"

#include "smil/smil_parser.h"

#include "windowinterface.h"

namespace grins {


TopLevel::TopLevel(Main *pMain, const TCHAR *url)
:	m_pMain(pMain), 
	m_url(url)
	{
	read_it();
	}
		
TopLevel::~TopLevel()
	{
	}

bool TopLevel::read_it()
	{
	smil::parser smil_parser;

	ExpatParser xml_parser(&smil_parser);

	memfile mf;
	if(!mf.open(m_url.c_str()))
		{
		showmessage(TEXT("memfile::open() failed"));
		return false;
		}
	mf.fill();

	if(!xml_parser.parse((const char*)mf.data(), mf.size(), true))
		{
		showmessage(TEXT("buildFromFile() failed"));
		return false;
		}
	showmessage(TEXT("parsed document"));
	return true;
	}


} // namespace grins

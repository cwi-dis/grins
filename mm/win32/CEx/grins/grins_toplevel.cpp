#include "stdenv.h"

#include "grins_toplevel.h"

#include "grins_main.h"

#include <windows.h>

#include "charconv.h"
#include "memfile.h"

#include "tree_node.h"

#include "xml_parsers.h"

#include "smil/smil_parser.h"

#include "windowinterface.h"

namespace grins {

static smil::parser smil_parser;

TopLevel::TopLevel(Main *pMain, const TCHAR *url)
:	m_pMain(pMain), 
	m_url(url),
	m_root(0)
	{
	}
		
TopLevel::~TopLevel()
	{
	if(m_root != 0)
		delete m_root;
	}

bool TopLevel::read_it()
	{
	// do not allow reuse
	assert(m_root == 0);

	// use expat xml parser
	// with smil::parser as xml::sax_handler
	ExpatParser xml_parser(&smil_parser);

	// we currently handle only local files
	memfile mf;
	if(!mf.open(m_url.c_str()))
		{
		showmessage(TEXT("memfile::open() failed"));
		return false;
		}
	mf.fill();

	// reset smil parser
	smil_parser.reset();

	// parse source
	if(!xml_parser.parse((const char*)mf.data(), mf.size(), true))
		{
		showmessage(TEXT("parse() failed"));
		return false;
		}
	
	// get ownership of root
	m_root = smil_parser.detach();

	return true;
	}


} // namespace grins

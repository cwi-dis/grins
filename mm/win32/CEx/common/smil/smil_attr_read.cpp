
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_attr_read.h"

#include "RE.h"

static std::string _S = "[ \t\r\n]+";
static std::string _opS = "[ \t\r\n]*";
static std::string _opSign = "[\\+\\-]?";

// size = 4 (0 all, 1 int, 2 .dec, 3 dec)
static std::string _pNum = "(([0-9]+)(\\.([0-9]+))?)";

// size = 5 (0 all, 1 int, 2 .dec, 3 dec, 4 units)
static std::string _clock_pat = "^" + _pNum + _opS + "(h|min|s|ms)?"; 
enum {clock_group_units = 4};

static RE clock_re(_clock_pat);


namespace smil {

inline const char* skip_space(const char* p)
	{while(*p && isspace(*p)) p++; return p;}

any* read_clock_value(const char* rawstr)
	{
	const char *pstr = skip_space(rawstr);
	if(!clock_re.match(pstr)) return 0;

	const REMatch *p = clock_re.getMatch();
	std::string str_num = p->get_group(pstr, 1) + p->get_group(pstr, 2);
	double v = atof(str_num.c_str());
	std::string units = p->get_group(pstr, clock_group_units);
	if(units == "h") v *= 3600.0;
	else if(units == "min") v *= 60.0;
	else if(units == "ms") v *= 0.001;
	return new any(v);
	}

} // namespace smil

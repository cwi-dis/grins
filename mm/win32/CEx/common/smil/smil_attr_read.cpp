
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#include "stdenv.h"

#include "smil_attr_read.h"

#include "windowinterface.h"
#include "charconv.h"
#include "strutil.h"

#include "RE.h"

///////////////////
// static REs

static std::string _S = "[ \t\r\n]+";                      // white space
static std::string _opS = "[ \t\r\n]*";                    // optional white space
static std::string _Name = "[a-zA-Z_:][-a-zA-Z0-9._:]*";   // valid XML name

static std::string clock_val = _opS +
	     "(?:(?P<use_clock>"	    // full/partial clock value
	     "(?:(?P<hours>\\d+):)?"	// hours: (optional)
	     "(?P<minutes>[0-5][0-9]):"	// minutes:
	     "(?P<seconds>[0-5][0-9])"  // seconds
	     "(?P<fraction>\\.\\d+)?"	// .fraction (optional)
	     ")|(?P<use_timecount>"		// timecount value
	     "(?P<timecount>\\d+)"		// timecount
	     "(?P<units>\\.\\d+)?"		// .fraction (optional)
	     "(?P<metric>h|min|s|ms)?)"	// metric (optional)
	     ")" + _opS;

static RE clock_re(clock_val);

static RE color_re(std::string("(?:") +
		   "#(?P<hex>[0-9a-fA-F]{3}|" +		// #f00
			    "[0-9a-fA-F]{6})|"			// #ff0000
		   "rgb" + _opS + "\\(" +			// rgb(R,G,B)
			   _opS + "(?:(?P<ri>[0-9]+)" + _opS + ',' + // rgb(255,0,0)
			   _opS + "(?P<gi>[0-9]+)" + _opS + ',' +
			   _opS + "(?P<bi>[0-9]+)|" +
			   _opS + "(?P<rp>[0-9]+)" + _opS + '%' + _opS + ',' + // rgb(100%,0%,0%)
			   _opS + "(?P<gp>[0-9]+)" + _opS + '%' + _opS + ',' +
			   _opS + "(?P<bp>[0-9]+)" + _opS + "%)" + _opS + "\\))"); // xxx: eos

static RE syncbase_re(std::string("id\\(") + _opS + "(?P<name>" + _Name + ')' + _opS + "\\)" +
		      _opS +
		      "(?:\\(" + _opS + "(?P<event>[^)]*[^) \t\r\n])" + _opS + "\\))?" +
		      _opS);

static RE idref_re(std::string("id\\(") + _opS + "(?P<id>" + _Name + ")" + _opS + "\\)");

static RE offsetvalue_re(std::string("(?P<sign>[-+])?") + clock_val);

static RE int_percent_re("^([0-9]?[0-9]|100)%");

///////////////////
// debug checker
struct re_checker
	{
	re_checker()
		{
		check(clock_re);
		check(color_re);
		check(syncbase_re);
		check(idref_re);
		check(offsetvalue_re);
		check(int_percent_re);
		}
	void check(RE& re)
		{
		if(!re.is_valid())
			show_error(re);
		}
	void show_error(RE& re)
		{
		std::string str("re::compile() failed: ");
		str += re.get_last_error_str();
		windowinterface::showmessage(TextPtr(str.c_str()));
		}
	} a_re_checker;


///////////////////
// smil attribute parsing

namespace smil {


any* read_clock_value(const std::string& str)
	{
	if(!clock_re.match(str.begin(), str.end())) return 0;

	const REMatch *p = clock_re.get_match();
	
	std::string exp;
	exp = p->get_subex_str("use_timecount");
	if(!exp.empty())
		{
		std::string str_num = p->get_subex_str("timecount") + p->get_subex_str("units");
		double v = atof(str_num.c_str());

		std::string units = p->get_subex_str("metric");
		if(units == "h") v *= 3600.0;
		else if(units == "min") v *= 60.0;
		else if(units == "ms") v *= 0.001;
		return new any(v);
		}
	exp = p->get_subex_str("use_clock");
	// ...
	return 0;
	}

} // namespace smil

#include "stdenv.h"

#include <windows.h>

#include "charconv.h"

void test_attr_def();
void test_re();

void main_test()
	{
	test_re();
	}

//////////////////////////////////////////
// test1

#include "xml/attribute_def.h"

#include "smil/attrdef.h"

void test_attr_def()
	{
	std::string str = smil::begin_def.get_description();
	MessageBox(NULL, TextPtr(str.c_str()), TEXT("GRiNS Player"), MB_OK);

	str = smil::borderColor_def.get_description();
	MessageBox(NULL, TextPtr(str.c_str()), TEXT("GRiNS Player"), MB_OK);

	str = smil::calcMode_def.get_description();
	MessageBox(NULL, TextPtr(str.c_str()), TEXT("GRiNS Player"), MB_OK);
	}

//////////////////////////////////////////
// test2

#include "RE.h"

template <class T> std::string& operator<<(std::string& s, T c) 
	{ s+=c; return s;}

inline std::string& operator<<(std::string& s, int c) 
	{char sz[16];sprintf(sz,"%d",c); s+=sz; return s;}	

inline std::string& operator<<(std::string& s, double c) 
	{char sz[16];sprintf(sz,"%f",c); s+=sz; return s;}	

std::string space = "[ \t\r\n]+";
std::string opspace = "[ \t\r\n]*";
std::string opsign = "[\\+\\-]?";
std::string numpat = "([0-9]+\\.?)|(\\.[0-9]+)|([0-9]+\\.[0-9]+)";
std::string opunits = "(px|pt|pc|mm|cm|in|%)?";

std::string lengthPat;

struct PatInitializer {
	PatInitializer(){
		lengthPat << "(" << opsign << ")(" << numpat << ")" << opspace << opunits;
		// ...
		}
	} patInitializer;

class Length
	{
	public:
	enum {px=1, mm=2, cm=3};
	Length(const char *psz)
	:	value(std::numeric_limits<double>::quiet_NaN()), units(0)
		{
		if(re.match(psz)){
			const REMatch *p = re.getMatch();
			if(std::string(psz+p->begin(0), psz+p->end(0))=="-")
				value = -atof(std::string(psz+p->begin(1), psz+p->end(1)).c_str());
			else
				value = atof(std::string(psz+p->begin(1), psz+p->end(1)).c_str());
			setUnits(std::string(psz+p->begin(5), psz+p->end(5)));
			}
		else
			{
			//cout << "invalid legth spec" << endl;
			}
		}

	operator bool() const {return value!=std::numeric_limits<double>::quiet_NaN();}
	std::string str() const {std::string s;s << value << getUnits(); return s;}

	private:
	void setUnits(const std::string& s) {
		if(s=="px") units = px;
		else if(s=="mm") units = mm;
		else if(s=="cm") units = cm;
		else units = 0;
		}
	std::string getUnits() const {
		switch(units)
			{
			case 1: return "px";
			case 2: return "mm";
			case 3: return "cm";
			}
		return "";
		}
	static RE re;
	double value;
	int units;
	};

//static 
RE Length::re(lengthPat);

void test_re()
	{
	Length l1("-34.2 mm"); 
	std::string str = l1.str();
	MessageBox(NULL, TextPtr(str.c_str()), TEXT("GRiNS Player"), MB_OK);
	}
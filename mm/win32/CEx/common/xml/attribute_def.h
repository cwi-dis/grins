
/************************************************************************
Copyright 1991-2002 by Oratrix Development BV, Amsterdam, The Netherlands.

                        All Rights Reserved

*************************************************************************/

#ifndef INC_XML_ATTRIBUTE_DEF
#define INC_XML_ATTRIBUTE_DEF

namespace xml {

template <typename T, typename R, typename W>
class attribute_def
	{
	public:

	typedef typename T type;
	typedef typename R reader;
	typedef typename W writer;

	attribute_def(const std::string name, T default_value, const std::string description)
	:	m_name(name), 
		m_default_value(default_value), 
		m_description(description)
		m_has_default(true), 		
		{
		}

	attribute_def(const std::string name, const std::string description)
	:	m_name(name), 
		m_description(description),
		m_has_default(false), 
		{
		}
	
	bool read(const std::string repr, T& v) const { return reader::read(repr, v);};
	const std::string write(const T& v) const { return writer::write(v);}

	const std::string& get_name() const { return m_name;}
	const std::string& get_description() const { return m_description;}

	bool has_fedault() const { return m_has_default;}
	T get_default_value() const { return m_default_value};

	std::string m_name;
	std::string m_description;
	T m_default_value;
	bool m_has_default;
	};

} // namespace xml 

#endif // INC_XML_ATTRIBUTE_DEF

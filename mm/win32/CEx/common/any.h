#ifndef INC_ANY
#define INC_ANY

// Copyright Kevlin Henney, 2000, 2001, 2002. All rights reserved.
//
// Permission to use, copy, modify, and distribute this software for any
// purpose is hereby granted without fee, provided that this copyright and
// permissions notice appear in all copies and derivatives.

//////////////
// note by kk:
// this a somewhat simplified version of the original 'any'
// typeinfo and std exceptions are not available under wince

struct any
	{
    any() : m_pwrapper(0) {}

	template<class T>
    any(const T& value)
    :	m_pwrapper(new wrapper<T>(value))
		{
        }

	any(const any& other)
    :	m_pwrapper(other.m_pwrapper ? other.m_pwrapper->clone():0)
        {
        }

    ~any()
        {
        delete m_pwrapper;
        }

	any& swap(any& rhs)
		{
		std::swap(m_pwrapper, rhs.m_pwrapper);
		return *this;
        }

	template<class T>
	any& operator=(const T& rhs)
        {
		any(rhs).swap(*this);
		return *this;
		}

	any& operator=(const any& rhs)
		{
		any(rhs).swap(*this);
		return *this;
        }

	bool empty() const
        {
        return m_pwrapper == 0;
        }
	
    struct wrapper_base
		{
		virtual ~wrapper_base() {}
		virtual wrapper_base* clone() const = 0;
		};
  
	template<class T>
	struct wrapper : public wrapper_base
        {
        wrapper(const T& value)
        :	m_value(value)
            {
            }
        wrapper_base* clone() const
            {
            return new wrapper(m_value);
            }

		T m_value;
		};

	wrapper_base* m_pwrapper;
	};

template<class T>
T* get_value(any *p)
    {
	if(p->empty()) return 0;
	return &static_cast<any::wrapper<T>*>(p->m_pwrapper)->m_value;
    }

#endif

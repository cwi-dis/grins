
class PythonLibrary
	{
	public:
	PythonLibrary(const char *python_module, const char *python_home, const char *program_name)
	:	m_module(LoadLibrary(python_module)), 
		m_needs_finalize(false)
		{
		if(m_module != NULL) 
			{
			get_procs_addresses();
			SetPythonHome(const_cast<char*>(python_home));
			SetProgramName(const_cast<char*>(program_name));
			cout << python_module << " loaded" << endl;
			if(IsInitialized()==0)
				{
				cout << "PythonLibrary Initialize" << endl;
				Initialize();
				m_needs_finalize = true;
				}
			}
		else
			cout << "Failed to load "<< python_module << endl;
		}

	~PythonLibrary()
		{
		if(m_module != NULL)
			{
			if(IsInitialized()!=0 && m_needs_finalize)
				Finalize();
			FreeLibrary(m_module);
			}
		}

	void set_argv(int argc, char **argv)
		{
		SetArgv(argc, argv);
		}
	private:

	typedef int (__cdecl *Py_IsInitialized_type)();
	typedef void (__cdecl *Py_Initialize_type)();
	typedef void (__cdecl *Py_Finalize_type)();
	typedef void (__cdecl *Py_SetPythonHome_type)(char *);
	typedef void (__cdecl *Py_SetProgramName_type) (char *);
	typedef void (__cdecl *PySys_SetArgv_type) (int, char **);

	Py_IsInitialized_type IsInitialized;
	Py_Initialize_type Initialize;
	Py_Finalize_type Finalize;
	Py_SetPythonHome_type SetPythonHome;
	Py_SetProgramName_type SetProgramName;
	PySys_SetArgv_type SetArgv;

	void get_procs_addresses()
		{
		IsInitialized = (Py_IsInitialized_type)GetProcAddress(m_module, "Py_IsInitialized");
		Initialize = (Py_Initialize_type)GetProcAddress(m_module, "Py_Initialize");
		Finalize = (Py_Finalize_type)GetProcAddress(m_module, "Py_Finalize");
		SetPythonHome = (Py_SetPythonHome_type)GetProcAddress(m_module, "Py_SetPythonHome");
		SetProgramName = (Py_SetProgramName_type)GetProcAddress(m_module, "Py_SetProgramName");
		SetArgv = (PySys_SetArgv_type)GetProcAddress(m_module, "PySys_SetArgv");
		}

	HMODULE m_module;
	bool m_needs_finalize;
	};


#ifndef INC_UTIL
#define INC_UTIL

namespace python 
{
	bool initialize(int argc, char **argv, char *python_home = NULL);
	void finalize();
	bool get_sys_path(std::list<std::string>& path);
	bool addto_sys_path(const char *folder);
	bool addto_sys_path(const std::list<std::string>& path);
	void splitpath(const char *path, char *dir, char *name);
	bool run_command(const char *command);
	bool run_file(const char *filename);

} 

#endif

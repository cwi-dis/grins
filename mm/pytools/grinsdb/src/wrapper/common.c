/* common.c --- Common routines, constants, etc.  Used by all the wrappers.
 *
 * Copyright (C) 1998 by the Free Software Foundation, Inc.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software 
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

#include "common.h"

/* passed in by configure */
#define SCRIPTDIR PREFIX ## "/"		     /* trailing slash */
#define MODULEDIR PREFIX		     /* no trailing slash */

const char* scriptdir = SCRIPTDIR;
const char* moduledir = MODULEDIR;
char* python = PYTHON;

/* bogus global variable used as a flag */
int running_as_cgi = 0;



/* Some older systems don't define strerror().  Provide a replacement that is
 * good enough for our purposes.
 */
#ifndef HAVE_STRERROR

extern char *sys_errlist[];      
extern int sys_nerr;                      
        
char* strerror(int errno)                
{                                                   
	if(errno < 0 || errno >= sys_nerr) { 
		return "unknown error";
	}
	else {
		return sys_errlist[errno];
	}
}

#endif /* ! HAVE_STRERROR */


/* Report on errors and exit
 */
void
fatal(const char* ident, int exitcode, const char* format, ...)
{
	char log_entry[1024];

	va_list arg_ptr;
	va_start(arg_ptr, format);
	vsprintf(log_entry, format, arg_ptr);
	va_end(arg_ptr);

	/* Write to the console, maillog is often mostly ignored, and root
	 * should definitely know about any problems.
	 */
	openlog(ident, LOG_CONS, LOG_MAIL);
	syslog(LOG_ERR, "%s", log_entry);
	closelog();

#ifdef HELPFUL
	/* If we're running as a CGI script, we also want to write the log
	 * file out as HTML, so the admin who is probably trying to debug his
	 * installation will have a better clue as to what's going on.
	 */
	if (running_as_cgi) {
		printf("Content-type: text/html\n\n");
		printf("<head>\n");
		printf("<title>Python CGI error!!!</title>\n");
		printf("</head><body>\n");
		printf("<h1>Python CGI error!!!</h1>\n");
		printf("The expected gid of the Python CGI wrapper did ");
		printf("not match the gid as set by the Web server.");
		printf("<p>The most likely cause is that it was ");
		printf("configured and installed incorrectly.  Please ");
		printf("read the INSTALL instructions again, paying close ");
		printf("attention to the <tt>--with-cgi-gid</tt> configure ");
		printf("option.  This entry is being stored in your syslog:");
		printf("\n<pre>\n");
		printf(log_entry);
		printf("</pre>\n");
	}
#endif /* HELPFUL */
	exit(exitcode);
}



/* Is the parent process allowed to call us?
 */
void
check_caller(const char* ident, gid_t parentgid)
{
	gid_t mygid = getgid();
	if (parentgid != mygid) {
		fatal(ident, GID_MISMATCH,
		      "Failure to exec script. WANTED gid %d, GOT gid %d.  "
		      "(Reconfigure to take %d?)",
		      parentgid, mygid, mygid);
	}
}



/* Run a Python script out of the script directory
 *
 * args[0] should be the abs path to the Python script to execute
 * argv[1:] are other args for the script
 * env may or may not contain PYTHONPATH, we'll substitute our own
 */
int
run_script(const char* script, int argc, char** argv, char** env)
{
	const char envstr[] = "PYTHONPATH=";
	const int envlen = strlen(envstr);

	int envcnt = 0;
	int i, j, status;
	char** newenv;
	char** newargv;
    
	/* We need to set the real gid to the effective gid because there are
	 * some Linux systems which do not preserve the effective gid across
	 * popen() calls.  This breaks mail delivery unless the ~mailman/data
	 * directory is chown'd to the uid that runs mail programs, and that
	 * isn't a viable alternative.
	 */
#ifdef HAVE_SETREGID
	status = setregid(getegid(), -1);
	if (status)
		fatal(logident, SETREGID_FAILURE, "%s", strerror(errno));
#endif /* HAVE_SETREGID */

	/* We want to tightly control how the CGI scripts get executed.
         * For portability and security, the path to the Python executable
         * is hard-coded into this C wrapper, rather than encoded in the #!
         * line of the script that gets executed.  So we invoke those
         * scripts by passing the script name on the command line to the
         * Python executable.
         *
         * We also need to hack on the PYTHONPATH environment variable so
         * that the path to the installed Mailman modules will show up
         * first on sys.path.
	 *
         */
	for (envcnt = 0; env[envcnt]; envcnt++)
		;

	/* okay to be a little too big */
	newenv = (char**)malloc(sizeof(char*) * (envcnt + 2));

	/* filter out any existing PYTHONPATH in the environment */
	for (i = 0, j = 0; i < envcnt; i++)
		if (strncmp(envstr, env[i], envlen)) {
			newenv[i] = env[j];
			j++;
		}

	/* Tack on our own version of PYTHONPATH, which should contain only
	 * the path to the Mailman package modules.
	 *
	 * $(PREFIX)/modules
	 */
	newenv[j] = (char*)malloc(sizeof(char) * (
		strlen(envstr) +
		strlen(moduledir) +
		1));
	strcpy(newenv[j], envstr);
	strcat(newenv[j], moduledir);
	j++;

	newenv[j] = NULL;

	/* Now put together argv.  This will contain first the absolute path
	 * to the python executable, then the absolute path to the script,
	 * then any additional args passed in argv above.
	 */
	newargv = (char**)malloc(sizeof(char*) * (argc + 2));
	newargv[0] = python;
	newargv[1] = (char*)malloc(sizeof(char) * (
		strlen(scriptdir) +
		strlen(script) +
		1));
	strcpy(newargv[1], scriptdir);
	strcat(newargv[1], script);

	/* now tack on all the rest of the arguments.  we can skip argv's
	 * first two arguments because, for cgi-wrapper there is only argv[0].
	 * For mail-wrapper, argv[1] is the mail command (e.g. post,
	 * mailowner, or mailcmd) and argv[2] is the listname.  The mail
	 * command to execute gets passed in as this function's `script'
	 * parameter and becomes the argument to the python interpreter.  The
	 * list name therefore should become argv[2] to this process.
	 *
	 * TBD: have to make sure this works with alias-wrapper.
	 */
	for (i = 2; i < argc; i++)
		newargv[i] = argv[i];

	newargv[i] = NULL;

	/* return always means failure */
	(void)execve(python, &newargv[0], &newenv[0]);
	return EXECVE_FAILURE;
}



/*
 * Local Variables:
 * c-file-style: "python"
 * End:
 */

/* mail-wrapper.c --- Generic wrapper that will take info from a environment
 * variable, and pass it to two commands.
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

/* TBD: Should make this an array too?... */

/* GID that your sendmail runs filter programs as.  See you sendmail.cf
 * documentation for details
 */
#define LEGAL_PARENT_GID MAIL_GID

const int parentgid = LEGAL_PARENT_GID;
const char* logident = "Grinsdb mail-wrapper";



const char *VALID_COMMANDS[] = {
	"grinsregister.py",
	"lostkey.py",
	NULL				     /* Sentinel, don't remove */
};


int
check_command(char *command)
{
	int i = 0;

	while (VALID_COMMANDS[i] != NULL) {
		if (!strcmp(command, VALID_COMMANDS[i]))
			return 1;
		i++;
	}
	return 0;
}



int
main(int argc, char** argv, char** env)
{
	int status;

	/* sanity check arguments */
	if (argc < 2)
		fatal(logident, MAIL_USAGE_ERROR,
		      "Usage: %s program [args...]\n", argv[0]);

	if (!check_command(argv[1]))
		fatal(logident, MAIL_ILLEGAL_COMMAND,
		      "Illegal command: %s", argv[1]);

	check_caller(logident, parentgid);

	/* If we got here, everything must be OK */
	status = run_script(argv[1], argc, argv, env);
	fatal(logident, status, "%s", strerror(errno));
	return status;
}



/*
 * Local Variables:
 * c-file-style: "python"
 * End:
 */

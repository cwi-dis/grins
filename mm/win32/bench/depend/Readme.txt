

1. 	The dependency files <binfile>.txt where produced by
		DUMPBIN /DEPENDENTS <binfile>
	These files have as their first line:
		Microsoft (R) COFF Binary File Dumper Version 6.00.8168
	DUMPBIN scans the bin for dependencies statically
	so it is usefull for DLLs referenced directly by the bin
	(each DLL usually depends on others not shown.
	Note that the win32 platform is build as a set of DLLs)

2. 	The rest of the dependency files where produced by
	NuMega BoundsChecker. This is a tool that among others
	traces dynamically the DLLs loaded.
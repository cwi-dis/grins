Build GRiNSed.exe

1. check that all cmif releted projects found in
   cmif\win32\src\cmif extensions.dsw
   have been build

2. clean any c files in cmif\Build\win32\Editor
   (or include step in domkp.bat)
   	
3. run cmif\Build\win32\Editor\domkp.bat
   
4. Open vc6 prj: cmif\Build\win32\Editor\GRiNSed.dsw
   from vc6 project remove all the c files from the branch 
   Source Files and Insert all c files
   found in cmif\Build\win32\Editor
		- to remove them select them all (as in explorer) and press key del
		- to add new just select all c files found in cmif\Build\win32\Editor
		- these c files are all new and have been created by domkp.bat
		- you do not haved to remove/add c files in the project
		  if the import status of the project hasn't changed
		  (but it is better to do it anyway!)

5. Set Active Congiguration to: GRiNSed - Win32 Release
   and build the project
   - check that /MD option is set 
	 i.e C/C++,Gode Generation,Use run-time Library, Multithreaded DLL
	
__version__ = "$Id$"

from version import registryname, registrykey

# machine generated bar state by regedit tool with a little hand editing
# to change "Oratrix GRiNS" into %(registrykey)s and "Editor 2.0" into %(registryname)s.

DefaultState = r"""
[HKEY_CURRENT_USER\Software\%(registrykey)s]

[HKEY_CURRENT_USER\Software\%(registrykey)s\%(registryname)s]

[HKEY_CURRENT_USER\Software\%(registrykey)s\%(registryname)s\AmbulantToolBars-Bar0]
"BarID"=dword:0000e81b
"Bars"=dword:00000004
"Bar#0"=dword:00000000
"Bar#1"=dword:0000e803
"Bar#2"=dword:0000e804
"Bar#3"=dword:00000000

[HKEY_CURRENT_USER\Software\%(registrykey)s\%(registryname)s\AmbulantToolBars-Bar1]
"BarID"=dword:0000e804
"XPos"=dword:0000007b
"YPos"=dword:fffffffe
"Docking"=dword:00000001
"MRUDockID"=dword:0000e81b
"MRUDockLeftPos"=dword:0000007b
"MRUDockTopPos"=dword:fffffffe
"MRUDockRightPos"=dword:000000d7
"MRUDockBottomPos"=dword:0000001e
"MRUFloatStyle"=dword:00002004
"MRUFloatXPos"=dword:80000000
"MRUFloatYPos"=dword:0c050c03

[HKEY_CURRENT_USER\Software\%(registrykey)s\%(registryname)s\AmbulantToolBars-Bar2]
"BarID"=dword:0000e803
"XPos"=dword:fffffffe
"YPos"=dword:fffffffe
"Docking"=dword:00000001
"MRUDockID"=dword:00000000
"MRUDockLeftPos"=dword:fffffffe
"MRUDockTopPos"=dword:fffffffe
"MRUDockRightPos"=dword:0000007d
"MRUDockBottomPos"=dword:0000001e
"MRUFloatStyle"=dword:00002004
"MRUFloatXPos"=dword:80000000
"MRUFloatYPos"=dword:00000000

[HKEY_CURRENT_USER\Software\%(registrykey)s\%(registryname)s\AmbulantToolBars-Summary]
"Bars"=dword:00000003
"ScreenCX"=dword:00000500
"ScreenCY"=dword:00000400

""" % {'registryname': registryname, 'registrykey': registrykey}

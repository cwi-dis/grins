TARGETS = playerproxy.dll

CPP_FLAGS = /c /MTd /Zi /Od /D_WIN32_WINNT=0x0400
EXE_LINK_FLAGS = /NOD
DLL_LINK_FLAGS = /NOD /DLL

LIBS = kernel32.lib uuid.lib advapi32.lib ole32.lib oleaut32.lib rpcndr.lib rpcns4.lib rpcrt4.lib

#################################################
#
# Targets
#


all : $(TARGETS)

#################################################
iface.h server.tlb proxy.c guids.c dlldata.c : proxy.idl
	midl /Oicf /h iface.h /iid guids.c /proxy proxy.c proxy.idl 

dlldata.obj : dlldata.c 
	cl /c /Ox /DWIN32 /D_WIN32_WINNT=0x0400 /DREGISTER_PROXY_DLL dlldata.c

proxy.obj : proxy.c 
	cl /c /Ox /DWIN32 /D_WIN32_WINNT=0x0400 /DREGISTER_PROXY_DLL proxy.c

guids.obj : guids.c
	cl /c /Ox /DWIN32 /D_WIN32_WINNT=0x0400 /DREGISTER_PROXY_DLL guids.c

PROXYSTUBOBJS = dlldata.obj   \
                proxy.obj     \
                guids.obj

PROXYSTUBLIBS = kernel32.lib  \
                rpcndr.lib    \
                rpcns4.lib    \
                rpcrt4.lib    \
                uuid.lib       \
				oleaut32.lib

playerproxy.dll : $(PROXYSTUBOBJS) proxy.def
	link /dll /out:playerproxy.dll /def:proxy.def   \
		$(PROXYSTUBOBJS) $(PROXYSTUBLIBS)
	regsvr32 /s playerproxy.dll

#################################################
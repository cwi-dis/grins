
GRiNSPEps.dll: dlldata.obj GRiNSPE_p.obj GRiNSPE_i.obj
	link /dll /out:GRiNSPEps.dll /def:GRiNSPEps.def /entry:DllMain dlldata.obj GRiNSPE_p.obj GRiNSPE_i.obj \
		kernel32.lib rpcndr.lib rpcns4.lib rpcrt4.lib oleaut32.lib uuid.lib \

.c.obj:
	cl /c /Ox /DWIN32 /D_WIN32_WINNT=0x0400 /DREGISTER_PROXY_DLL \
		$<

clean:
	@del GRiNSPEps.dll
	@del GRiNSPEps.lib
	@del GRiNSPEps.exp
	@del dlldata.obj
	@del GRiNSPE_p.obj
	@del GRiNSPE_i.obj

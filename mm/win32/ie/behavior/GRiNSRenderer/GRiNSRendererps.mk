
GRiNSRendererps.dll: dlldata.obj GRiNSRenderer_p.obj GRiNSRenderer_i.obj
	link /dll /out:GRiNSRendererps.dll /def:GRiNSRendererps.def /entry:DllMain dlldata.obj GRiNSRenderer_p.obj GRiNSRenderer_i.obj \
		kernel32.lib rpcndr.lib rpcns4.lib rpcrt4.lib oleaut32.lib uuid.lib \

.c.obj:
	cl /c /Ox /DWIN32 /D_WIN32_WINNT=0x0400 /DREGISTER_PROXY_DLL \
		$<

clean:
	@del GRiNSRendererps.dll
	@del GRiNSRendererps.lib
	@del GRiNSRendererps.exp
	@del dlldata.obj
	@del GRiNSRenderer_p.obj
	@del GRiNSRenderer_i.obj

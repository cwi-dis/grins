
import dshow

inputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\168.au'
outputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\168.wav'

def any2wav(infile,outfile):
	b = dshow.CreateGraphBuilder()
	source=b.AddSourceFilter(infile)
	f = dshow.CreateFilter('WAV Dest');
	b.AddFilter(f,'WAV Dest')
	f = dshow.CreateFilter('File writer')
	b.AddFilter(f,'File writer')
	sink = f.QueryIFileSinkFilter()
	sink.SetFileName(outfile)
	pin=source.FindPin("Output")
	b.Render(pin)
	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()


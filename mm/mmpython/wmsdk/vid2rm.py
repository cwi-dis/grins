
import dshow

inputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\fox.mpg'
outputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\fox.rm'

def vid2rm(infile,outfile):
	b = dshow.CreateGraphBuilder()
	source=b.AddSourceFilter(infile)
	f = dshow.CreateFilter('Video Real Media Converter');
	b.AddFilter(f,'RMC')
	sink = f.QueryIFileSinkFilter()
	sink.SetFileName(outfile)
	pin=source.FindPin("Output")
	b.Render(pin)
	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()



import dshow

inputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\fox.mpg'
outputfile='d:\\ufs\\mm\\cmif\\bin\\win32\\fox.rm'

# no checks
def vid2rm(infile,outfile):
	b = dshow.CreateGraphBuilder()
	b.RenderFile(infile)
	renderer=b.FindFilterByName('Video Renderer')
	enumpins=renderer.EnumPins()
	pin=enumpins.Next()
	lastpin=pin.ConnectedTo()
	b.RemoveFilter(renderer)

	f = dshow.CreateFilter('Video Real Media Converter');
	b.AddFilter(f,'VRMC')
	sink = f.QueryIFileSinkFilter()
	sink.SetFileName(outfile)
	b.Render(lastpin)

	mc = b.QueryIMediaControl()
	mc.Run()
	b.WaitForCompletion()
	mc.Stop()

# vid2rm(inputfile,outputfile)



try:
    import dshow
    dshow.CoInitialize()
except:
    dshow=None

def play(filename):
    if not dshow: return
    b = dshow.CreateGraphBuilder()
    try:
        b.RenderFile(filename)
    except:
        print 'Can not render',filename
    mc = b.QueryIMediaControl()
    mc.Run()
    b.WaitForCompletion()
    # the next line seems to be needed only
    # for Pythonwin (not for Python or PyShell)
    del mc

if __name__ == '__main__':
    filename=r'd:\ufs\mm\cmif\bin\win32\test.mpg'
    play(filename)

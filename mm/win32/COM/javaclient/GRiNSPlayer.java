
import java.awt.*;
import java.util.Vector;

class GRiNSPlayer implements SMILPlayer, Runnable {
    
    GRiNSPlayer(SMILListener listener){
        this.listener = listener;
        }
    
    public Canvas getCanvas() {
        if(canvas==null)
            canvas = new PlayerCanvas();
        if(canvas instanceof PlayerCanvas)
            ((PlayerCanvas)canvas).setPlayer(this);
        return canvas;
        }
    
    public void setCanvas(Canvas c) {
        canvas = c;
        if(c!=null && c instanceof PlayerCanvas)
            ((PlayerCanvas)c).setPlayer(this);
        }
            
    public void update() {push(new GRiNSCmd("update"));}
    
    public void mouseClicked(int x, int y){push(new GRiNSCmd("mouseClicked", x, y));}
    
    public boolean mouseMoved(int x, int y){
        push(new GRiNSCmd("mouseMoved", x, y));
        return ishot;
        }
        
    public void open(String fn) {   
        push(new GRiNSCmd("open", fn));
        if(isRunning) return;
        new Thread(this).start();
        }
        
    public void close(){push(new GRiNSCmd("close"));}
    
    public void play(){push(new GRiNSCmd("play"));}
    
    public void stop(){push(new GRiNSCmd("stop"));}
    
    public void pause(){push(new GRiNSCmd("pause"));}
       
    public int getState() throws GRiNSInterfaceException
    {
        if(hgrins!=0) return ngetState(hgrins);
        return -1;
    }
             
    public double getDuration() {return -1.0;}
    
    public void setTime(double t) {}
    
    public double getTime() {return -1;}
    
    public void setSpeed(double v) {}
    
    public double getSpeed() {return 1.0;}
       
    class GRiNSCmd {
        GRiNSCmd(String fname){
            this.fname = fname;
        }
        GRiNSCmd(String fname, String strarg){
            this.fname = fname;
            this.strarg = strarg;
        }
    
        GRiNSCmd(String fname, int xarg, int yarg){
            this.fname = fname;
            this.xarg = xarg;
            this.yarg = yarg;
        }
    
        String fname;
        int xarg, yarg;
        String strarg;
    }
    
    public void run(){
        isRunning = true;
        try {
            while(!Thread.currentThread().interrupted()){
                GRiNSCmd cmd = peek();
                if(cmd==null){
                    Thread.sleep(interval);
                    continue;
                }
                try {
                if(cmd.fname.equals("open")){
                    listener.setWaiting();
                    hopen(cmd.strarg);
                    viewportSize = ngetPreferredSize(hgrins);
                    while(viewportSize.width==0){
                        Thread.sleep(50);
                        viewportSize = ngetPreferredSize(hgrins);
                        }
                     listener.setViewportSize(viewportSize.width, viewportSize.height);  
                     listener.setReady();
                }
                else if(cmd.fname.equals("close"))
                    {hclose();listener.closed(); break;}
                else if(cmd.fname.equals("play"))
                    nplay(hgrins);
                else if(cmd.fname.equals("stop"))
                    nstop(hgrins);
                else if(cmd.fname.equals("pause"))
                    npause(hgrins);
                else if(cmd.fname.equals("update"))
                    nupdate(hgrins);
                else if(cmd.fname.equals("mouseClicked"))
                    nmouseClicked(hgrins, cmd.xarg, cmd.yarg);
                else if(cmd.fname.equals("mouseMoved"))
                    ishot = nmouseMoved(hgrins, cmd.xarg, cmd.yarg);
                }
                catch(GRiNSInterfaceException e){System.out.println(""+e);}
                }
            }
        catch(InterruptedException e){System.out.println(""+e);}
        isRunning = false;
    }

    private synchronized void push(GRiNSCmd cmd){
        cmds.add(cmd);
        notifyAll();
    }
    
    private synchronized GRiNSCmd peek() {
	    int	len = cmds.size();
	    if (len == 0)
	        return null;
	    GRiNSCmd cmd = (GRiNSCmd)cmds.elementAt(0);
	    cmds.removeElementAt(0);
	    return cmd;
     }
    
    private void hopen(String fn) throws GRiNSInterfaceException
    {
        if(canvas!=null && canvas.isDisplayable())
            hgrins = nconnect(canvas);
        else
            hgrins = nconnect();
        if(hgrins!=0) {
            nopen(hgrins, fn);
            nupdate(hgrins);
        }
    }
    
    private void hclose() throws GRiNSInterfaceException
        {
        if(hgrins!=0) {
            nclose(hgrins);
            ndisconnect(hgrins);
            hgrins = 0;
            }
         try {
            Thread.sleep(500);
         }
         catch(InterruptedException e){}
         if(canvas!=null && canvas.isDisplayable())
            canvas.repaint();
    }
    
    private boolean ishot = false;
    private boolean isRunning = false;
    private Vector cmds = new Vector(10);
    private int interval = 50;
    private Dimension viewportSize;
    private SMILListener listener;
    
	private Canvas canvas; 
	
	private int hgrins;
	
    public native void initializeThreadContext();
    public native void uninitializeThreadContext();
    
    private native int nconnect();
    private native int nconnect(Component g);
    private native void ndisconnect(int hgrins);
    private native void nopen(int hgrins, String str);
    private native void nclose(int hgrins);
    private native void nplay(int hgrins);
    private native void nstop(int hgrins);
    private native void npause(int hgrins);
    private native void nupdate(int hgrins);
    private native int ngetState(int hgrins);
    private native Dimension ngetPreferredSize(int hgrins);
    private native double ngetDuration(int hgrins);
    private native void nsetTime(int hgrins, double t);
    private native double ngetTime(int hgrins);
    private native void nsetSpeed(int hgrins, double v);
    private native double ngetSpeed(int hgrins);
    private native void nmouseClicked(int hgrins, int x, int y);
    private native boolean nmouseMoved(int hgrins, int x, int y);
    static {
         System.loadLibrary("grinsp");
     }
    
}



package grins;

class GRiNSPlayerMonitor extends Thread {
    GRiNSPlayerMonitor(int cookie, int interval){
        this.cookie = cookie;
        this.interval = interval;
    }
    
    public void addListener(SMILListener listener){
        this.listener = listener;
    }
    
    public void run(){
        initializeThreadContext();
        hgrins = nconnect(cookie);
        while(hgrins!=0 && !interrupted()){
            int state = ngetState(hgrins);
            double t = ngetTime(hgrins);
            if(listener!=null){
                listener.setPos(t);
            }
            // update listener
            try {
                Thread.sleep(interval);
            }
            catch(InterruptedException e) {break;}
        }
        if(hgrins!=0)ndisconnect(hgrins);
        uninitializeThreadContext();
    }
    
    private native void initializeThreadContext();
    private native void uninitializeThreadContext();
    private native int nconnect(int cookie);
    private native void ndisconnect(int hgrins);
    private native int ngetState(int hgrins);
    private native double ngetTime(int hgrins);
    static {
         System.loadLibrary("grinsp");
     }    
    private int hgrins; 
    private int cookie;
    private int interval = 100;
    private SMILListener listener;
}

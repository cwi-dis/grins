
package grins;

class GRiNSPlayerMonitor extends Thread {
    GRiNSPlayerMonitor(GRiNSPlayer player, int interval){
        this.player = player;
        this.cookie = player.getCookie();
        this.interval = interval;
    }
    
    public void run(){
        initializeThreadContext();
        hgrins = nconnect(cookie);
        int n = ngetTopLayoutCount(hgrins);
        if(n>0){
            player.updateViewports();
            viewportsCount = n;
            }
        while(hgrins!=0 && !interrupted()){
            player.updatePosition(ngetTime(hgrins));
            player.updateState(ngetState(hgrins));
            n = ngetTopLayoutCount(hgrins);
            if(n!=viewportsCount){
                player.updateViewports();
                viewportsCount = n;
                }
            try {
                Thread.sleep(interval);
                }
            catch(InterruptedException e) {break;}
            }
        if(hgrins!=0)
            {
            ndisconnect(hgrins);
            hgrins=0;
            }
        uninitializeThreadContext();
        }
    
    private native void initializeThreadContext();
    private native void uninitializeThreadContext();
    private native int nconnect(int cookie);
    private native void ndisconnect(int hgrins);
    private native int ngetState(int hgrins);
    private native double ngetTime(int hgrins);
    private native int ngetTopLayoutCount(int hgrins);
    private native int ngetTopLayoutState(int hgrins, int index);
    
    static {
         System.loadLibrary("grinsp");
     }    
    private int hgrins; 
    private int cookie; 
    private GRiNSPlayer player;
    private int interval = 100;
    private int viewportsCount = 0;
}

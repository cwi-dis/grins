
package grins;

 /**
 *   The interface through which we receive playback notifications.
 */
public interface SMILListener {
    /**
    *  If state == STOPPED then we are stopped
    */
    public final int STOPPED = 0;
    
    /**
    *  If state == PAUSING then we are pausing
    */
    public final int PAUSING = 1;
    
    /**
    *  If state == PLAYING then we are playing
    */
    public final int PLAYING = 2;
    
    /**
    *  Current playback state notification.
    *  If state == STOPPED then we are stopped
    *  If state == PAUSING then we are pausing
    *  If state == PLAYING then we are playing
    */
    void setState(int state);
    
    /**
    *  Notification for current playback pos in seconds
    */
    void setPos(double pos);
    
    /**
    *  Notification for a top level windows change
    */
    void updateViewports();
}

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
    *  Current playback state notification from the monitoring thread.
    *  If state == STOPPED then we are stopped
    *  If state == PAUSING then we are pausing
    *  If state == PLAYING then we are playing
    */
    void setState(int state);
    
    /**
    *  Notification for current playback position in seconds from the monitoring thread.
    */
    void setPos(double pos);
    
    /**
    *  Notification for a top level windows change from the monitoring thread.
    *  This notification is send when a new top level window is needed
    *  or a top level window has been closed.
    *  Use SMILDocument.getViewportCount() to get the number of top level windows.
    *  Having the number of document's top level window you get info for each viewport using the SMILDocument methods
    *       Dimension getViewportSize(int index);
    *       String getViewportTitle(int index);
    *       boolean isViewportOpen(int index);
    *  index is in [0, SMILDocument.getViewportCount())
    */
    void updateViewports();
}
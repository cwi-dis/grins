
package grins;

 /**
 *   The interface to associate a SMILCanavas with SMIL 2 top level window.
 */
public interface SMILRenderer {
    
    /**
    *   Associate SMILCanavas with SMIL 2 top level window with index.
    */
    void setCanvas(int index, SMILCanvas canvas) throws GRiNSException;
}
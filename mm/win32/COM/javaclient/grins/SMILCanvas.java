
package grins;

import java.awt.*;
import java.awt.event.*;

public class SMILCanvas extends Canvas 
    implements MouseListener, MouseMotionListener 
{
	public void paint(Graphics g) {
		if(renderer!=null) renderer.update();
		else super.paint(g);
	}
	
    void setRenderer(GRiNSPlayer renderer) {
        this.renderer = renderer;
        addMouseListener(this);
        addMouseMotionListener(this);
    }
    private GRiNSPlayer renderer;
    private Cursor handCursor = new Cursor(Cursor.HAND_CURSOR);
    private Cursor defaultCursor = new Cursor(Cursor.DEFAULT_CURSOR);
    
    // MouseListener
    public void mouseClicked(MouseEvent e) 
        {if(renderer!=null)renderer.mouseClicked(e.getX(),e.getY());}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}

    // MouseMotionListener
    public void mouseDragged(MouseEvent e){}
    public void mouseMoved(MouseEvent e){
        if(renderer!=null && renderer.mouseMoved(e.getX(),e.getY()))
            setCursor(handCursor);
        else
            setCursor(defaultCursor);
        }
}

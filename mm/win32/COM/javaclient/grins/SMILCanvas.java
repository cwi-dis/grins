
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
	
    void setRenderer(GRiNSPlayer renderer, int index) {
        this.renderer = renderer;
        this.index = index;
        addMouseListener(this);
        addMouseMotionListener(this);
    }
    private GRiNSPlayer renderer;
    private Cursor handCursor = new Cursor(Cursor.HAND_CURSOR);
    private Cursor defaultCursor = new Cursor(Cursor.DEFAULT_CURSOR);
    private int index;
    
    // MouseListener
    public void mouseClicked(MouseEvent e) 
        {if(renderer!=null)renderer.mouseClicked(index, e.getX(),e.getY());}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}

    // MouseMotionListener
    public void mouseDragged(MouseEvent e){}
    public void mouseMoved(MouseEvent e){
        if(renderer!=null && renderer.mouseMoved(index, e.getX(),e.getY()))
            setCursor(handCursor);
        else
            setCursor(defaultCursor);
        }
}


import java.awt.*;
import java.awt.event.*;

public class PlayerCanvas extends Canvas 
    implements MouseListener, MouseMotionListener {
        
    public void setPlayer(SMILPlayer player) {
        this.player = player;
        addMouseListener(this);
        addMouseMotionListener(this);
    }
	public void paint(Graphics g) {
		if(player!=null) player.update();
		else super.paint(g);
	}
    private SMILPlayer player;
    private Cursor handCursor = new Cursor(Cursor.HAND_CURSOR);
    private Cursor defaultCursor = new Cursor(Cursor.DEFAULT_CURSOR);
    
    // MouseListener
    public void mouseClicked(MouseEvent e) 
        {if(player!=null)player.mouseClicked(e.getX(),e.getY());}
    public void mousePressed(MouseEvent e) {}
    public void mouseReleased(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}

    // MouseMotionListener
    public void mouseDragged(MouseEvent e){}
    public void mouseMoved(MouseEvent e){
        if(player!=null && player.mouseMoved(e.getX(),e.getY()))
            setCursor(handCursor);
        else
            setCursor(defaultCursor);
    }

}

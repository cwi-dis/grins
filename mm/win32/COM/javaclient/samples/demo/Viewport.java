import java.awt.*;
import java.awt.event.*;

public class Viewport extends Frame {

    private Canvas canvas;
    
    public Viewport(Canvas p) {
        canvas = p;
	    add("Center", canvas);
	    pack();
	    addWindowListener( new WindowAdapter() {
	        public void windowClosing(WindowEvent we) {
		    Viewport.this.setVisible(false);
	        }
	        });
        }
    
    public Canvas getCanvas(){
        return canvas;
        }
    
    public void update(Dimension d){
	    Insets insets = getInsets();
	    setSize(insets.left+insets.right+d.width, insets.top+insets.bottom+d.height);
	    setVisible(true);
        }
}

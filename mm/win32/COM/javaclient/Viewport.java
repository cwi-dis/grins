
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
    
    public void update(int width, int height){
	    Insets insets = getInsets();
	    setSize(insets.left+insets.right+width, insets.top+insets.bottom+height);
	    setVisible(true);
        }
}

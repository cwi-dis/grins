
import java.awt.*;
import java.awt.event.*;

public class Viewport extends Frame {

    private Dimension viewportSize;
    private Canvas viewportCanvas;
    
    public Viewport(int width, int height) {
	viewportSize = new Dimension(width, height);
	viewportCanvas = new PlayerCanvas() {
	    public Dimension getPreferredSize() {
		return viewportSize;
	    }
	};
	add("Center", viewportCanvas);
	pack();
	addWindowListener( new WindowAdapter() {
	    public void windowClosing(WindowEvent we) {
		Viewport.this.setVisible(false);
	    }
	    });
    }
    
    public Canvas getCanvas(){
        return viewportCanvas;
    }
    
    public void update(int width, int height){
	    viewportSize.width = width;
	    viewportSize.height = height;
	    Insets insets = getInsets();
	    setSize(insets.left+insets.right+width, insets.top+insets.bottom+height);
	    setVisible(true);
    }
}

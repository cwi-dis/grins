
import java.awt.*;

public class PlayerCanvas extends Canvas implements Renderable {
    public void setRenderer(Renderer renderer) {
        this.renderer = renderer;
    }
	public void paint(Graphics g) {
		if(renderer!=null) renderer.update();
		else super.paint(g);
	}
    private Renderer renderer;
}

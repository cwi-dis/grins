
package com.oratrix.client;

import java.awt.*;
import java.awt.event.*;

class SoftButton extends Component {
    public static final int X = 4;
    public static final int Y = 4;
    private boolean pressed = false;
    private boolean hot = false;
    private ActionListener actionListener;
    
    private Color color3d = new Color(128, 128+20, 128+40); //Color.gray;
    private Color color3dhigh = new Color(128, 128+40, 128+80);
    
    private Cursor handCursor = new Cursor(Cursor.HAND_CURSOR);
    private boolean changeCursor = false;
    
    static final int BORDERS_ALWAYS = 1;
    static final int BORDERS_NEVER = 2;
    static final int BORDERS_WHEN_ACTIVE = 3;
    private int paintBorders = BORDERS_NEVER;
    
    private Image[] image = {null, null, null};
    private int selImage = 0;
    private String label = null;
    private Font labelFont;
    
    private TooltipProvider tooltip = null;
    private String tooltipText;
    
    public SoftButton(){
        enableEvents(AWTEvent.MOUSE_EVENT_MASK);
    }
    
    public void set3DColors(Color col,Color colhi){
        color3d = col;
        color3dhigh = colhi;
    }
    
    public void setBorders(int t){
        paintBorders = t;
    }
    
    public void setImage(Image ig){
        image[0] = ig;
    }
    public void setImageAt(Image ig, int ix){
        if(ix==0)image[0] = ig;
        else if(ix==1) image[1] = ig;
        else image[2] = ig;
    }
    public void selectImage(int ix){
        if(ix==0) selImage = 0;
        else if(ix==1)selImage = 1;
        else selImage = 2;
        repaint();
    }
    public void setLabel(String s){
        label = s;
        labelFont = new Font("Dialog", Font.PLAIN, 12);
    }
    
    public void setTooltip(TooltipProvider t, String msg){
        tooltip = t;
        tooltipText = msg;
    }
    public void setChangeCursor(boolean b){
        changeCursor = b;
    }
    
    public void paint(Graphics g){
        if(image[selImage]!=null) g.drawImage(image[selImage], 0, 0, this);
        if(label!=null) {
            g.setColor(Color.blue);
            g.setFont(labelFont);
            FontMetrics fm = g.getFontMetrics(labelFont);
            g.drawString(label, 0, fm.getHeight());
        }
        if(paintBorders==BORDERS_NEVER) return;
        if(paintBorders==BORDERS_WHEN_ACTIVE && !hot) return;
        
        if(!hot){
            g.setColor(color3d);
        }
        else {
            g.setColor(color3dhigh);
        }
            
        Dimension d = getSize();
        for(int i=0;i<=(X+Y)/4;i++){
            g.draw3DRect(i, i, d.width-2*i-1, d.height-2*i-1, !pressed);
        }
    }
    
   public void addActionListener(ActionListener listener) {
        actionListener = AWTEventMulticaster.add(actionListener, listener);
        enableEvents(AWTEvent.MOUSE_EVENT_MASK);
        changeCursor = true;
   }
 
   public void removeActionListener(ActionListener listener) {
        actionListener = AWTEventMulticaster.remove(actionListener, listener);
   }

   public void processMouseEvent(MouseEvent e) {
        if (e.getID() == MouseEvent.MOUSE_PRESSED){
            pressed = true;
            repaint();
        }
      else if (e.getID() == MouseEvent.MOUSE_RELEASED){
        if(actionListener != null) 
            actionListener.actionPerformed(new ActionEvent(
               this, ActionEvent.ACTION_PERFORMED, "" + this));
         if (pressed){
            pressed = false;
            repaint();
         }
      }
      else if (e.getID() == MouseEvent.MOUSE_EXITED){
        if (pressed) {
            pressed = false;
            repaint();
         }
        if (hot) {
            hot = false;
            if(changeCursor)
                setCursor(Cursor.getDefaultCursor());
            if(paintBorders!=BORDERS_NEVER || image!=null)
                repaint();
         }
       if(tooltip!=null)
            tooltip.hideTooltipText();
      }
      else if(e.getID() == MouseEvent.MOUSE_ENTERED){
        if(!hot){
            hot = true;
            if(changeCursor)
                setCursor(handCursor);
            if(paintBorders!=BORDERS_NEVER || image!=null)
                repaint();
        }
        if(tooltip!=null)
            tooltip.showTooltipText(tooltipText);
      }
      super.processMouseEvent(e);
   }
    
}
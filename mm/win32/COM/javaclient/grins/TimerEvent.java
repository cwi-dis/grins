
package grins;

import java.awt.*;

public class TimerEvent extends AWTEvent
{  public TimerEvent(Component t, String name) { super(t, TIMER_EVENT); this.name=name;}
   public static final int TIMER_EVENT 
      = AWTEvent.RESERVED_ID_MAX  + 5555;
   
   public String getName() {return name;}
   private String name= "";
}



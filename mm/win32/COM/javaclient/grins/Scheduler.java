
package grins;

import java.awt.*;

public class Scheduler extends Component implements Runnable
{  public Scheduler(int i, String name) 
   {  interval = i;
      this.name = name;
      Thread t = new Thread(this);
      t.start();
      evtq = Toolkit.getDefaultToolkit().getSystemEventQueue();
      enableEvents(0);
   }

   public void addTimerListener(TimerListener l)
   {  listener = l;
   }

   public void run()
   {  
         try { Thread.sleep(interval); } 
         catch(InterruptedException e) {}
         TimerEvent te = new TimerEvent(this, name); 
         evtq.postEvent(te);   
   }

   public void processEvent(AWTEvent evt)
   {  if (evt instanceof TimerEvent)
      {  if (listener != null)
            listener.timeElapsed((TimerEvent)evt);
      }
      else super.processEvent(evt);
   }

   private int interval;
   private TimerListener listener;
   private static EventQueue evtq;
   private String name;
}


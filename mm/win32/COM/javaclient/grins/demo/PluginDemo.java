package grins.demo;

import java.awt.*;
import java.applet.*;

import java.awt.event.*;
import java.io.*;

import grins.*;

public class PluginDemo extends Applet
implements SMILListener

{
    private SMILDocument smil;
    private SMILController player;
    private String smilSrc;
    
    private Rectangle canvasrc = new Rectangle(10,12,580,400);
    
	public void init()
	{
		// This code is automatically generated by Visual Cafe when you add
		// components to the visual environment. It instantiates and initializes
		// the components. To modify the code, only use code syntax that matches
		// what Visual Cafe can generate, or Visual Cafe may be unable to back
		// parse your Java file into its visual environment.
		//{{INIT_CONTROLS
		setLayout(null);
		setBackground(java.awt.Color.white);
		setSize(600,480);
		add(canvas);
		canvas.setBackground(new java.awt.Color(236,236,236));
		canvas.setBounds(10,12,580,400);
		buttonPlay.setLabel("Play");
		add(buttonPlay);
		buttonPlay.setBackground(java.awt.Color.lightGray);
		buttonPlay.setBounds(10,452,60,24);
		buttonPause.setLabel("Pause");
		add(buttonPause);
		buttonPause.setBackground(java.awt.Color.lightGray);
		buttonPause.setBounds(88,452,60,24);
		buttonStop.setLabel("Stop");
		add(buttonStop);
		buttonStop.setBackground(java.awt.Color.lightGray);
		buttonStop.setBounds(168,452,60,24);
		add(textFieldFileOpen);
		textFieldFileOpen.setBounds(10,426,432,22);
		buttonOpen.setLabel("Open");
		add(buttonOpen);
		buttonOpen.setBackground(java.awt.Color.lightGray);
		buttonOpen.setBounds(442,426,64,24);
		buttonClose.setLabel("Close");
		add(buttonClose);
		buttonClose.setBackground(java.awt.Color.lightGray);
		buttonClose.setBounds(526,426,64,24);
		add(labelStatus);
		labelStatus.setBounds(256,458,334,18);
		//}}
		getParameters();
	
		//{{REGISTER_LISTENERS
		SymAction lSymAction = new SymAction();
		buttonPlay.addActionListener(lSymAction);
		buttonPause.addActionListener(lSymAction);
		buttonStop.addActionListener(lSymAction);
		buttonOpen.addActionListener(lSymAction);
		buttonClose.addActionListener(lSymAction);
		SymKey aSymKey = new SymKey();
		textFieldFileOpen.addKeyListener(aSymKey);
		//}}
	}
	
	//{{DECLARE_CONTROLS
	grins.SMILCanvas canvas = new grins.SMILCanvas();
	java.awt.Button buttonPlay = new java.awt.Button();
	java.awt.Button buttonPause = new java.awt.Button();
	java.awt.Button buttonStop = new java.awt.Button();
	java.awt.TextField textFieldFileOpen = new java.awt.TextField();
	java.awt.Button buttonOpen = new java.awt.Button();
	java.awt.Button buttonClose = new java.awt.Button();
	java.awt.Label labelStatus = new java.awt.Label();
	//}}
	
	private void getParameters()
	    {
		smilSrc = getParameter("smilsrc");
		if(smilSrc!=null){
		    smilSrc.trim();
		    }
	        
	    }
	    
	private void message(String str) {
	    System.out.println(str);
	}
	
	public void start() {
	    if(smilSrc!=null)
	        {
	        textFieldFileOpen.setText(smilSrc);    
	        buttonOpen.setEnabled(true);
	        buttonClose.setEnabled(false);
	        }
	    buttonPlay.setEnabled(false);
	    buttonPause.setEnabled(false);
	    buttonStop.setEnabled(false);
	    }
	    
	public void stop() {
	    if(smil!=null) 
	        {
	        smil.close();	    
	        smil = null;
	        }
	    }
	    
    public void destroy() {
        }
        
    public void setWaiting(){
        setCursor(new Cursor(Cursor.WAIT_CURSOR));
    }
    public void setReady(){
       setCursor(Cursor.getDefaultCursor());
    }
	
	// SMILListener interface
    public void setPos(double pos){}
    public void setState(int state)
        {
        if(state==SMILListener.STOPPED)
            {
	        buttonPlay.setEnabled(true);
	        buttonPause.setEnabled(false);
	        buttonStop.setEnabled(false);
            }
        }
	public void updateViewports(){
	}
	
    private void open(String filename){
        // create SMIL doc
        String license = "";
	    smil = GRiNSToolkit.createDocument(filename, license);
	    
	    // update create UI
	    double dur = smil.getDuration();
	    String str = "Documement duration: ";
	    if(dur<0 || dur==0)
	        labelStatus.setText(str + "indefinite");
	    else
	        labelStatus.setText(str + (int)(dur+0.5) + " secs");
	    
	    Dimension d = smil.getViewportSize(0);
	    Rectangle rc  = canvas.getBounds();
	    
	    int x=rc.x, y=rc.y, w=rc.width, h=rc.height;
	    if(d.width<rc.width)
	        {
	        x = rc.x + (rc.width-d.width)/2;
	        w = d.width;
	        }
	    if(d.height<rc.height)
	        {
	        y = rc.y + (rc.height-d.height)/2;
	        h = d.height;
	        }
	    canvas.setBounds(x,y,w,h);
	    
	    // set SMIL canvas
	    try {smil.getRenderer().setCanvas(0, canvas);}
	    catch(Exception e){System.out.println(""+e);}
	    
	    // get controller
        player = smil.getController();
        player.addListener(this);
    }
	

	class SymAction implements java.awt.event.ActionListener
	{
		public void actionPerformed(java.awt.event.ActionEvent event)
		{
			Object object = event.getSource();
			if (object == buttonPlay)
				buttonPlay_ActionPerformed(event);
			else if (object == buttonPause)
				buttonPause_ActionPerformed(event);
			else if (object == buttonStop)
				buttonStop_ActionPerformed(event);
			else if (object == buttonOpen)
				buttonOpen_ActionPerformed(event);
			else if (object == buttonClose)
				buttonClose_ActionPerformed(event);
		}
	}

	void buttonOpen_ActionPerformed(java.awt.event.ActionEvent event)
	{
	    smilSrc = textFieldFileOpen.getText();
	    open(smilSrc);
	    
	    buttonOpen.setEnabled(false);
	    buttonClose.setEnabled(true);
	    
	    buttonPlay.setEnabled(true);
	    buttonPause.setEnabled(false);
	    buttonStop.setEnabled(false);
	}

	void buttonClose_ActionPerformed(java.awt.event.ActionEvent event)
	{
        if(player!=null) player.stop();	
        player = null;
        
	    if(smil!=null) smil.close();
        smil=null;
        
        canvas.setBounds(canvasrc);
        
	    buttonOpen.setEnabled(true);
	    buttonClose.setEnabled(false);
        
	    buttonPlay.setEnabled(false);
	    buttonPause.setEnabled(false);
	    buttonStop.setEnabled(false);
	}

	void buttonPlay_ActionPerformed(java.awt.event.ActionEvent event)
	    {
		if(player!=null) player.play();
		
	    buttonPlay.setEnabled(false);
	    buttonPause.setEnabled(true);
	    buttonStop.setEnabled(true);
	    }

	void buttonPause_ActionPerformed(java.awt.event.ActionEvent event)
	    {
		if(player!=null) player.pause();
		
	    buttonPlay.setEnabled(true);
	    buttonPause.setEnabled(true);
	    buttonStop.setEnabled(true);
	    }

	void buttonStop_ActionPerformed(java.awt.event.ActionEvent event)
	    {
        if(player!=null) player.stop();	
                
	    buttonPlay.setEnabled(true);
	    buttonPause.setEnabled(false);
	    buttonStop.setEnabled(false);
	    }


	class SymKey extends java.awt.event.KeyAdapter
	{
		public void keyTyped(java.awt.event.KeyEvent event)
		{
			Object object = event.getSource();
			if (object == textFieldFileOpen)
				textFieldFileOpen_KeyTyped(event);
		}
	}

	void textFieldFileOpen_KeyTyped(java.awt.event.KeyEvent event)
	{
	    smilSrc = textFieldFileOpen.getText();
	    if(smilSrc.length()==0) return;
		
		buttonOpen.setEnabled(true);
		if(event.getKeyChar()=='\n' || event.getKeyChar()=='\r'){
		        event.consume();
	            open(smilSrc);
	    
	            buttonPlay.setEnabled(true);
	            buttonPause.setEnabled(false);
	            buttonStop.setEnabled(false);
		    }
		
	}
}

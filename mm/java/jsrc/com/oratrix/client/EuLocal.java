
package com.oratrix.client;

class EuLocal {
    // Unicode base
    static final int GREEK_BASE = 880;
    
    // MBS base
    static final int GREEK_BASE_MBS = 160;
    
	public static String toMB(String s){
		StringBuffer sb = new StringBuffer();
		int n = s.length();
		for(int i=0;i<n;i++){
		    char ch = s.charAt(i);
		    int chcode = (int)ch;
		    if(chcode>GREEK_BASE)
		        sb.append((char)(GREEK_BASE_MBS + chcode - GREEK_BASE));
		    else
		        sb.append(ch);
		}
	    return sb.toString();
	}

	public static byte[] getBytes(String s){
		int n = s.length();
		byte[] buf = new byte[n];
		for(int i=0;i<n;i++){
		    char ch = s.charAt(i);
		    int chcode = (int)ch;
		    if(chcode>GREEK_BASE){
		        chcode -= GREEK_BASE;
		        chcode += GREEK_BASE_MBS;
		    }
	        buf[i] = (byte)chcode;
		}
	    return buf;
	}
	
	public static byte[] getDirBytes(String s){
		int n = s.length();
		byte[] buf = new byte[n];
		for(int i=0;i<n;i++)
	        buf[i] = (byte)s.charAt(i);
	    return buf;
	}

	public static String toUN(String s){
		StringBuffer sb = new StringBuffer();
		int n = s.length();
		for(int i=0;i<n;i++){
		    char ch = s.charAt(i);
		    int chcode = (int)ch;
		    if(chcode > GREEK_BASE_MBS)
		        ch = (char)(GREEK_BASE + chcode - GREEK_BASE_MBS);
	        sb.append(ch);
		}
	    return sb.toString();
	}
	
	public static void checkUNtoMB(String uns, String mbs){
	   System.out.println("UN: " + uns);
	   System.out.println("MB: " + toUN(mbs));
	}
}

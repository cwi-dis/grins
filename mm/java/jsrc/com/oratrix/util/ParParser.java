
package com.oratrix.util;

import java.awt.*;
import java.util.*;

public class ParParser {
   static public String[] parseStrings(String str, String sep){
      if (str != null){
         StringTokenizer st = new StringTokenizer(str, sep);
         String result[] = new String[st.countTokens()];
         for (int i = 0; i < result.length; i++)
            result[i] = st.nextToken();
         return result;
      }
      else return null;
   }

   static public String toPar(String str){
      if(str==null || str.length()==0){
        return "";
      }
      String lines[] = parseStrings(str, "\r\n");
      StringBuffer sb = new StringBuffer();
      for(int i = 0; i < lines.length; i++){
        if(i>0) sb.append(" ");
        sb.append(lines[i]);
      }
      return sb.toString();
   }
   
    static public String[] toLines(String str, FontMetrics fm, int width) {
      if(str==null || str.length()==0){
        String result[] = new String[1];
        result[0]="";
        return result;
      }
      String[] hlines = parseStrings(str, "\r\n");
      Vector list = new Vector(0, 1);
      for (int i = 0; i < hlines.length; i++){
        String[] slines = wordWrap(hlines[i], fm, width);
        for(int j=0;j<slines.length;j++)
            list.insertElementAt(slines[j], list.size());
      }
      int num = list.size();
      String result[] = new String[num];
      for (int k = 0; k < num; k++)
         result[k] = (String)list.elementAt(k);
      return result;
    }
   
    static public String[] wordWrap(String str, FontMetrics fm, int width) {
      if(str==null || str.length()==0){
        String result[] = new String[1];
        result[0]="";
        return result;
      }
        
      String word[] = parseStrings(str, " ");
      
      if(word.length==1){
        String result[] = new String[1];
        result[0]=word[0];
        return result;
      }
      
      Vector list = new Vector(0, 1);
      String line = word[0];

      for (int i = 1; i < word.length; i++)
      {
         if ((fm.stringWidth(line) + fm.stringWidth(word[i] + " ")) >= (width))
         {
            list.insertElementAt(line, list.size());
            line = word[i];
         }

         else
         {
            line = line + " " + word[i];
         }

         if (i == (word.length - 1))
         {
            list.insertElementAt(line, list.size());
         }
      }

      int num = list.size();
      String result[] = new String[num];

      for (int i = 0; i < num; i++)
      {
         result[i] = (String) (list.elementAt(i));
      }

      return result;
   }
}

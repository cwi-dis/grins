package com.oratrix.xml.parse;

/**
 * Information about a markup declaration.
 * @version $Revision$ $Date$
 */
public interface MarkupDeclarationEvent {
  static int ATTRIBUTE = 0;
  static int ELEMENT = 1;
  static int GENERAL_ENTITY = 2;
  static int PARAMETER_ENTITY = 3;
  static int NOTATION = 4;
  int getType();
  String getName();
  String getAttributeName();
  DTD getDTD();
}

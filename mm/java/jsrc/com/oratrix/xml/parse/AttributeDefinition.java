package com.oratrix.xml.parse;

import java.util.Enumeration;

/**
 * Information about the definition of an Attribute.
 *
 * @see ElementType#getAttributeDefinition
 * @version $Revision$ $Date$
 */

public interface AttributeDefinition {
  /**
   * Returns the normalized default value
   * or null if no default value was specified.
   */
  String getDefaultValue();

  /**
   * Returns the unnormalized default value
   * or null if no default value was specified.
   */
  String getDefaultUnnormalizedValue();

  /**
   * Returns true if the attribute was #REQUIRED or #FIXED.
   */
  boolean isRequired();

  static byte UNDECLARED = -1;
  static byte CDATA = 0;
  static byte ID = 1;
  static byte IDREF = 2;
  static byte IDREFS = 3;
  static byte ENTITY = 4;
  static byte ENTITIES = 5; 
  static byte NMTOKEN = 6;
  static byte NMTOKENS = 7;
  static byte ENUM = 8;
  static byte NOTATION = 9;
  /**
   * Returns an integer corresponding to the type of the attribute.
   */
  byte getType();

  /**
   * Returns an enumeration over the allowed values
   * if this was declared as an enumerated type, and null otherwise.
   */
  Enumeration allowedValues();
}

package com.oratrix.xml.parse;

/**
 * Information about the end of the reference to an entity.
 * @version $Revision$ $Date$
 */
public interface StartEntityReferenceEvent {
  /**
   * Returns the name of the referenced entity.
   */
  String getName();
}

package com.oratrix.xml.parse;

/**
 * Interface for events which provide location information.
 * @version $Revision$ $Date$
 */
public interface LocatedEvent {
  /**
   * Returns the location
   * of the first character of the markup of the event.
   * The return value is valid only so long as the event
   * itself is valid.
   */
  ParseLocation getLocation();
}


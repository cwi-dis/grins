package com.oratrix.xml.parse;

/**
 * Information about the prolog.
 * @version $Revision$ $Date$
 */
public interface EndPrologEvent {
  /**
   * Returns the DTD.
   * This will not be null even if there was no DOCTYPE declaration.
   */
  DTD getDTD();
}

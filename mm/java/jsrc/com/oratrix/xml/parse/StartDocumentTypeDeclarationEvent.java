package com.oratrix.xml.parse;

/**
 * Information about the start of a document type declaration.
 * @version $Revision$ $Date$
 */
public interface StartDocumentTypeDeclarationEvent {
  /**
   * Returns the DTD being declared.
   */
  DTD getDTD();
}

package com.oratrix.xml.parse;

/**
 * Information about the end of a document type declaration.
 * @see com.oratrix.xml.parse.base.Application#endDocumentTypeDeclaration
 * @version $Revision$ $Date$
 */
public interface EndDocumentTypeDeclarationEvent {
  /**
   * Returns the DTD that was declared.
   */
  DTD getDTD();
}

package com.oratrix.client;


import com.oratrix.xml.parse.*;

import java.io.IOException;


class ApplicationAdapter implements Application {
  public void startDocument() throws IOException { }
  public void endDocument() throws IOException { }
  public void startElement(StartElementEvent event) throws IOException { }
  public void characterData(CharacterDataEvent event) throws IOException { }
  public void endElement(EndElementEvent event) throws IOException { }
  public void processingInstruction(ProcessingInstructionEvent pi) throws IOException { }
  public void endProlog(EndPrologEvent event) throws IOException { }
  public void comment(CommentEvent event) throws IOException { }
  public void startCdataSection(StartCdataSectionEvent event) throws IOException { }
  public void endCdataSection(EndCdataSectionEvent event) throws IOException { }
  public void startEntityReference(StartEntityReferenceEvent event) throws IOException { }
  public void endEntityReference(EndEntityReferenceEvent event) throws IOException { }
  public void startDocumentTypeDeclaration(StartDocumentTypeDeclarationEvent event) throws IOException { }
  public void endDocumentTypeDeclaration(EndDocumentTypeDeclarationEvent event) throws IOException { }
  public void markupDeclaration(MarkupDeclarationEvent event) throws IOException { }
}

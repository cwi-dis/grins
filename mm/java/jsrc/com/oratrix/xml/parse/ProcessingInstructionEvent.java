package com.oratrix.xml.parse;

/**
 * Information about a processing instruction.
 * @version $Revision$ $Date$
 */
public interface ProcessingInstructionEvent extends LocatedEvent {
  /**
   * Returns the target of the processing instruction.
   */
  String getName();
  /**
   * Returns the part of the processing instruction following the
   * target.  Leading white space is not included.
   * The string will be empty rather than null if the processing
   * instruction contains only a target.
   */
  String getInstruction();
}

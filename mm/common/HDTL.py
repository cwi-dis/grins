__version__ = "$Id$"

# The player algorithm treats the head and tail (begin and end) sides
# of a node as separate events in time; there are separate counters
# and lists of dependencies, indexed by the symbolic constants
# HD and TL: e.g., node.counter[HD], node.deps[HD].
# This is used in modules Player and Timing

HD, TL = 0, 1

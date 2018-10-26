# Soffit Input Format, v0.1

A Soffit graph grammar is represented as a JSON object in text format, or
as a Python dictionary in source code format.  Each dictionary entry represents
one input rule, which may have a single output or multiple outputs.

If you're familiar with Tracery, think of it as a Tracery grammar where *all*
identifiers are nonterminals.

### Single rule

```
  "inputgraph" : "outputgraph"
```

### Multiple-choice rule

```
  "inputgraph" : [ "outputgraph", "outputgraph2", "outputgraph3" ]
```

### Starting graph

The special rule "start" gives an initial graph, or choice of graphs, from
which to begin applying rules.  This rule is optional, but "start" is a
reserved word which may not be used in other contexts.

```
  "start" : "startgraph"
```

## Graph notation

Graphs are represented in a format similar to that used by the Dot language.

All graphs are simple graphs (permitting self-loops), not multigraphs.

### Node (vertex) identifiers

Standalone strings of characters represent a node in a rule.  The restrictions
on node identifiers follows that in Swift (see
https://docs.swift.org/swift-book/ReferenceManual/LexicalStructure.html)

Identifiers may start with any non-digit non-punctuation character, and
continue with any non-punctuation character.  Suggested convention is to
use capital letters for node names.

FIXME: allow underscores?

Examples: `A`, `X35`, `😀`, `♡`

Node identifiers are variables that bind to edges; nodes themseleves do not
have names.  To apply labels to the output, tags must be used (see below.)

### Edges

`A -- B` represents an undirected edge between node A and node B

`A -> B` represents a directed edge from node A to node B

`A <- B` represents a directed edge from node B to node A

Soffit accepts either and will automatically determine that the graph is
directed if any directed edges occur.  Undirected edges will be converted into
two directed edges in a directed graph.

Edges may be chained together to represent a sequence of edges.

Edges do not have names.

Whitespace around the edge notations is permitted.

Examples: `A--B`, `A -- X -- Y`, `C <- D->E`

### Graphs

A graph is represented by a string containing a sequence of vertex names
and edges, separated by semicolons.

If a vertex name appears multiple times it always refers to the same vertex.

If is permissible for a vertex name to appear on both sides of an edge,
creating a self-loop.

Example: `A--B--C; Q; B--C--D; E--E; F`

### Node and edge tags

Sticking with the Dot convention, a tag or attribute may be applied to a
node identifier or an edge declaration, by enclosing the tag in square
bracket after the declaration.

Example: `A [leaf];`, `A -- B [color='red']`

Example: `A -- B -- C [31]` (both edges get the tag 31.)

Single-quotes may be used inside tags without escaping.  Double-quotes should
be escaped with `\"`. Square brackets in a tag should be escaped with `\[` `\]`.

Soffit supports only a single tag per node or edge; the entire contents of
the square brackets form a single object, even if separated by commana. These
tags will be provided in the output; a postprocessing stage in an output
formatter may provide additional conventions on tags, such as suppressing
non-formatting tags.

### Merged nodes

A non-injective rule may merge nodes.  That is, nodes on the right hand side of a rule
correspond to more than one node from the left hand.  This is indicated by using ^ to combine
node identifiers in the graph on a right-hand side of a rule.  A merge need only be indicated once
on the right side.  Node merges are transitive, so if A is merged with B, and B is merged with C,
then A is merged with C as well.

Example: `"A; B; C" : "A^B^C"'

Example: `"A--B--C" : "A^C--B"'

Example: `"A--B--C" : "A^C--B^C"' creates a single node with a single self-loop

Example: `"A--B--C" : "A^B--A--C"' and `"A--B--C" : "A^B--A^B--C"' and `"A--B--C" : "A--B--C; A^B"' are all equivalent. 


## Versioning

The rule format may change, with no guarantee of backward-compatibility in
alpha and pre-alpha releases.

A version string may be added to the rule set as a key-value pair:

`"version": "0.1"`

This will allow Soffit to warn about any incompatible changes in the grammar,
though such functionality is not guaranteed.

### Reserved rule names

`start` is a reserved rule name for the (optional) initial graph

`version` is a reserved rule name that contains the version number of the
input format

`extensions` is a reserved rule name for adding non-graph key/value pairs, for
example graph-wide display attributes.

### Reserved characters

The characters `$` and `{` should be avoided in tags as they may be used
in later versions to do pattern-matching instead of exact tag match.
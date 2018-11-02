# Soffit Rule Application Semantics

A Soffit graph grammar is interpreted in a nondeterminstiic (random) fashion.

## Rule selection

Each iteration of the graph rewriting performs the following steps:

1. Choose one left-hand graph uniformly from the left-hand graphs specified in the
grammar.
2. Choose one right-hand graph uniformly from the available left-hand graphs (if there are multiple choices.)
3. Choose one match uniformly from the available locations in the graph.
4. If we fail in step #3, the choice in step #2 may be retried if a different right-hand graph could result in a match (due to deletion of nodes and the dangling condition; see below.)
5. If we fail to find any right-hand rules which produce a match, go back to step #1 and make a different choice.
6. If have tried all left-hand graphs without a match, application of the graph grammar terminates.

On the next iteration, all choices made are forgotten and the process starts over.

If a rule can be permuted, then each possible permutation is a different match.

### Example

For example, if the rule set is

```
"X [a]" : "X[a]; Y[b]; X--Y;"
"X [b]" : [ "X[c]", "X[d]", "X[e]" ]
```

Then we have 50% chance of selecting `X[a]` and 50% chance of selecting `X[b]`.  If we select the
first rule, and no nodes tagged `[a]` are available, then we try applying the second rule.

If `X[b]` is chosen, and there is a node tagged with `b` in the graph, then it will be relabled `c`, `d`, or `e` with 1/3 probability each.

The left-hand side `A--B` can match `1--2` as both `A=1, B=2` and `A=2, B=1` even if the graph
is undirected.

## Rule match constraints

Left graphs in Soffit are matched injectively; each node ID must bind to a different node.
If X matches node 1, then no other variable can match node 1.

The "dangling condition" must be satisfied: if a node is deleted, then it cannot leave an undeleted
edge behind that is missing one vertex.  Whenever a node ID X is matched with a graph node 1,
it must be the case that either

1. X has no edges touching it, or
2. any edges adjacent to X are matched with edges that are deleted by the rule

An item missing from the left hand side is not necessarily missing in the match.

### Examples

The left-hand graph `A--B--C` matches `1--2--3` as either `A=1, B=2, C=3` or `A=3, B=2, C=1` but not
'A=1, B=2, C=1` or `A=2, B=1, C=2`.

The rule `"A--B" : "B"` matches `1--2--3` as either 'A=1, B=2` or `A=3, B=2` but not `A=2, B=3`
which would leave the dangling edge 1--2.

The rule `"A; B" : "A--B"` matches `1--2; 3` as any one of 'A=1, B=2`, `B=1, A=2`, `A=1, B=3`, `A=3, B=1`, `A=2, B=3`, or `A=3, B=2`, even though the edge already exists between two of these graphs.  It is not possible to specify a "don't match" condition.

## Rule application

Any node IDs appearing on the right side of a rule but not its left side will result in the
creation of new nodes, one per ID.  The new node is assigned a number; the text of the node ID
is not used.

Example: `"A" : "A; B;"` creates a new node.  Applied to the graph `1; 2; 3;` this will result in the graph `1; 2; 3; 4`.

Any edges appearing on the right side of a rule but not its left side will result in the
creation of new edges.

Example: `"A[x]; B[y]" : "A--B; A[x]; B[y];"` creates a new edge between the nodes
tagged with `a` and `b`.  When applied to the graph `1[x]; 2[y]` the result is `1[x]; 2[y]; 1--2`.

Any node IDs appearing on the left hand side, but not the right hand side, are deleted.  Similarly,
any edges appearing on the left hand side are deleted if the same pair of nodes are not connected
on the right hand side.

Example: `"A[x]; B[y]; A--B; C[z];" : "A[x]; B[y];"` deletes the edge between two nodes
tagged with `a` and `b`, and deletes a node tagged with `z`.

A rule is only applied once per iteration.  If a rule specifies deletion of a node with a
specific tag, only one such node is deleted, even if multiple such locations exist in the graph.

Any node IDs appearing on the left hand side, but as part of a merged group on the right hand
side, are collapsed to a single node in the output.

Example: `"A[x]; B[x]; A--B;" : "A^B[x];"` merges two nodes tagged with `x` that are connected
by an edge, and deletes the edge between them.  Edges that are adjacent to either node will now
be adjacent to the merged node.  Applied to the graph `1[x]; 2[x]; 3[z]; 1--2--3` the result will be the graph `1[x]; 3[z]; 1--3`.

If two nodes are merged as the result of a rule, then edges adjacent to those nodes may also
be merged.  The tag on the resulting edge will be chosen arbitrarily; it will be one of the
tags associated with the original edges, but no guarantee is made as to which one.

Example: `"A[x]; B[x]; A--B;" : "A^B[x];"` applied to the graph `1[x]; 2[x]; 1--2; 2--3 [foo]; 2--3 [bar];` will result in either `1[x]; 1--3 [foo]` or `1[x]; 1--3 [bar]`.

All of the tags on the right hand side of the rule are applied; even the absence of a tag is
meaningful.  Tags do not automatically carry over.

Example: `"A[x]; B[x];" : "A--B;"` places an edge between two nodes tagged with `x`, but removes the tags from both nodes.  The new edge has no tag.  Specify `"A[x]; B[x];" : "A--B; A[x]; B[x]"` to keep the existing tags.

Example: `"A[x]; B[x];" : "A[x]; B[y];"` relabels one of the two nodes in the graph from `x` to `y`, but only if there are two `x`'s to be found.

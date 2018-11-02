# Ideas on rewrite semantics

Would like to permit deletions of nodes and edges, but is DPO (double pushout) really the right
model?

Are non-injective mappings understandable to ordinary users, or just a pain?  Should we let
a rule, or an entire grammar, specify that they wnat only injective mappings?

## Non-morphisms

The input format as currently defined lets somebody define a rule that is not, in fact, a graph
morphism.  For example,

"A[x]; B[y]" => "A^B[z]"

is not a morphism because if n is the label function and m = ( m_V, m_E ) is the mapping between
graphs, then

N_l(B) = y
N_r(m(B)) = N(A^B) = z

So N_l != N_r . m, the diagram does not commute, so m is not a graph morphism.

Do we care that this is the case?  Does it lead to ambiguity?

To read: "Relabelling in Graph Transformation" Annegret Habel and Detlef Plump

## Graphs vs. Multigraphs

Consider the rule

"A[1]; B[1]; C[2]; D[2];" => "A^B[1]; C^D[2]"

which *is* a graph morphism, but what happens when we try to apply it to

```
W[1] --m-- X[1]
 |          |
 p          n
 |          |
Z[2] --o-- Y[2]


W^X[1] == m
 |
 ???
 |
Y^Z[2] == o
```

We can't unambiguously reduce it to a single edge.  The "right" thing is to allow
multigraphs; then the pushout is defined by preserving *both* edges.

But, multigraphs are harder to represent--- we'd need a way to numbering edges as well
as tagging them.  And most of the time people probably wouldn't care?

## v0.1 decisions:

I'll switch to injective mappings only (which should reduce the number of clauses a lot!)

I'll stick with simple graphs (allowing self-loops) and document that when nodes are merged
then the tag on the merged edge is unpredictable.  It will be the tag on one of the merged edges.












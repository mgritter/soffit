# Ideas on semantics

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

## Merged edges

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

Should the edge have label p or n?  Or is this matching not a morphism?

What is the single pushout here?

```
p : Left - > Right

p(A) = A^B   n(A) = 1  n(A^C) = 1
p(B) = A^B   n(B) = 1
p(C) = C^D   n(C) = 2  n(C^D) = 2
p(D) = C^D   n(D) = 2

m : Left -> Graph

m(A) = W    n(W) = 1
m(B) = X    n(X) = 1
m(C) = Y    n(Y) = 2
m(D) = Z    n(Z) = 2
```
(or, P(C) and P(D) could be swapped, or P(C)=P(D).)

Factorize p:L->R as

```
h : L->p(L)          surjective
inc_p(L) : p(L)->R   injective
p = inc_p(L) . h
```

What is the gluing relation on L induced by h?

Well, A equiv^h B, and C equiv^h D (and the reflexive elements)

What is the induced gluing relation on G, call it Rm

x Rm y if m(x) equiv m(y)
e1 Rm e2 if m(e1) equiv m(e2)

So, no edges are related by the gluing relation?  That seems wrong.


i1(A^B) = i1(p(A)) = i2(m(A)) = i2(W)
i1(A^B) = i1(p(B)) = i2(m(B)) = i2(X)
i1(C^D) = i1(p(C)) = i2(m(B)) = i2(Y)
i1(C^D) = i1(p(D)) = i2(m(B)) = i2(Z)

To read: "Relabelling in Graph Transformation" Annegret Habel and Detlef Plump




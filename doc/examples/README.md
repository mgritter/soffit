## Examples of using Soffit ##

### Building a chain of nodes ###

A simple example that just adds nodes in a line.

![chain example](chain.svg)

[source](chain.json)

### Tree ###

A branching structure, demonstrating the use of Graphviz attributes as tags.

![tree example](tree.svg)

[source](tree.json)

### Tracery ###

Translation of a [Tracery](http://tracery.io/) grammar into Soffit:

![tracery example](tracery.svg)

[source](tracery.json)

### Grid ###

Building a grid

![grid example](grid.svg)

[source](grid.json) -- [notes](grid.md)

### Fixed-sized binary trees ###

Demonstration of using a countdown timer to terminate the growth of the binary tree after a
given number of nodes have been added.  Three examples from the same grammar are shown.

1 | 2 | 3
---- | ---- | ----
![binary tree example](countdown-1.svg) | ![binary tree example](countdown-2.svg) | ![binary tree example](countdown-3.svg)

[source](countdown.md)

### Rule 30 Cellular Automaton ###

This grammar creates a fixed-sized grid using the techniques from the previous two examples, then
implements a 1-d ceullar automaton on the result.

The "cursor" tag moves across the row adding one "x" at a time:

```
   eXe
  SXC

   eXe
  SXXC

   eXe
  SXXXC
```

At the end of a row, a rule caps it with an end marker and starts a new row
below the "S", if there are any "row" tags left to consume.

```
   eXe
  eXXXe
 SXC
```

This rule is illustrated below:

left graph | right graph
--- | ----
![left](1d-cellular-left.svg) | ![right](1d-cellular-right.svg)

The example here has been run through three different rule sets to apply
styles to the edges (still present, but colored white so they don't show)
and to the nodes.

![rule 30 example](1d-cellular-rule30.svg)

[source](1d-cellular-rule30.json)

[edge styling](1d-cellular-display-edges.json)

[node styling](1d-cellular-rule30-display.json)

Command line:

```
python -m soffit.application -i 3000 doc/examples/1d-cellular-rule30.json \
   doc/examples/1d-celluar-display-edges.json \
   doc/examples/1d-cellular-display.json
```

### Cyclic Generation ###

In "Procedural Generation in Game Design" (Tanya X. Short and Tarn Adams, editors), Dr. Joris Dormans gives a simple example of a set of graph generation rules on page 88 that implement a lock-and-key puzzle.

I don't have "embedded" nodes like his example shows, and instead used a
separate node for the lock and key, with tagged edges showing the relationship.

![Dormans example](dormans-pggd.svg)

[source code](dormans-pggd.json)

### Random Pentominos ###

A pentomino can be viewed as either a chain 1-2-3-4-5 or a forked chain 1-2-3-4 3-5.  (Some shapes can be represented both ways.)  So we can generate
random pentominos on a grid by matching these two patterns with
previously-unmatched squares.  Without wildcarding, it's difficult to generate
a lot of different colors.

![Three pentominos on a 5x5 grid](pentomino.svg)

[source code](pentomino.json)



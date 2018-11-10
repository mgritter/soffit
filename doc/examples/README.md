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

The example has been edited to apply graphviz styles for 0 and 1, which could be done with a separate rule set.

![rule 30 example](1d-cellular-rule30.svg)

[source](1d-cellular-rule30.json)


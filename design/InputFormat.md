# Ideas for input format

## general properties
  * how to distinguish variables from literals--- do we even want to support tag variables?
  * how to make very compact and easy to write, short ramp-up time, lack of boilerplate?
  * graph notation should name vertices, name edges by putting them in between, like dot

## Dot
  * Well-known graph format, easy to plot with graphviz
  * Supports attaching labels
  * Would need to extend format
  * pydot parsing library exists
  
## JSON
  * more tracery-like
  * larger existing toolchain
  * more compatible with JavaScript if ported to a front-end library
  * closer to Tracery inspiration

## Examples

```javascript
{
   "start" : "A-B-C-A",
   "A" : "A-B-C-A",
   "A-B-C-A-D-E-A" : "A-B-A-D-A"
}
```

Allow "don't care", which is distinct from all other symbols (including itself):

```javascript
{
   "start" : "A-*-*-A",
   "A" : "A-*-*-A",
   "A-B-*-A-D-*-A" : "A-B-A-D-A"
}
```

Directed graphs?  Use -- for undirected and -> for directed like dot?

```javascript
{
   "start" : "A->B",
   "A->B" : "A->B,A->C",
   "A->B->C->D" : "A->B->C->D, A->D"
}
```

Alternatives: use list, like Tracery

```javascript
{
   "start" : "A--B",
   "A--B" : [ "A--B--C--A", 
              "A--B,A--C,A--D" ] 
}
```

Tags: use square brackets and lowercase?
Or use something else to distinguish from alternative notation?
Period? works well for nodes but not edges.  Alow --foo-- or -foo- or -foo> or --foo->?

```javascript
{
   "start" : "A.root",
   "A.root" : "A.root -1> internal",
   "X.internal" : "X.internal -2-> Y.leaf",
   "X -2-> Y" : "X -3-> Y",
   "Z-{2}->Z" : "Z",
}
```

A--X->Y is ambiguous wether it's A--X and X->Y or A->Y with label X.

Require spacing? Meh.
Require small vs. capital? Maybe.
Small vs. capital, with {} as an escape mechanism?

What about ways to represent variable attributes?  Can't use {} for
disambiguation *and* for that.

Could require a prefix for variable labels.

```javascript
{
   "Z-#x->Z" : "Z-->Z, A-#x->Z, Z-#x->B",
   "Z-$x->Z" : "Z-->Z, A-$x->Z, Z-$x->B",
   "Z-{$x}->Z" : "Z-->Z, A-{$x}->Z, Z-{$x}->B",
}
```

${x} vs {$x}?  Bash-like syntax?

Could have special operators

${x:something}
$x$increment
{$x something pipeline blah}

I need some way to represent non-injective mappings.  For example, the rule

A => C
B => C
A--B => C--C


that turns two nodes connected by an edge into a single node with a self-loop.

One idea:

```javascript
{
   "A--B" : "AB--AB",
}
```

This seems ambiguous, but if the convention is that source rules are single
letters than it's clear. What about somebody who wants to do

```javascript
{
   "X10-10-Y10" : "X10Y10-10-X10Y10",
}
```

I think we could live with this, but now the parsing needs to be semantically
dependent.  Other ideas:

Double-arrow to represent merging explicitly as L=>R

```javascript
{
   "A--B" : "B=>A",
}
```

Addition or other symbol to represent merging as the "new object"

```javascript
{
   "A--B" : "A+B--A+B",
   "A--B" : "A^B--A^B",
}
```

Write rename rules on the *left* instead of the right?

```javascript
{
   "A--B[A]" : "A",
   "A--B>A" : "A",   // this is ambiguous with an labelled edge?
   "A,B[A]" : "A",

}
```


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
Period? works well for notes but not edges.  Alow --foo-- or -foo- or -foo> or --foo->?

```javascript
{
   "start" : "A.root",
   "A.root" : "A.root -1> internal",
   "X.internal" : "X.internal -2-> Y.leaf",
   "X -2-> Y" : "X -3-> Y"
}
```

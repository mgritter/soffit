## Building a grid

Allowing a graph to be expanded at arbitrary locations tends not to respect the
geometry of the plane.  A better approach if we want a regular pattern is to only allow
expansion at a particular point.

```
 c-c-^
 | | |
 c-c--

     <-c
     | |
 c-e-e--
 | | | |
 -------

   <---c
   | | |
 c-e-i--
 | | | |
 -------

 <-----c
 | | | |
 c-i-i--
 | | | |
 -------

 c-------c
 | | | | |
 v-e-i-i--
   | | | |
   e------
   | | | |
   c------

 c-------c
 | | | | |
 --i-i-i--
 | | | | |
 --i------
 | | | | |
 V-c------

 c-------c
 | | | | |
 --i-i-i--
 | | | | |
 --i------
 | | | | |
 --e------
 | |
 c->


 --i------
 | | | | |
 --e-----c A
 | | | | | 
 c-------> B

 --i------
 | | | | |
 --i------
 | | | | |
 --e-----e-^
 | | | | | |
 c---------c
```

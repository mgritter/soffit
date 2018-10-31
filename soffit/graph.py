"""Graph manipulation functions."""
#
#   soffit/graph.py
#
#   Copyright 2018 Mark Gritter
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import networkx as nx
from constraint import *
from soffit.constraint import *
import itertools
import time

def graphIdentifiersToNumbers( g ):
    """Replace the graph identified by strings, with one where all nodes
    are integers.  The graph nextNodeId attribute will be used to allocate
    new node IDs as we evolve the grammar."""

    ret = nx.convert_node_labels_to_integers( g )
    nextId = max( ret.nodes ) + 1
    ret.graph['nextId'] = nextId
    return ret

class RightHandGraph(object):
    def __init__( self, right  ):
        self.right = right
        self.join = right.graph['join']
        self.rename = right.graph['rename']
        
    def ruleDeletions( self, left ):
        """Return nodes and edges deleted by this left-right pair.
        Returned as a tuple (nodes, edges)."""

        # Rename contains all nodes on the right, merged or not, so
        # any node *not* present is deleted.
        dn = [ n for n in left.nodes if
               n not in self.rename ]

        de = [ e for e in left.edges if
               ( self._joinedVersionOfEdge( e ) not in self.right.edges ) ]

        return (dn, de)

    def _joinedVersionOfEdge( self, e ):
        (a,b) = e
        # Edges may be to a node which is deleted.
        return ( self.rename.get( a, None ),
                 self.rename.get( b, None ) )

class MatchError(Exception):
    def __init__( self, message ):
        self.message = message

class MatchFinder(object):
    """
    An object which finds matches for graph grammar rules.
    """
    def __init__( self, graph, verbose = False ):
        """Initialize the finder with the graph in which matches are to 
        be found."""
        
        # Relabel for compactness, nodes numbered 0..(n-1)
        self.graph = nx.convert_node_labels_to_integers( graph, label_attribute="orig" )

        self.model = Problem()
        self.impossible = False
        self.verbose = verbose

    def checkCompatible( self, lr ):
        if nx.is_directed( self.graph ) != nx.is_directed( lr ):
            raise MatchError( "Convert both graphs to directed first." )
        
    def leftSide( self, leftGraph ):        
        """Specify the left side of a rule; that is, a graph to match."""
        self.checkCompatible( leftGraph )

        self.left = leftGraph
        maxVertex = max( self.graph.nodes )

        # Build a variable for each vertex that must be matched.
        # The convention is to allow non-injective matches, so
        # two variables could match to the same vertex.
        for n in leftGraph.nodes:
            # FIXME: how permissive is this on what may be in a string?
            self.model.addVariable( n, range( 0, maxVertex + 1 ) )

            # Add a contraint to only assign to nodes with identical tag.
            # FIXME: no tag is *not* a wildcard, does that match expectations?
            tag = leftGraph.nodes[n].get( 'tag', None )
            matchingTag = [ (i,) for i in self.graph.nodes
                            if self.graph.nodes[i].get( 'tag', None ) == tag ]
            if self.verbose:
                print( "node", n, "matchingTag", matchingTag )
            if len( matchingTag ) == 0:
                self.impossible = True
                return

            # If node choice is unconstrained, don't bother adding it as
            # a constraint!
            if len( matchingTag ) != len( self.graph.nodes ):
                self.model.addConstraint( TupleConstraint( matchingTag ),
                                          [n] )

        # Add an allowed assignment for each edge that must be matched,
        # again limiting to just exact matching tags.
        for (a,b) in leftGraph.edges:
            tag = leftGraph.edges[a,b].get( 'tag', None )
            
            matchingTag = [ i for i in self.graph.edges
                            if self.graph.edges[i].get( 'tag', None ) == tag ]
            if self.verbose:
                print( "edge", (a,b), "matchingTag", matchingTag )
            if len( matchingTag ) == 0:
                self.impossible = True
                return

            # Allow reverse matches if the graph is undirected
            if not nx.is_directed( leftGraph ):
                revEdges = [ (b,a) for (a,b) in matchingTag ]
                matchingTag += revEdges

            self.model.addConstraint( TupleConstraint( matchingTag ),
                                      [ a, b ] )
                                              
            
    def rightSide( self, rightGraph ):        
        """Specify the right side of a rule; if the rule deletes nodes,
        this restricts further which matches may be made.

        A node which is deleted cannot be an endpoint of an edge that is
        not explicitly deleted.

        If A is being deleted and is matched to node B, then no node which
        is not also being deleted can be matched to node B.
        """
        self.checkCompatible( rightGraph )
        self.right = RightHandGraph( rightGraph )
        
        # Bail out early if we already decided no match is present.
        if self.impossible:
            return

        (dn,de) = self.right.ruleDeletions( self.left  )
        self.deletedNodes = dn
        self.deletedEdges = de
        
        # The problem with getting ruleDeletions back as a list is that
        # the list isn't smart enough to tell whether directed and undirected
        # are the same thing, so... make a doubled set to check membership.
        if nx.is_directed( rightGraph ):
            deletedEdgeSet = set( de )
        else:
            deletedEdgeSet = set( de + [ (b,a) for (a,b) in de ] )

        # "danging condition"
        # If a node is deleted, then any node with the same endpoint must
        # be explicitly deleted as well.
        # For all n in G that are the image of a deleted node (in L)
        #   if s(e) = n or t(e) = n for an edge e in G, then
        #       e is the image in G of some deleted edge (in L)
        #
        # Example:
        # rule: X--A => A
        # graph: 1--2, 1--3, 1--4
        # if X = 1, then 1--2, 1--3, 1--4 must all be mapped to deleted edges
        # If X = 2, then 1--2 must be deleted as well, so A = 2

        # n = label on deleted node in left graph
        for n in dn:
            indicators = []
            # i = which graph node was picked
            possible = False
            for i in self.graph.nodes:
                if nx.is_directed( self.graph ):
                    raise MatchError( "Directed graphs not yet supported." )
                else:
                    if self._danglingUndirected( n, i ):
                        possible = True

            if not possible:
                self.impossible = True
                return
                
    def _danglingUndirected( self, n, i ):
        # Could have a self-loop, let's treat it specially
        deletedAdjacentEdges = \
            [ (a,b) for (a,b) in self.deletedEdges if a == n and b != n ] + \
            [ (b,a) for (a,b) in self.deletedEdges if b == n and a != n ]

        if len( deletedAdjacentEdges ) == 0:
            # Condition does not apply!
            return True
        
        graphAdjacent = self.graph[i]

        # OK, an easy case: does N have a self-loop?
        if (n,n) in self.deletedEdges:
            # Does i lack a self-loop?
            if i not in graphAdjacent:
                # Then impossible to match.
                if self.verbose:
                    print( "{} => {} is impossible, no self-loop".format( n, i ) )
                self.model.addConstraint( NotInSetConstraint([i]), [n] )
                return False

        # We already covered the other direction-- i is already rejected
        # if the left graph has a self-loop for n, and i does not have a
        # self-loop.

        # Match nodes from from deletedAdjacentEdges with neighbors in the graph
        # Mapping doesn't have to be injective, but it does have to
        # be surjective.  So, if too many neighbors, can't be a match!
        # 1--1 is a match for A--B; A--C; A--D => B; C; D with A=1
        # 1--1; 1--2; 1--3 can't be a match for A--B => B  with A=1

        neighborVars = [ t for (_,t) in deletedAdjacentEdges ]

        if len( graphAdjacent ) > len( neighborVars ):
            # Can't be surjective
            if self.verbose:
                print( "{} => {} is impossible, not surjective".format( n, i ) )
            self.model.addConstraint( NotInSetConstraint([i]), [n] )
            return None

        values = list( surjectiveMappings( len( neighborVars ),
                                           list( graphAdjacent ) ) )
        if self.verbose:
            print( "When {} = {}:".format( n, i ) )
            print( " ".join( "{:>6}".format( str( x ) ) for x in neighborVars ) )
            print( "|".join( "------" for x in neighborVars ) )
            for v in values:
                print( " ".join( "{:6}".format( y ) for y in v ) )
            print()
            

        self.model.addConstraint( ConditionalConstraint(i, TupleConstraint( values )),
                                  [n] + neighborVars )
        return True

    def _convertNodes( self, soln ):
        return { k : self.graph.nodes[v]['orig']
                 for (k,v) in soln.items() }
        
    def matches( self ):
        if self.impossible:
            return []
        
        start = time.time()
        solns = self.model.getSolutions()
        end = time.time()

        if self.verbose:
            print( "{} matches in {:.3f} seconds.".format( len( solns ),
                                                          end - start ) )
        
        return [ Match(self._convertNodes(s)) for s in solns ]
    

class Match(object):
    """A Match object contains mappings from nodes in the left-hand side
    to nodes in the target graph.
    (It's a graph morphism!)"""
    def __init__( self, soln = None ):
        if soln is None:
            self.nodeMap = {}
            self.frozen = False
        else:
            self.nodeMap = soln
            self.frozen = True
        
    def addMap( self, leftNode, graphNode ):
        if self.frozen:
            raise MatchError( "Match modified after it was hashed." )
        self.nodeMap[leftNode] = graphNode

    def node( self, leftNode ):
        return self.nodeMap[leftNode]

    def edge( self, e ):
        (s, t) = e
        return ( self.nodeMap[s], self.nodeMap[t] )

    def __str__( self ):
        morphism = [ "{}=>{}".format( l, g )
                     for ( l , g ) in self.nodeMap.items() ]
        return "{ " + ", ".join( morphism ) + " }"

    def __repr__( self ):
        return "Match(" + self.__str__() + ")"

    def __eq__( self, other ):
        return isinstance( other, Match ) and \
            self.nodeMap == other.nodeMap

    def __hash__( self ):
        self.frozen = True
        return hash( tuple( sorted( self.nodeMap.items() ) ) )

def surjectiveMappings( k, values, optional=[] ):
    """Enumerate all the ways to select k distinct items from 'values' such that
    all values appear at least once."""
    if k < len( values ):
        return
    elif k == 1:
        if len( values ) == 1:
            yield (values[0],)
        else:
            for o in optional:
                yield (o,)

    # Pick a must-use, it becomes optional
    for i in range(len(values)):
        selected = values[i]
        for m in surjectiveMappings( k-1,
                                     values[:i] + values[i+1:], 
                                     optional + [selected] ):
            yield (selected,) + m

    # Pick a may-use
    for selected in optional:
        for m in surjectiveMappings( k-1,
                                     values, 
                                     optional ):
            yield (selected,) + m
        
            
        
            


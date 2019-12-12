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
    if len( ret.nodes ) > 0:        
        nextId = max( ret.nodes ) + 1
        ret.graph['nextId'] = nextId
    else:
        ret.graph['nextId'] = 0
        
    return ret

def allocateNewNode( g, tag = None ):
    """Allocate a new numeric node in the graph, based on its nextId attribute.
    Such graphs are created by graphIndentifiersToNumbers."""
    
    if not 'nextId' in g.graph:
        raise MatchError( "Graph must come from graphIndentifiersToNumbers." )

    n = g.graph['nextId']
    g.graph['nextId'] = n + 1
    if tag is None:
        g.add_node( n )
    else:
        g.add_node( n, tag = tag )

    return n

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
        
        self.originalGraph = graph
        # Relabel for compactness, nodes numbered 0..(n-1)
        self.graph = nx.convert_node_labels_to_integers( graph, label_attribute="orig" )

        self.model = Problem()
        self.impossible = False
        self.verbose = verbose

        self.currentConstraintVariables = None
        self.currentConstraintTuples = None
        
        self.maxMatches = 100000
        self.maxMatchTime = 60.0

    def checkCompatible( self, lr ):
        if nx.is_directed( self.graph ) != nx.is_directed( lr ):
            raise MatchError( "Convert both graphs to directed first." )
        
    def leftSide( self, leftGraph ):        
        """Specify the left side of a rule; that is, a graph to match."""
        self.checkCompatible( leftGraph )

        # FIXME: handle zero-length left graphs?
        self.left = leftGraph
        maxVertex = max( self.graph.nodes )

        # Build a variable for each vertex that must be matched.
        # We will use injective matching only, as it's more expessive and probably
        # easier to understand.
        for n in leftGraph.nodes:
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

        self.model.addConstraint( AllDifferentConstraint(), list( leftGraph.nodes ) )

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
                                              
    def addConditionalTupleConstraint( self, first, rest, variables ):
        if self.currentConstraintVariables != variables:
            self.finishTupleConstraint()
            self.currentConstraintVariables = variables
            self.currentConstraintTuples = []

        for r in rest:
            self.currentConstraintTuples.append( (first,) + r )

    def finishTupleConstraint( self ):
        if self.currentConstraintVariables is None:
            return
        
        if self.verbose:
            vs = self.currentConstraintVariables
            print( "If    |Then" )
            print( " ".join( "{:>6}".format( str( v ) ) for v in vs ) )
            print( "|".join( "------" for v in vs ) )
            for t in self.currentConstraintTuples:
                print( " ".join( "{:6}".format( y ) for y in t ) )
                
        self.model.addConstraint(
            ConditionalTupleConstraint( self.currentConstraintTuples ),
            self.currentConstraintVariables
        )

        self.currentConstraintVariables = None
        self.currentConstraintTuples = []
        
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
        if self.verbose:
            print( "Deleted nodes:", dn )
            print( "Deleted edges:", de )
        
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
        #
        # n = label on deleted node in left graph
        for n in dn:
            indicators = []
            # i = which graph node was picked
            possible = False
            for i in self.graph.nodes:
                # We waste a lot of time constructing these
                # conditions if they're impossible anyway.
                #
                # We *could* just pass in a function rather than a table
                # constraint, since our backend is pyconstraint.  But that
                # wouldn't be very portable back to a SAT-based solver.
                tag = self.left.nodes[n].get( 'tag', None )
                if self.graph.nodes[i].get( 'tag', None ) != tag:
                    continue
                        
                if nx.is_directed( self.graph ):
                    if self._danglingDirected( n, i ):
                        possible = True
                else:
                    if self._danglingUndirected( n, i ):
                        possible = True

            if not possible:
                self.impossible = True
                return

            self.finishTupleConstraint()

        # Fossil code: keep to allow non-injective matching as an option?
        #
        #if nx.is_directed( self.graph ):
        #    raise MatchError( "Directed graphs not yet supported." )
        #else:
        #    self._identificationUndirected()
            

    def _identificationUndirected( self ):
        """Restrict matches of deleted nodes and deleted edges,
        to nodes and edges that are not matched with undeleted nodes
        and undeleted edges."""
        dn = self.deletedNodes
        de = self.deletedEdges
        un = [ n for n in self.left.nodes if n not in dn ]
        ue = [ (a,b) for (a,b) in self.left.edges if
               ( (a,b) not in de and (b,a) not in de ) ]

        # In the technical report [Martini 1996] this condition is
        # restricted further, that two left-nodes may not be mapped to the
        # same node of if either is deleted.
        # I don't understand this restriction; it seems OK that if A and B
        # are both being deleted, to allow A->x and B->x simultaneously?

        # Two nodes may only be identified if they are both deleted, or both
        # undeleted.
        if self.verbose:
            print( "Nonoverlapping node sets:" )
            print( "A=", dn )
            print( "B=", un )
        self.model.addConstraint( NonoverlappingSets( dn, un ),
                                  dn + un )

        if self.verbose:
            print( "Nonoverlapping edge sets:" )
            print( "A=", de )
            print( "B=", ue )
        edgeVars = list( set( itertools.chain.from_iterable( de + ue ) ) )
        # Two edges may only be identified if they are both deleted, or both
        # undeleted.
        self.model.addConstraint( NonoverlappingUnorderedPairs( de, ue ),
                                  edgeVars )
            
    def _danglingUndirected( self, n, i ):
        """Restrict matches of deleted node n to graph node i,
        only to those which leave no undeleted edges dangling."""

        # Could have a self-loop, let's treat it specially
        deletedAdjacentEdges = \
            [ (a,b) for (a,b) in self.deletedEdges if a == n and b != n ] + \
            [ (b,a) for (a,b) in self.deletedEdges if b == n and a != n ]

        graphAdjacent = self.graph[i]

        # Does i have a self-loop but N does not?
        if i in graphAdjacent:
            if (n,n) not in self.deletedEdges:
                # Then impossible to match.
                if self.verbose:
                    print( "{} => {} is impossible, no self-loop".format( n, i ) )
                self.model.addConstraint( NotInSetConstraint([i]), [n] )
                return False
            
            # Remove self loop from consideration for the rest of the code.
            graphAdjacent = [ x for x in graphAdjacent if x != i ]

        # An easy case: does i have too many edges for the rule to delete
        # them all?
        if len( graphAdjacent ) > len( deletedAdjacentEdges ):
            if self.verbose:
                print( "{} => {} is impossible, too many neighbors".format( n, i ) )
                print( "graphAdjacent", graphAdjacent )
                print( "deletedAdjacentEdges", deletedAdjacentEdges )

            self.model.addConstraint( NotInSetConstraint([i]), [n] )
            return False

        # FIXME: write a test for ordering of these two conditions.
        # Are there no incident edges, and we didn't expect any?
        if len( graphAdjacent ) == 0 and len( deletedAdjacentEdges ) == 0:
            return True
            
        # We already covered the other direction-- i is already rejected
        # if the left graph has a self-loop for n, and i does not have a
        # self-loop.

        # Match nodes from from deletedAdjacentEdges with neighbors in the graph
        # Mapping doesn't have to be injective, but it does have to
        # be surjective.  So, if too many neighbors, can't be a match!
        # 1--1 is a match for A--B; A--C; A--D => B; C; D with A=1
        # 1--1; 1--2; 1--3 can't be a match for A--B => B  with A=1

        neighborVars = [ t for (_,t) in deletedAdjacentEdges ]

        # FIXME: is this redundant?
        # I suspect it is because it returned "None" previously....
        if len( graphAdjacent ) > len( neighborVars ):
            # Can't be surjective
            if self.verbose:
                print( "{} => {} is impossible, not surjective".format( n, i ) )
            self.model.addConstraint( NotInSetConstraint([i]), [n] )
            return False

        # FIXME: this allows multiple assignments to the same adjacency,
        # which is not possible in an injective mapping.
        values = list( surjectiveMappings( len( neighborVars ),
                                           list( graphAdjacent ) ) )
        self.addConditionalTupleConstraint( i, values, [n] + neighborVars )
        return True

    def _danglingDirected( self, n, i ):
        """Restrict matches of deleted node n to graph node i,
        only to those which leave no undeleted edges dangling,
        on a directed graph."""

        # Could have a self-loop, let's treat it specially
        deletedOutgoingEdges = [ (a,b) for (a,b) in self.deletedEdges if a == n and b != n ]
        deletedIncomingEdges = [ (a,b) for (a,b) in self.deletedEdges if b == n and a != n ]
        graphPred = list( x for x in self.graph.predecessors( i ) if x != i )
        graphSucc = list( x for x in self.graph.successors( i ) if x != i )

        # An easy case: does i have too many edges for the rule to delete
        # them all?
        if len( graphPred ) > len( deletedIncomingEdges ) or \
           len( graphSucc ) > len( deletedOutgoingEdges ):
            if self.verbose:
                print( "{} => {} is impossible, too many neighbors".format( n, i ) )
            self.model.addConstraint( NotInSetConstraint([i]), [n] )
            return False

        # Another easy case: does i have a self-loop but N does not?
        if (i,i) in self.graph.edges():
            if (n,n) not in self.deletedEdges:
                # Then impossible to match.
                if self.verbose:
                    print( "{} => {} is impossible, no self-loop".format( n, i ) )
                self.model.addConstraint( NotInSetConstraint([i]), [n] )
                return False

        # Match nodes surjectively from predecessors to incomingEdges
        # and from successors to outgoingEdges
        
        succVars = [ t for (_,t) in deletedOutgoingEdges ]
        predVars = [ t for (t,_) in deletedIncomingEdges ]

        for ( neighborVars, graphAdjacent ) in \
            [ ( succVars, graphSucc ),
              ( predVars, graphPred ) ]:

            if len( neighborVars ) == 0 and len( graphAdjacent ) == 0:
                # Trivially satisfied
                continue
            
            values = list( surjectiveMappings( len( neighborVars ),
                                               graphAdjacent ) )
            if len( values ) == 0:
                if self.verbose:
                    print( "{} => {} is impossible, not surjective".format( n, i ) )
                self.model.addConstraint( NotInSetConstraint([i]), [n] )
                return False
                
            self.addConditionalTupleConstraint( i, values, [n] + neighborVars )
                        
        return True

    def _convertNodes( self, soln ):
        return { k : self.graph.nodes[v]['orig']
                 for (k,v) in soln.items() }

    def matchExists( self ):
        """Return true if at least one match exists."""
        if self.impossible:
            return False

        x = self.model.getSolutionIter()
        try:
            next( x )
            return True
        except StopIteration:
            return False
        
    def matches( self ):
        if self.impossible:
            return []

        self.endReason = "Maximum matches reached."
        start = time.time()
        solns = []
        x = self.model.getSolutionIter()
        while len( solns ) < self.maxMatches:
            try:
                solns.append( next( x ) )
                if time.time() - start > self.maxMatchTime:
                    self.endReason = "Maximum time exceeded."
                    break
            except StopIteration:
                self.endReason = "No more matches."
                break
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

    def __contains__( self, n ):
        return n in self.nodeMap
    
    def __hash__( self ):
        self.frozen = True
        return hash( tuple( sorted( self.nodeMap.items() ) ) )

    def copy( self ):
        # copy is unfrozen
        m = Match()
        m.nodeMap = self.nodeMap.copy()
        return m
        
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
        
            
class RuleApplication(object):
    """Apply a rule to a graph where it has been matched."""
    
    def __init__( self, finder, match ):
        """Create a RuleApplication using a MatchFinder and a 
        Match that it produced."""
        self.finder = finder

        self.left = finder.left
        # The networkx graph, not the RightHandGraph object
        self.right = finder.right.right
        self.rename = finder.right.rename
        self.join = finder.right.join
        
        self.match = match.copy()
        self.beforeGraph = finder.originalGraph

    def verify( self ):
        gTest = self.beforeGraph.copy()
        for e in self.finder.deletedEdges:
            (m_s,m_t) = self.match.edge( e )
            assert (m_s,m_t) in gTest.edges, "Missing edge " + str( e ) + " => " + str((m_s,m_t))

        for n in self.finder.deletedNodes:
            m_n = self.match.node( n )
            assert m_n in gTest.nodes, "Missing node " + str( n )  + " => " + str(m_n)

        self._deleteEdges( gTest )

        for n in self.finder.deletedNodes:
            m_n = self.match.node( n )
            assert len( gTest[m_n] ) == 0, "Remaining edges on " + str( n )  + " => " + str(m_n)

    def _deleteEdges( self, g ):
        alreadyDeleted = set()
        for e in self.finder.deletedEdges:            
            m_e = self.match.edge( e )
            if m_e not in alreadyDeleted:
                (m_s, m_t) = m_e
                g.remove_edge( m_s, m_t )
                alreadyDeleted.add( m_e )
                if not nx.is_directed( g ):
                    alreadyDeleted.add( (m_t, m_s) )
        
    def _deleteNodes( self, g ):
        alreadyDeleted = set()
        for n in self.finder.deletedNodes:
            m_n = self.match.node( n )
            if m_n not in alreadyDeleted:
                g.remove_node( m_n )
                alreadyDeleted.add( m_n )

    def _mergeNodes( self, g ):
        # The label on the combined edge will be placed in _retagEdge
        # And the label on the combined node will be placed in _retagNode
        #
        # So our job is limited to ensuring any edges that terminate on a merged
        # node are routed to the correct place.
        # join has just the nodes that need to be changed
        # rename has the canonical renaming
        alreadyMerged = set()

        for v in self.join:
            u = self.rename[ v ]
            try:
                m_u = self.match.node( u )
                m_v = self.match.node( v )
            except KeyError:
                # A merge was specified for a node introduced in the right-hand
                # side of the rule.
                # Add an alias as if it were specified in the left-hand side.
                if u not in self.left:
                    self.match.addMap( u, self.match.node( v ) )
                    continue
                elif v not in self.left:
                    self.match.addMap( v, self.match.node( u ) )
                    continue
                else:
                    assert False
                
            # Matching could have identified two nodes that are both to be merged
            # or are already merged!            
            if m_v != m_u and m_v not in alreadyMerged:
                g = nx.algorithms.minors.contracted_nodes( g, m_u, m_v, self_loops = True )
                alreadyMerged.add( m_v )
        return g

    def _addNode( self, g, n ):
        r_n = self.right.nodes[n]
        new_n = allocateNewNode( g, r_n.get( 'tag', None ) )
        self.match.addMap( n, new_n )
        
    def _retagNode( self, g, n ):
        r_n = self.right.nodes[n]
        
        m_n = self.match.node( n )
        g_n = g.nodes[m_n]

        if 'tag' in r_n:
            g_n['tag'] = r_n['tag']
        elif 'tag' in g_n:
            del g_n['tag']
    
    def _addAndRelabelNodes( self, g ):
        # FIXME: this is dumb, add 'nodes' to RightHandGraph
        for rightNode in self.right.nodes:
            if rightNode in self.match:
                # It must have been in left, too, but the tag may have changed
                self._retagNode( g, rightNode )
            else:
                self._addNode( g, rightNode )

    def _addEdge( self, g, e ):
        (m_s, m_t) = self.match.edge( e ) 
        r_e = self.right.edges[e]
        g.add_edge( m_s, m_t, **r_e )

    def _retagEdge( self, g, e ):        
        r_e = self.right.edges[e]
        
        m_e = self.match.edge( e )
        g_e = g.edges[m_e]

        if 'tag' in r_e:
            g_e['tag'] = r_e['tag']
        elif 'tag' in g_e:
            del g_e['tag']
            
    def _addAndRelabelEdges( self, g ):
        for (a,b) in self.right.edges:
            # Should have already added the endpoints if they are new
            assert a in self.match
            assert b in self.match
            if (a,b) in self.left.edges:
                self._retagEdge( g, (a,b) )
            else:
                self._addEdge( g, (a,b) )
        
    def result( self ):
        if __debug__:
            self.verify()
            
        g = self.beforeGraph.copy()
        self._deleteEdges( g )
        self._deleteNodes( g )
        g = self._mergeNodes( g )
        self._addAndRelabelNodes( g )
        self._addAndRelabelEdges( g )

        return g
        

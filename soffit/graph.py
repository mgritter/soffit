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
from ortools.sat.python import cp_model
import time

def graphIdentifiersToNumbers( g ):
    """Replace the graph identified by strings, with one where all nodes
    are integers.  The graph nextNodeId attribute will be used to allocate
    new node IDs as we evolve the grammar."""

    ret = nx.convert_node_labels_to_integers( g )
    nextId = max( ret.nodes ) + 1
    ret.graph['nextId'] = nextId
    return ret

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
        self.model = cp_model.CpModel()
        self.variables = {}
        
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
            v = self.model.NewIntVar( 0, maxVertex, n )
            self.variables[n] = v

            # Add a contraint to only assign to nodes with identical tag.
            # FIXME: no tag is *not* a wildcard, does that match expectations?
            tag = leftGraph.nodes[n].get( 'tag', None )
            matchingTag = [ i for i in self.graph.nodes
                            if self.graph.nodes[i].get( 'tag', None ) == tag ]
            if self.verbose:
                print( "node", n, "matchingTag", matchingTag )
            if len( matchingTag ) == 0:
                self.impossible = True
                return

            # If node choice is unconstrained, don't bother adding it as
            # a constraint!
            if len( matchingTag ) != len( self.graph.nodes ):
                self.model.AddAllowedAssignments(
                    [v],
                    [ (x,) for x in matchingTag ] )

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

            self.model.AddAllowedAssignments( [self.variables[a], self.variables[b]],
                                              matchingTag )
            
    def rightSide( self, rightGraph ):        
        """Specify the right side of a rule; if the rule deletes nodes,
        this restricts further which matches may be made.

        A node which is deleted cannot be an endpoint of an edge that is
        not explicitly deleted.

        If A is being deleted and is matched to node B, then no node which
        is not also being deleted can be matched to node B.
        """

        # Bail out early if we already decided no match is present.
        if self.impossible:
            return
        
        pass
    
    def matches( self ):
        if self.impossible:
            return []
        
        callback = MatchAggregator( self )
        solver = cp_model.CpSolver()
        # print( self.model.ModelProto() )

        start = time.time()
        status = solver.SearchForAllSolutions( self.model, callback )
        end = time.time()

        # print( solver.ResponseStats() )
        
        if self.verbose:
            print( "{} matches in {:.3f} seconds.".format( len( callback.matches ),
                                                          end - start ) )
        return list( callback.matches )
    

class Match(object):
    """A Match object contains mappings from nodes in the left-hand side
    to nodes in the target graph.
    (It's a graph morphism!)"""
    def __init__( self ):
        self.nodeMap = {}
        self.frozen = False
        
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

class MatchAggregator( cp_model.CpSolverSolutionCallback ):
    """Callback implementation for cp_model that gets solutions one at 
    a time; aggregate them into a list."""
    def __init__( self, finder ):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.nodes = 0
        self.finder = finder
        self.variables = finder.variables
        self.renumberedGraph = finder.graph

        self.matches = set()

    def OnSolutionCallback( self ):
        try:
            # variables[n], where n is a node from finder.left,
            # contains the number of the node in the renumbered graph.
            # Its original name is in graph.nodes[i]['orig']
            m = Match()

            for (lhNode, modelVariable) in sorted( self.variables.items() ):
                renumberedNode = self.Value( modelVariable )
                origNode = self.renumberedGraph.nodes[renumberedNode]['orig']
                m.addMap( lhNode, origNode )

            # The use of a set is a hack around the solver returning
            # the same solution multiple times.
            self.matches.add( m )
        except Exception as e:
            # The C++ library chokes if we throw an exception, but doesn't
            # print it!
            print( repr( e ) )
            raise e

            
            


"""Test matching and replacement, using Hypothesis."""
#
#   test/test_match_hyp.py
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

import unittest
import soffit.graph as sg
import networkx as nx
from hypothesis import given, assume, note, reproduce_failure, settings
import hypothesis.strategies as st

nodeIds_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

nodeIds = st.sampled_from( nodeIds_list )
edgeStrategy = st.lists( st.tuples( nodeIds, nodeIds ) )
edgeStrategy1_to_10 = st.lists( st.tuples( nodeIds, nodeIds ), min_size=1, max_size=10 )
edgeStrategy0_to_10 = st.lists( st.tuples( nodeIds, nodeIds ), min_size=0, max_size=10 )

@st.composite
def undirected_subgraph_and_extra_edges( draw ):
    """Return extra edges such that at least one edge is new, and connects to existing nodes."""
    edges = draw( edgeStrategy1_to_10 )
    edgeList = [ (min(s,t), max(s,t)) for (s,t) in edges ]
    
    nodes = [ s for (s,t) in edges ] + [ t for (s,t) in edges ]
    s = draw( st.sampled_from( nodes ) )
    t = draw( nodeIds )
    newEdge = (min(s,t), max(s,t))
    assume( newEdge not in edgeList )

    moreEdges = draw( edgeStrategy0_to_10 ) + [ newEdge ]
    return (edges, moreEdges)

@st.composite
def directed_subgraph_and_extra_edges( draw ):
    """Return extra edges such that at least one edge is new, and connects to existing nodes."""
    edges = list( draw( edgeStrategy1_to_10 ) )

    nodes = [ s for (s,t) in edges ] + [ t for (s,t) in edges ]
    s = draw( st.sampled_from( nodes ) )
    t = draw( nodeIds )
    # Allow edge to go either way
    newEdge = draw( st.sampled_from( [(s, t), (t,s)] ) )
    
    assume( newEdge not in edges )

    moreEdges = draw( edgeStrategy0_to_10 ) + [ newEdge ]
    return (edges, moreEdges)

@st.composite
def disjoint_subgraphs( draw ):
    """Return graphs that contain no nodes in common."""
    edges = draw( edgeStrategy1_to_10 )
    nodes = [ s for (s,t) in edges ] + [ t for (s,t) in edges ]

    remainingIds_list = [ x for x in nodeIds_list if x not in nodes ]
    remainingIds = st.sampled_from( remainingIds_list )
    moreEdges = draw( st.lists( st.tuples( remainingIds, remainingIds ), min_size=0, max_size=10 ) )
    return (edges, moreEdges)

class TestMatchAndReplace(unittest.TestCase):
    def undirectedGraphFromEdgeList( self, edges ):
        g = nx.Graph()
        for (s,t) in edges:
            g.add_edge( s, t )
        return g

    def directedGraphFromEdgeList( self, edges ):
        g = nx.DiGraph()
        for (s,t) in edges:
            g.add_edge( s, t )
        return g
        
    @given( edgeStrategy )
    def test_match_self( self, edges ):
        # FIXME: empty graphs do cause problems, they should be fixed
        # or else error out more explicitly.
        assume( len( edges ) > 0 )
        
        l = self.undirectedGraphFromEdgeList( edges )
        g = sg.graphIdentifiersToNumbers( l )

        finder = sg.MatchFinder( g )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        m = finder.matches()

        self.assertGreaterEqual( len( m ), 1 )
        
    @given( edgeStrategy, edgeStrategy )
    def test_match_subgraph( self, edges, moreEdges ):
        assume( len( edges ) > 0 )
        assume( len( moreEdges ) > 0 )
        
        l = self.undirectedGraphFromEdgeList( edges )
        g = self.undirectedGraphFromEdgeList( edges + moreEdges )
        g = sg.graphIdentifiersToNumbers( g )

        finder = sg.MatchFinder( g )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        m = finder.matches()

        self.assertGreaterEqual( len( m ), 1 )

    def _buildRename( self, g ):
        if 'join' in g.graph:
            join = g.graph['join']
        else:
            join = {}
            g.graph['join'] = join
            
        rename = {}
        for n in g.nodes:
            rename[n] = n
        for k in join:
            orig = k
            while k in join:
                k = join[k]
            rename[orig] = k
        g.graph['rename'] = rename
        
    @given( disjoint_subgraphs() )
    @settings( deadline=200 )
    def test_delete_subgraph( self, sgs ):
        (edges, moreEdges ) = sgs

        nodesG = set( [ s for (s,t) in moreEdges ] + [ t for (s,t) in moreEdges ] )
        
        l = self.undirectedGraphFromEdgeList( edges )
        r = nx.Graph()
        self._buildRename( r )
        g_orig = self.undirectedGraphFromEdgeList( edges + moreEdges )        
        g = sg.graphIdentifiersToNumbers( g_orig )

        finder = sg.MatchFinder( g, verbose=False )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        finder.rightSide( r )
        
        m = finder.matches()
        self.assertGreater( len( m ), 0 )
        
        app = sg.RuleApplication( finder, m[0] )
        g2 = app.result()

        self.assertEqual( len( g2.nodes ), len( nodesG ) )
        
    @given( disjoint_subgraphs() )
    @settings( deadline=200 )
    def test_delete_directed_subgraph( self, sgs ):
        (edges, moreEdges ) = sgs

        nodesG = set( [ s for (s,t) in moreEdges ] + [ t for (s,t) in moreEdges ] )
        
        l = self.directedGraphFromEdgeList( edges )
        r = nx.DiGraph()
        self._buildRename( r )
        g_orig = self.directedGraphFromEdgeList( edges + moreEdges )        
        g = sg.graphIdentifiersToNumbers( g_orig )

        finder = sg.MatchFinder( g, verbose=False )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        finder.rightSide( r )
        
        m = finder.matches()
        self.assertGreater( len( m ), 0 )
        
        app = sg.RuleApplication( finder, m[0] )
        g2 = app.result()

        self.assertEqual( len( g2.nodes ), len( nodesG ) )

    @given( undirected_subgraph_and_extra_edges() )
    @settings( deadline=200 )
    def test_cant_delete_subgraph( self, ug ):
        (edges, moreEdges) = ug

        # OK, build the graph and label the edges so the deletion can only happen
        # in one way (which is disallowed)
        l = self.undirectedGraphFromEdgeList( edges )
        for (s,t) in edges:
            l.nodes[s]['tag'] = 'kill'
            l.nodes[t]['tag'] = 'kill'
            
        r = nx.Graph()
        self._buildRename( r )
        g_orig = self.undirectedGraphFromEdgeList( edges + moreEdges )
        for (s,t) in edges:
            g_orig.nodes[s]['tag'] = 'kill'
            g_orig.nodes[t]['tag'] = 'kill'                   
        g = sg.graphIdentifiersToNumbers( g_orig )

        finder = sg.MatchFinder( g, verbose=False )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        finder.rightSide( r )
        
        m = finder.matches()
        self.assertEqual( len( m ), 0 )


    @given( directed_subgraph_and_extra_edges() )
    @settings( deadline=200 )
    def test_cant_delete_directed_subgraph( self, dg ):
        (edges, moreEdges) = dg

        l = self.directedGraphFromEdgeList( edges )
        for (s,t) in edges:
            l.nodes[s]['tag'] = 'kill'
            l.nodes[t]['tag'] = 'kill'
            
        r = nx.DiGraph()
        self._buildRename( r )
        g_orig = self.directedGraphFromEdgeList( edges + moreEdges )
        for (s,t) in edges:
            g_orig.nodes[s]['tag'] = 'kill'
            g_orig.nodes[t]['tag'] = 'kill'                   
        g = sg.graphIdentifiersToNumbers( g_orig )

        finder = sg.MatchFinder( g, verbose=False )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        finder.rightSide( r )
        
        m = finder.matches()
        self.assertEqual( len( m ), 0 )


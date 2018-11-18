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
from hypothesis import given, assume, note
import hypothesis.strategies as st

nodeIds = st.text( alphabet="ABCDEFGHIJKLMNOPQRSTUVWZYZ",
                   min_size=1 )
edgeStrategy = st.lists( st.tuples( nodeIds, nodeIds ) )
                   
class TestMatchAndReplace(unittest.TestCase):
    def undirectedGraphFromEdgeList( self, edges ):
        g = nx.Graph()
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

    @unittest.skip( "Failing, bad assertion." )
    @given( edgeStrategy, edgeStrategy )
    def test_delete_subgraph( self, edges, moreEdges ):
        assume( len( edges ) > 0 )
        assume( len( moreEdges ) > 0 )
        
        l = self.undirectedGraphFromEdgeList( edges )
        r = nx.Graph()
        self._buildRename( r )
        g = self.undirectedGraphFromEdgeList( edges + moreEdges )        
        g = sg.graphIdentifiersToNumbers( g )

        finder = sg.MatchFinder( g, verbose=True )
        finder.maxMatches = 2
        finder.maxMatchTime = 0.2
        finder.leftSide( l )
        finder.rightSide( r )
        m = finder.matches()
        self.assertGreaterEqual( len( m ), 1 )
        
        app = sg.RuleApplication( finder, m[0] )
        g2 = app.result()


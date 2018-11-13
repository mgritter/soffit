"""Test parser, using Hypothesis."""
#
#   test/test_parser_hyp.py
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
import soffit.parse as sp
import networkx as nx
from hypothesis import given, assume, note
import hypothesis.strategies as st

nodeIds = st.text( alphabet="ABCDEFGHIJKLMNOPQRSTUVWZYZabcdefghikjklmnopqrstuvwyz",
                   min_size=1 )
edgeStrategy = st.lists( st.tuples( nodeIds, nodeIds ) )
                   
class TestParseGraph(unittest.TestCase):
    def textForUndirectedGraph( self, g ):
        return "; ".join( "{}--{}".format( s, t) for (s,t) in g.edges )

    def undirectedGraphFromEdgeList( self, edges ):
        g = nx.Graph()
        for (s,t) in edges:
            g.add_edge( s, t )
        return g
        
    @given( edgeStrategy )
    def test_untagged_undirected( self, edges ):
        g = self.undirectedGraphFromEdgeList( edges )
        t = self.textForUndirectedGraph( g )
        h = sp.parseGraphString( t )
        gV = set( g.nodes )
        hV = set( h.nodes )
        self.assertEqual( gV, hV )
        gE = set( ( min( s, t ), max( s, t ) ) for (s,t) in g.edges )
        hE = set( ( min( s, t ), max( s, t ) ) for (s,t) in h.edges )
        self.assertEqual( gE, hE )
        

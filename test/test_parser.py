"""Test parsing of graphs."""
#
#   test/test_parser.py
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
from unittest import skip
from soffit.parse import parseGraphString, nodeName
import networkx as nx

class TestGraphParsing(unittest.TestCase):
    def test_single_node(self):
        g = parseGraphString( "X" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 1 )
        self.assertTrue( g.has_node( "X" ) )
        self.assertFalse( g.has_node( ";" ) )

    def test_multi_node(self):
        g = parseGraphString( "X; Y; Z" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 3 )
        self.assertTrue( g.has_node( "X" ) )
        self.assertTrue( g.has_node( "Y" ) )
        self.assertTrue( g.has_node( "Z" ) )
        self.assertFalse( g.has_node( ";" ) )

    def test_single_edge( self ):
        g = parseGraphString( "X -- A" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 2 )
        self.assertEqual( len( g.edges ), 1 )
        self.assertTrue( g.has_node( "X" ) )
        self.assertTrue( g.has_node( "A" ) )
        self.assertTrue( g.has_edge( "X", "A" ) )

    def test_single_edge_directed( self ):
        g = parseGraphString( "X->A" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 2 )
        self.assertEqual( len( g.edges ), 1 )
        self.assertTrue( g.has_node( "X" ) )
        self.assertTrue( g.has_node( "A" ) )
        self.assertTrue( g.has_edge( "X", "A" ) )
        self.assertFalse( g.has_edge( "A", "X" ) )
        
    def test_cycle( self ):
        g = parseGraphString( "X -- A -- B -- X" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 3 )
        self.assertEqual( len( g.edges ), 3 )
        self.assertTrue( g.has_node( "X" ) )
        self.assertTrue( g.has_node( "A" ) )
        self.assertTrue( g.has_node( "B" ) )
        self.assertTrue( g.has_edge( "X", "A" ) )
        self.assertTrue( g.has_edge( "A", "B" ) )
        self.assertTrue( g.has_edge( "X", "B" ) )
        
    def test_edge_whitespace( self ):
        g1 = parseGraphString( "X--Z" )
        self.assertIsNotNone( g1 )
        g2 = parseGraphString( "X-- Z" )
        self.assertIsNotNone( g2 )
        self.assertTrue( nx.is_isomorphic( g1, g2 ) ) 
        g3 = parseGraphString( "X -- Z" )
        self.assertIsNotNone( g3 )
        self.assertTrue( nx.is_isomorphic( g1, g3 ) ) 
        g4 = parseGraphString( " X-- Z" )
        self.assertIsNotNone( g4 )
        self.assertTrue( nx.is_isomorphic( g1, g4 ) ) 
        g5 = parseGraphString( "X-- Z  " )
        self.assertIsNotNone( g5 )
        self.assertTrue( nx.is_isomorphic( g1, g5 ) ) 
        
    def test_semicolon_optional( self ):
        g1 = parseGraphString( "X; Y; Z" )
        g2 = parseGraphString( "X; Y; Z;" )
        self.assertIsNotNone( g1 )
        self.assertIsNotNone( g2 )        
        self.assertTrue( nx.is_isomorphic( g1, g2 ) ) 
        
        g3 = parseGraphString( "X" )
        g4 = parseGraphString( "X;" )
        self.assertIsNotNone( g3 )
        self.assertIsNotNone( g4 )        
        self.assertTrue( nx.is_isomorphic( g3, g4 ) )

    def test_bidrectional_edges( self ):
        g = parseGraphString( "A<-CENTER->B" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 3 )
        self.assertEqual( len( g.edges ), 2 )
        self.assertTrue( g.has_node( "CENTER" ) )
        self.assertTrue( g.has_node( "A" ) )
        self.assertTrue( g.has_node( "B" ) )
        self.assertTrue( g.has_edge( "CENTER", "A" ) )
        self.assertTrue( g.has_edge( "CENTER", "B" ) )
        self.assertFalse( g.has_edge( "B", "CENTER" ) )
        self.assertFalse( g.has_edge( "A", "CENTER" ) )
                        
    def test_multiple_elements( self ):
        g = parseGraphString( "Q; X--Y--Z--X; Y--A; S; Y--B; B--C" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 8 )
        self.assertEqual( len( g.edges ), 6 )
        self.assertTrue( g.has_node( "A" ) )
        self.assertTrue( g.has_node( "B" ) )
        self.assertTrue( g.has_node( "C" ) )
        self.assertTrue( g.has_node( "Q" ) )
        self.assertTrue( g.has_node( "S" ) )
        self.assertTrue( g.has_node( "X" ) )
        self.assertTrue( g.has_node( "Y" ) )
        self.assertTrue( g.has_node( "Z" ) )
        self.assertTrue( g.has_edge( "Y", "A" ) )
        self.assertTrue( g.has_edge( "Y", "B" ) )
        self.assertTrue( g.has_edge( "Y", "Z" ) )
        self.assertTrue( g.has_edge( "Y", "X" ) )
        self.assertTrue( g.has_edge( "X", "Z" ) )
        self.assertTrue( g.has_edge( "B", "C" ) )

    def test_long_node_names( self ):
        n1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxzy"
        n2 = "node2431412xyz"
        n3 = "エンタープライズフラッシュストレージ＆ソフトウェア"
        g = parseGraphString( "--".join( [n1, n2, n3] ) )
        self.assertIsNotNone( g )
        self.assertTrue( g.has_node( n1 ) )
        self.assertTrue( g.has_node( n2 ) )
        self.assertTrue( g.has_node( n3 ) )
        self.assertEqual( len( g.nodes ), 3 )        

    @skip( "Failing" )
    # Swift doesn't allow this, but I think I should
    def test_suit_vertex( self ):
        n1 = "♠"
        self.assertTrue( n1 in nodeName.initCharsOrig )
        x = nodeName.parseString( n1 )
        print( x )
        
    def test_unicode_chars( self ):
        n1 = "😖"
        n2 = "꼭지점"
        n3 = "顶角"
        g = parseGraphString( "--".join( [n1, n2, n3] ) )
        self.assertIsNotNone( g )
        self.assertTrue( g.has_node( n1 ) )
        self.assertTrue( g.has_node( n2 ) )
        self.assertTrue( g.has_node( n3 ) )
        self.assertEqual( len( g.nodes ), 3 )        
        
    def test_invalid_node_names( self ):
        self.assertIsNone( parseGraphString( "123", quiet=True ) )
        self.assertIsNone( parseGraphString( "\n--X", quiet=True ) )
        self.assertIsNone( parseGraphString( "«", quiet=True ) )
        self.assertIsNone( parseGraphString( "+", quiet=True ) )
        self.assertIsNone( parseGraphString( "-", quiet=True ) )
        self.assertIsNone( parseGraphString( "Y.Z", quiet=True ) )
        

if __name__ == '__main__':
    unittest.main()


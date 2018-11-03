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
from soffit.parse import parseGraphString, nodeName, parseGraphGrammar
from soffit.parse import ParseError
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

    def test_empty_graph(self):
        g = parseGraphString( "" )
        self.assertIsNotNone( g )
        self.assertEqual( len( g.nodes ), 0 )
        self.assertEqual( len( g.edges ), 0 )

        g2 = parseGraphString( ";" )
        self.assertIsNotNone( g2 )
        self.assertEqual( len( g2.nodes ), 0 )
        self.assertEqual( len( g2.edges ), 0 )

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
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "123" ) )
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "\n--X" ) )
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "«" ) )
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "+" ) )
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "-" ) )
        with self.assertRaises( ParseError ):
            self.assertIsNone( parseGraphString( "Y.Z" ) )

    def test_merged_nodes( self ):
        a = nodeName.parseString( "A" )
        self.assertIsNotNone( a )
        self.assertIn( "join", a )
        self.assertEqual( len( a['join'] ), 0 )

        b = nodeName.parseString( "B^C^D" )
        self.assertIsNotNone( b )
        self.assertIn( "join", b )
        self.assertEqual( len( b['join'] ), 2 )

    def test_merged_graphs( self ):
        g = parseGraphString( "X^A--Y^B--Z^C", joinAllowed=True )
        self.assertIsNotNone( g )
        self.assertIn( "join", g.graph )
        self.assertEqual( len( g.graph['join'] ), 3 )

    def follow( self, union, x ):
        while x in union:
            x = union[x]
        return x
        
    def test_merged_graphs_cyclic( self ):
        g2 = parseGraphString( "P^Q; Q^R; R^S; S^P", joinAllowed=True )
        self.assertIsNotNone( g2 )
        self.assertIn( "join", g2.graph )
        join = g2.graph['join']
        # The "root" object is not included in the dictionary
        self.assertEqual( len( join ), 3 )
        self.assertEqual( len( g2.nodes), 1 )

        self.assertEqual( self.follow( join, "P" ),
                          self.follow( join, "Q" ) )
        self.assertEqual( self.follow( join, "P" ),
                          self.follow( join, "R" ) )
        self.assertEqual( self.follow( join, "P" ),
                          self.follow( join, "S" ) )                        
        
        rename = g2.graph['rename']
        n0 = list( g2.nodes )[0]
        self.assertEqual( rename['P'], n0 )
        self.assertEqual( rename['Q'], n0 )
        self.assertEqual( rename['R'], n0 )
        self.assertEqual( rename['S'], n0 )
        
    def test_merged_graphs_disallowed( self ):
        with self.assertRaises( ParseError ):
            parseGraphString( "X^A--Y^B--Z^C", joinAllowed=False )

    def test_tagged_nodes( self ):
        g = parseGraphString( "P [x]; Q[2]  ; R; Z [a\[b\]=c d=e]" )
        self.assertEqual( len( g.nodes ), 4 )
        self.assertIn( 'tag', g.nodes['P'] )
        self.assertIn( 'tag', g.nodes['Q'] )
        self.assertNotIn( 'tag', g.nodes['R'] )
        self.assertIn( 'tag', g.nodes['Z'] )
        self.assertEqual( g.nodes['P']['tag'], "x" )
        self.assertEqual( g.nodes['Q']['tag'], "2" )
        self.assertEqual( g.nodes['Z']['tag'], "a[b]=c d=e" )
        
    def test_tagged_edges( self ):
        g = parseGraphString( "P -- Q [2]; A--B--C[!]  ;" )
        self.assertEqual( len( g.nodes ), 5 )
        self.assertEqual( len( g.edges ), 3 )
        self.assertNotIn( 'tag', g.nodes['P'] )
        self.assertNotIn( 'tag', g.nodes['Q'] )
        self.assertNotIn( 'tag', g.nodes['A'] )
        self.assertNotIn( 'tag', g.nodes['B'] )
        self.assertNotIn( 'tag', g.nodes['C'] )
        self.assertIn( 'tag', g.edges['P','Q'] )
        self.assertIn( 'tag', g.edges['Q','P'] )
        self.assertIn( 'tag', g.edges['A','B'] )
        self.assertIn( 'tag', g.edges['B','C'] )
        self.assertEqual( g.edges['P','Q']['tag'], '2' )
        self.assertEqual( g.edges['Q','P']['tag'], '2' )
        self.assertEqual( g.edges['A','B']['tag'], '!' )
        self.assertEqual( g.edges['C','B']['tag'], '!' )

    def test_tag_errors( self ):
        with self.assertRaises( ParseError ):
            parseGraphString( "X[3]--Y" )

        with self.assertRaises( ParseError ):
            parseGraphString( "X--Y[4][5];" )

        with self.assertRaises( ParseError ):
            parseGraphString( "[6]X;" )

    def test_christmas_tree( self ):
        g = parseGraphString( "P[x]; Q[y]; P -- Q^R[z]; P--Z99[x\[\]]", joinAllowed=True )
        self.assertEqual( len( g.nodes ), 3 )
        self.assertEqual( len( g.edges ), 2 )
        self.assertEqual( g.nodes['P']['tag'], 'x' )
        self.assertEqual( g.nodes['Q']['tag'], 'y' )
        self.assertEqual( g['P']['Q']['tag'], 'z' )
        self.assertEqual( g['P']['Z99']['tag'], 'x[]' )
        self.assertEqual( g.graph['join'], { 'R' : 'Q' } )
        
    def test_redefine_tag( self ):
        with self.assertRaises( ParseError ):
            parseGraphString( "P[x]; Q[y]; P[z]" )

        g = parseGraphString( "P[x]; Q[y]; P" )
        self.assertEqual( len( g.nodes ), 2 )

        g = parseGraphString( "P[x]; Q[y]; P [x]" )
        self.assertEqual( len( g.nodes ), 2 )
        self.assertEqual( g.nodes['P']['tag'], 'x' )

    def test_redefine_edge( self ):        
        with self.assertRaises( ParseError ):
            parseGraphString( "P -- Q[x]; Q -- P[y];" )

        with self.assertRaises( ParseError ):
            parseGraphString( "P -- Q[x]; A -> B -> C[y]; B -> P -> Q[z];" )

    def test_tag_node_after_first_use( self ):
        g = parseGraphString( "P -- Q [x]; P[1]; Q[2]" )
        self.assertEqual( g.nodes['P']['tag'], '1' )
        self.assertEqual( g.nodes['Q']['tag'], '2' )
        self.assertEqual( g['P']['Q']['tag'], 'x' )

    def test_tag_merged_node( self ):
        g = parseGraphString( "A[x]; A^C--B^D; D[y]", joinAllowed=True )
        self.assertEqual( len( g.nodes ), 2 )
        # FIXME: fragile?
        self.assertIn( 'A', g.nodes )
        self.assertIn( 'B', g.nodes )
        self.assertEqual( g.nodes['A']['tag'], 'x' )
        self.assertEqual( g.nodes['B']['tag'], 'y' )

    def test_merge_same_node( self ):
        g = parseGraphString( "A -- B [x]; A^B", joinAllowed=True )
        self.assertEqual( len( g.nodes ), 1 )
        n0 = list( g.nodes )[0]
        self.assertIn( (n0,n0), g.edges )
        self.assertEqual( g[n0][n0]['tag'], 'x' )

    def test_tag_many_merged_nodes( self ):
        g = parseGraphString( "A^B; B^C; C^D[y]; E^F; F^C; G^B; G[y]",
                              joinAllowed=True )
        self.assertEqual( len( g.nodes ), 1 )
        n0 = list( g.nodes )[0]
        self.assertEqual( g.nodes[n0]['tag'], 'y' )
        self.assertEqual( g.graph['rename']['A'], n0 )
        self.assertEqual( g.graph['rename']['B'], n0 )
        self.assertEqual( g.graph['rename']['C'], n0 )
        self.assertEqual( g.graph['rename']['D'], n0 )
        self.assertEqual( g.graph['rename']['E'], n0 )
        self.assertEqual( g.graph['rename']['F'], n0 )
        self.assertEqual( g.graph['rename']['G'], n0 )

    def test_directed_unequal_tags( self ):
        g = parseGraphString( "A->B [left]; A<-B [right]" )
        self.assertEqual( len( g.nodes ), 2 )
        self.assertEqual( len( g.edges ), 2 )
        self.assertEqual( g.edges['A','B']['tag'], 'left' )
        self.assertEqual( g.edges['B','A']['tag'], 'right' )

    def test_implicit_name( self ):
        g = parseGraphString( "A--D; B--C",
                              joinAllowed=True )
        self.assertEqual( g.graph['rename']['A'], 'A' )
        self.assertEqual( g.graph['rename']['B'], 'B' )
        self.assertEqual( g.graph['rename']['C'], 'C' )
        self.assertEqual( g.graph['rename']['D'], 'D' )

    def test_directed_square( self ):
        g = parseGraphString( "A->B->D; A->C->D; A[src]; D[dst]; A->D [new]",
                              joinAllowed=True )
        self.assertEqual( len( g.nodes ), 4 )
        self.assertEqual( len( g.edges ), 5 )
        self.assertEqual( g.graph['rename']['A'], 'A' )
        self.assertEqual( g.graph['rename']['B'], 'B' )
        self.assertEqual( g.graph['rename']['C'], 'C' )
        self.assertEqual( g.graph['rename']['D'], 'D' )
        
    def test_merge_unequal_tgs( self ):        
        with self.assertRaises( ParseError ):
            parseGraphString( "A[x]; B[y]; B^A -- C" )

        with self.assertRaises( ParseError ):
            parseGraphString( "A[x]; B^A; B[y];" )

        with self.assertRaises( ParseError ):
            parseGraphString( "A[x]; A^C; B^C[y]" )

v01a = """{
  "version" : "0.1",
  "start" : "A--B",
  "A--B" : "A--B--C; B--D",
  "A--B--C--D" : [ "A--B--C--D--A", "A--B; C--D;" ]
}
"""

class TestGrammarParsing(unittest.TestCase):
    showErrors = False
    
    def test_v01_grammar(self):
        g = parseGraphGrammar( v01a )
        self.assertIsNotNone( g )
        self.assertIsNotNone( g.start )
        self.assertEqual( len( g.rules ), 2 )

    def test_failed_start(self):
        badGrammar = """
        {
        "start" : "A<=>B"
        }
        """

        with self.assertRaises( ParseError ) as cm:
            g = parseGraphGrammar( badGrammar )

        x = cm.exception
        if self.showErrors:
            x.prettyPrint()
        self.assertEqual( x.left, "start" )
        self.assertEqual( x.right, "A<=>B" )
        
    def test_failed_lhs(self):
        badGrammar2 = """{
  "start" : "A--B",
  "A--B^A" : "D--A--C"
}
"""

        with self.assertRaises( ParseError ) as cm:
            g = parseGraphGrammar( badGrammar2 )

        x = cm.exception
        if self.showErrors:
            x.prettyPrint()
        self.assertEqual( x.left, "A--B^A" )

    def test_failed_rhs(self):
        badGrammar3 = """{
  "start" : "A--B",
  "A--B--C; B--D--E; D--F--G" : "Q--R--S--T--U--X.Y"
}
"""

        with self.assertRaises( ParseError ) as cm:
            g = parseGraphGrammar( badGrammar3 )

        x = cm.exception
        if self.showErrors:
            x.prettyPrint()
        self.assertEqual( x.left, "A--B--C; B--D--E; D--F--G" )

    
    def test_failed_choice(self):
        badGrammar4 = """{
  "start" : "A--B",
  "A--B" : [ "A--C--B", "C--A--B", "A--B--D; B--E", "A<->B" ]
}
"""
        with self.assertRaises( ParseError ) as cm:
            g = parseGraphGrammar( badGrammar4 )

        x = cm.exception
        if self.showErrors:
            x.prettyPrint()
        self.assertEqual( x.right, "A<->B" )
        
if __name__ == '__main__':
    unittest.main()


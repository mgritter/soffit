"""Test manipulation of graphs."""
#
#   test/test_graph.py
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
import networkx as nx
import soffit.graph as sg
from soffit.parse import parseGraphString

import sys

# FIXME: change this to key off the test runner's -v option, but
# it seems there are only gross ways to do so.
# https://stackoverflow.com/questions/13761697/how-to-access-the-unittest-mainverbosity-setting-in-a-unittest-testcase
testVerbose = True

class TestGraphModification(unittest.TestCase):
    def test_graph_renumber(self):
        g = nx.Graph()
        g.add_edge( 'A', 'B', tag='x' )
        g.add_edge( 'B', 'C', tag='y' )
        g2 = sg.graphIdentifiersToNumbers( g )
        self.assertEqual( len( g2.nodes ), 3 )
        self.assertIn( 0, g2.nodes )
        self.assertIn( 1, g2.nodes )
        self.assertIn( 2, g2.nodes )
        self.assertEqual( g2.graph['nextId'], 3 )

        edgeTags = [ g2.edges[e]['tag'] for e in g2.edges ]
        self.assertIn( 'x', edgeTags )
        self.assertIn( 'y', edgeTags )

    def _buildRename( self, g ):        
        join = g.graph['join']
        rename = {}
        for n in g.nodes:
            rename[n] = n
        for k in join:
            orig = k
            while k in join:
                k = join[k]
            rename[orig] = k
        g.graph['rename'] = rename
        
    def test_deleted_nodes( self ):
        l = nx.Graph()
        l.add_node( 'A', tag='x' )
        l.add_node( 'B', tag='y' )
        l.add_node( 'C', tag='z' )
        l.add_node( 'D' )
        l.add_node( 'E' )

        # B merged to A
        # C, E deleted
        r = nx.Graph()
        r.graph['join'] = { 'B' : 'A' }
        r.add_node( 'A', tag='x' )
        r.add_node( 'D' )
        self._buildRename( r )

        rh = sg.RightHandGraph( r )
        (dn, de) = rh.ruleDeletions( l )
        if testVerbose:
            print( "Deleted nodes:", dn )
            print( "Deleted edgess:", de )
            
        self.assertEqual( len( dn ), 2 )
        self.assertEqual( len( de ), 0 )
        self.assertIn( 'C', dn )
        self.assertIn( 'E', dn )
        self.assertNotIn( 'B', dn )
        
    def test_deleted_edges( self ):
        l = nx.Graph()
        l.add_edge( 'A', 'B', tag='1' )
        l.add_edge( 'B', 'C', tag='2' )
        l.add_edge( 'C', 'D', tag='3' )
        l.add_edge( 'B', 'E', tag='4' )
        l.add_edge( 'B', 'F', tag='5' )
        
        r = nx.Graph()
        # C and A got merged, so did the edges A-B and B-C
        # C-D got deleted but D did not
        # B-E got deleted along with E
        # B-F is not deleted
        r.graph['join'] = { 'C' : 'A' }        
        r.add_edge( 'A', 'B', tag='1' )
        r.add_node( 'D' )
        r.add_edge( 'B', 'F', tag='5' )
        self._buildRename( r )
        
        rh = sg.RightHandGraph( r )
        (dn, de) = rh.ruleDeletions( l )
        if testVerbose:
            print( "Deleted nodes:", dn )
            print( "Deleted edgess:", de )
        self.assertEqual( len( dn ), 1 )
        self.assertEqual( len( de ), 2 )
        self.assertIn( 'E', dn )
        # Crud, edges can appear in either order...
        self.assertTrue( ('C','D') in de  or ('D','C') in de )
        self.assertTrue( ('B','E') in de  or ('E','B') in de )
        self.assertNotIn( ('B','F'), de )
        self.assertNotIn( ('F','B'), de )

    def test_deleted_self_edges( self ):
        l = nx.Graph()
        l.add_edge( 'A', 'A', tag='1' )
        l.add_edge( 'B', 'C', tag='2' )

        r = nx.Graph( join={} )
        r.add_node( 'A' )
        r.add_edge( 'B', 'C', tag='2' )
        self._buildRename( r )

        rh = sg.RightHandGraph( r )
        (dn, de) = rh.ruleDeletions( l )
        self.assertEqual( len(dn), 0 )
        self.assertIn( ('A','A'), de )
        self.assertEqual( len(de), 1 )

class TestSurjectiveMappings(unittest.TestCase):
    def test_simple( self ):
        foo = list( sg.surjectiveMappings( 1, ['a'] ) )
        self.assertIn( ('a',), foo )
        self.assertEqual( len( foo ), 1 )

    def test_empty( self ):        
        mt = list( sg.surjectiveMappings( 1, ['a', 'b'] ) )
        self.assertEqual( len( mt ), 0 )

        mt2 = list( sg.surjectiveMappings( 3, ['a', 'b', 'c', 'd'] ) )
        self.assertEqual( len( mt2 ), 0 )

    def test_permutation( self ):
        foo = list( sg.surjectiveMappings( 3, ['a', 'b', 'c'] ) )
        self.assertIn( ('a', 'b', 'c'), foo )
        self.assertIn( ('a', 'c', 'b'), foo )
        self.assertIn( ('b', 'a', 'c'), foo )
        self.assertIn( ('b', 'c', 'a'), foo )
        self.assertIn( ('c', 'a', 'b'), foo )
        self.assertIn( ('c', 'b', 'a'), foo )
        self.assertEqual( len( foo ), 6 )

    def test_permutation_plus_one( self ):
        foo = list( sg.surjectiveMappings( 3, ['a', 'b'] ) )
        self.assertIn( ('a', 'b', 'a'), foo )
        self.assertIn( ('a', 'b', 'b'), foo )
        self.assertIn( ('a', 'a', 'b'), foo )
        self.assertIn( ('b', 'a', 'a'), foo )
        self.assertIn( ('b', 'a', 'b'), foo )
        self.assertIn( ('b', 'b', 'a'), foo )
        self.assertEqual( len( foo ), 6 )
        
class TestMatchFinding(unittest.TestCase):
    def twoEdgesX(self):
        g = nx.Graph()
        g.add_edge( 'A', 'B', tag='x' )
        g.add_edge( 'B', 'C', tag='x' )
        return g
    
    def test_impossible_match_edge(self):
        g = self.twoEdgesX()
        
        lhs = nx.Graph()
        lhs.add_edge( 'X', 'Y', tag='z')

        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        self.assertTrue( finder.impossible )

        m = finder.matches()
        self.assertEqual( len( m ), 0 )

    def test_impossible_match_none(self):
        g = self.twoEdgesX()

        lhs2 = nx.Graph()
        lhs2.add_edge( 'X', 'Y' )

        finder2 = sg.MatchFinder( g, verbose=testVerbose )
        finder2.leftSide( lhs2 )
        self.assertTrue( finder2.impossible )

    def test_impossible_match_node(self):
        g = nx.Graph()
        g.add_node( 'A', tag='x' )
        g.add_node( 'B', tag='y' )
        g.add_edge( 'A', 'B', tag='z' )
        
        lhs = nx.Graph()
        lhs.add_node( 'X', tag='z')

        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        self.assertTrue( finder.impossible )

        m = finder.matches()
        self.assertEqual( len( m ), 0 )

    def test_lhs_match_singlenode( self ):
        g = nx.Graph()
        g.add_node( 'A', tag='x' )
        g.add_node( 'B', tag='x' )

        lhs = nx.Graph()
        lhs.add_node( 'X', tag='x' )
        
        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        self.assertFalse( finder.impossible )

        m = finder.matches()
        if testVerbose:
            print( m )
        self.assertEqual( len( m ), 2 )
        if m[0].node( 'X' ) == 'A':
            self.assertEqual( m[1].node('X'), 'B' )
        else:
            self.assertEqual( m[1].node('X'), 'A' )

    def test_lhs_match_singledge( self ):
        g = self.twoEdgesX()

        lhs = nx.Graph()
        lhs.add_edge( 'X', 'Y', tag='x' )
        
        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        self.assertFalse( finder.impossible )

        mList = finder.matches()
        if testVerbose:
            print( mList )
        self.assertEqual( len( mList ), 4 )
        edges = set( [ ('A', 'B'),
                       ('B', 'A'),
                       ('B', 'C'),
                       ('C', 'B') ] )
        foundEdges = set( m.edge( ( 'X', 'Y' ) ) for m in mList )
        self.assertEqual( edges, foundEdges )

    def test_complicated_directed_single_path( self ):
        g = nx.DiGraph()
        g.add_edge( 'A', 'B', tag='1' )
        g.add_edge( 'A', 'C', tag='2' )
        g.add_edge( 'A', 'D', tag='3' )
        
        g.add_edge( 'B', 'E', tag='4' )
        g.add_edge( 'C', 'E', tag='5' )
        g.add_edge( 'D', 'E', tag='6' )

        g.add_edge( 'E', 'A', tag='x' )

        lhs = nx.DiGraph()
        lhs.add_edge( 'X1', 'X2', tag='1' )
        lhs.add_edge( 'X2', 'X3', tag='4' )
        lhs.add_edge( 'X3', 'X4', tag='x' )
        lhs.add_edge( 'X4', 'X5', tag='2' )
        lhs.add_edge( 'X5', 'X6', tag='5' )
        lhs.add_edge( 'X6', 'X7', tag='x' )
        lhs.add_edge( 'X7', 'X8', tag='3' )
        lhs.add_edge( 'X8', 'X9', tag='6' )
        lhs.add_edge( 'X9', 'XA', tag='x' )
        
        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        self.assertFalse( finder.impossible )
        mList = finder.matches()
        self.assertEqual( len( mList ), 1 )


    def multiPath( self, srcs, inter ):
        g = nx.Graph()
        for s in srcs:
            g.add_node( s, tag="src" )

        g.add_node( "DST", tag="dst" )

        for i in inter:
            g.add_node( i )
            for s in srcs:
                g.add_edge( s, i )
            g.add_edge( i, "DST" )

        return g
        
    def test_multiple_paths( self ):
        srcs = [ "S1", "S2", "S3" ]
        inter = [ "A", "B" ]
        g = self.multiPath( srcs, inter )
        
        lhs = nx.Graph()
        lhs.add_node( "X", tag="src" )
        lhs.add_node( "Y" )        
        lhs.add_node( "Z", tag="dst" )
        lhs.add_edge( "X", "Y" )
            
        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs )
        mList = finder.matches()
        self.assertEqual( len( mList ), len( srcs ) * len( inter ) ) 
        for m in mList:
            if testVerbose:
                print( m )
            self.assertIn( m.node( "X" ), srcs )
            self.assertIn( m.node( "Y"),  inter )
            self.assertEqual( m.node( "Z" ), "DST" )

    def test_multiple_paths_fail( self ):
        srcs = [ "S1", "S2", "S3" ]
        inter = [ "A", "B" ]
        g = self.multiPath( srcs, inter )

        lhs2 = nx.Graph()
        lhs2.add_node( "X", tag="src" )
        lhs2.add_node( "Z", tag="dst" )
        lhs2.add_edge( "X", "Z" )

        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( lhs2 )

        mList = finder.matches()
        self.assertEqual( len( mList ), 0 )

    def test_match_dedup( self ):
        a = sg.Match()
        a.addMap( 'X', 'A' )
        a.addMap( 'Y', 'B' )
        a.addMap( 'Z', 'B' )
        
        b = sg.Match()
        b.addMap( 'Z', 'B' )
        b.addMap( 'X', 'A' )
        b.addMap( 'Y', 'B' )

        self.assertEqual( a, b )
        self.assertEqual( hash(a), hash(b) )
        with self.assertRaises( sg.MatchError ):
            b.addMap( "BAD", "NEWS" )
        
    def test_directed_vs_undirected_error( self ):
        g = nx.Graph()
        g.add_edge( 'A', 'B' )

        lhs = nx.DiGraph()
        lhs.add_edge( 'X', 'Y' )

        finder = sg.MatchFinder( g, verbose=testVerbose )
        with self.assertRaises( sg.MatchError ) as me:
            finder.leftSide( lhs )

        if testVerbose:
            print( me.exception )

    def test_right_dangling_nodes( self ):
        l = parseGraphString( "A--B; A--C" )
        self.assertFalse( nx.is_directed( l ) )
        r = parseGraphString( "B; C" )
        self.assertFalse( nx.is_directed( r ) )
        g = parseGraphString( "w--x; w--y; w--z; z--s" )
        self.assertFalse( nx.is_directed( g ) )

        finder = sg.MatchFinder( g, verbose=testVerbose )
        finder.leftSide( l )
        finder.rightSide( r )
        mList = finder.matches()

        print( mList )
        
                
if __name__ == '__main__':
    unittest.main()

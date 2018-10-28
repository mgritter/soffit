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

    @skip( "Crashes or-tools, see https://github.com/google/or-tools/issues/907" )
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

        print( finder.model.ModelProto() )
        
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
        g.add_edge( 'X', 'Y' )

        finder = sg.MatchFinder( g, verbose=testVerbose )
        with self.assertRaises( sg.MatchError ) as me:
            finder.leftSide( lhs )

        if testVerbose:
            print( me.exception )
        
if __name__ == '__main__':
    unittest.main()

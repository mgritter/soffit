"""Test extensions to constraint solver."""
#
#   test/test_constraint.py
#
#   Copyright 2018-2019 Mark Gritter
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
from constraint import *
from soffit.constraint import *
import networkx as nx

class TestTupleConstraint(unittest.TestCase):
    def test_init( self ):
        testSet = [ [1, 2, 3],
                    [2, 3, 4],
                    [3, 4, 5],
                    [2, 3, 4],
                    [3, 5, 5] ]
                    
        tc = TupleConstraint( testSet )
        self.assertIn( (1, 2, 3), tc.allowedSet )
        self.assertIn( (2, 3, 4), tc.allowedSet )
        self.assertIn( (3, 4, 5), tc.allowedSet )
        self.assertIn( (3, 5, 5), tc.allowedSet )
        self.assertEqual( len( tc.allowedSet ), 4 )
        self.assertEqual( set( [1, 2, 3] ), tc.nthSet[0] )
        self.assertEqual( set( [2, 3, 4, 5] ), tc.nthSet[1] )
        self.assertEqual( set( [3, 4, 5] ), tc.nthSet[2] )

    def domains( self ):
        return { 'a' : Domain( range( 0, 10 ) ),
                 'b' : Domain( range( 0, 10 ) ),
                 'c' : Domain( range( 0, 10 ) ),
                 'd' : Domain( range( 0, 10 ) ) }
                 
    def test_call_incomplete( self ):
        testSet = [ [1, 2, 3],
                    [2, 3, 4] ]
        tc = TupleConstraint( testSet )
        self.assertTrue( tc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a': 1 } ) )
        self.assertTrue( tc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a': 1, 'b': 2 } ) )

    def test_call( self ):
        testSet = [ [1, 2, 3],
                    [2, 3, 4] ]
        tc = TupleConstraint( testSet )
        self.assertTrue( tc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 1, 'b' : 2, 'c': 3, 'd': 4 } ) )
        self.assertTrue( tc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 2, 'b' : 3, 'c': 4, 'd': 1 } ) )
        self.assertTrue( tc( ['a', 'b', 'd'],
                             self.domains(),
                             { 'a' : 2, 'b' : 3, 'c': 1, 'd': 4 } ) )
        self.assertFalse( tc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 6, 'b' : 7, 'c': 8 } ) )

    def test_nth_reduction( self ):
        testSet = [ [1, 2, 3],
                    [2, 3, 4] ]
        tc = TupleConstraint( testSet )
        variables = [ 'a', 'b', 'c' ]
        d = self.domains()
        constraints = [ ( tc, variables ), ( tc, ['x', 'y', 'z'] ) ]
        vconstraints = {}
        vconstraints['a'] = [ constraints[0] ]
        vconstraints['b'] = [ constraints[0] ]
        vconstraints['c'] = [ constraints[0] ]
        tc.preProcess( variables, d, constraints, vconstraints )
        self.assertEqual( d['a'], [1, 2] )
        self.assertEqual( d['b'], [2, 3] )
        self.assertEqual( d['c'], [3, 4] )
        self.assertEqual( len( constraints ), 2 )
        self.assertEqual( len( vconstraints['a'] ), 1 )
        self.assertEqual( len( vconstraints['b'] ), 1 )
        self.assertEqual( len( vconstraints['c'] ), 1 )

    def test_real_problem( self ):
        p = Problem()
        p.addVariable( 'a', range( 5 ) )
        p.addVariable( 'b', range( 5 ) )
        p.addVariable( 'c', range( 5 ) )
        firstPair = [ (1, 2),
                      (2, 3),
                      (3, 4) ]
        secondPair = [ (2, 3),
                       (3, 0),
                       (4, 0) ]
        p.addConstraint( TupleConstraint( firstPair ), ['a', 'b'] )
        p.addConstraint( TupleConstraint( secondPair ), ['b', 'c'] )
        soln = p.getSolutions()
        self.assertIn( {'a' : 1, 'b': 2, 'c': 3 }, soln )
        self.assertIn( {'a' : 2, 'b': 3, 'c': 0 }, soln )
        self.assertIn( {'a' : 3, 'b': 4, 'c': 0 }, soln )
        self.assertEqual( len( soln ), 3 )

    def test_single_tuple( self ):
        p = Problem()
        p.addVariable( 'a', range( 100 ) )
        p.addVariable( 'b', range( 100 ) )
        p.addVariable( 'c', range( 5 ) )
        firstPair = [ (1, 2) ]
        p.addConstraint( TupleConstraint( firstPair ), ['a', 'b'] )
        p.addConstraint( lambda a, b, c: a + b == c , ['a', 'b', 'c'] )
        soln = p.getSolutions()
        self.assertIn( {'a' : 1, 'b': 2, 'c': 3 }, soln )
        self.assertEqual( len( soln ), 1 )

class TestConditionalConstraint(unittest.TestCase):
    def domains( self ):
        return { 'a' : Domain( range( 0, 10 ) ),
                 'b' : Domain( range( 0, 10 ) ),
                 'c' : Domain( range( 0, 10 ) ),
                 'd' : Domain( range( 0, 10 ) ) }
    
    def test_call( self ):
        pairs = [ (1, 2),
                  (2, 3) ]
        tc = TupleConstraint( pairs )
        cc = ConditionalConstraint( 7, tc )

        self.assertTrue( cc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 5, 'b' : 1, 'c': 1, 'd': 1 } ) )

        self.assertTrue( cc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 7, 'b' : 1, 'c': 2 } ) )

        self.assertFalse( cc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'a' : 7, 'b' : 3, 'c': 4 } ) )

    def test_call_incomplete( self ):
        pairs = [ (1, 2),
                  (2, 3) ]
        tc = TupleConstraint( pairs )
        cc = ConditionalConstraint( 7, tc )

        self.assertTrue( cc( ['a', 'b', 'c'],
                             self.domains(),
                             { 'b' : 1, 'c': 1, 'd': 1 } ) )

class TestConditionalTupleConstraint(unittest.TestCase):
    def domains( self ):
        return { 'a' : Domain( range( 0, 10 ) ),
                 'b' : Domain( range( 0, 10 ) ),
                 'c' : Domain( range( 0, 10 ) ),
                 'd' : Domain( range( 0, 10 ) ) }
    
    def test_call( self ):
        tuples = [ (7, 1, 2),
                   (7, 2, 3) ]
        ctc = ConditionalTupleConstraint( tuples )

        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'a' : 5, 'b' : 1, 'c': 1, 'd': 1 } ) )

        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'a' : 7, 'b' : 1, 'c': 2 } ) )
        
        self.assertFalse( ctc( ['a', 'b', 'c'],
                               self.domains(),
                               { 'a' : 7, 'b' : 3, 'c': 4 } ) )
        
        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'a' : 8, 'b' : 3, 'c': 4 } ) )

    def test_compatible_tuples( self ):
        tuples = [ (7, 1, 2),
                   (7, 2, 3),
                   (8, 1, 4),
                   (8, 9, 4) ]
        ctc = ConditionalTupleConstraint( tuples )

        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'b' : 1, 'c': 1 } ) )
        
        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'b' : 1, 'c': 4 } ) )
        
        self.assertFalse( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'a' : 7,  'c': 4 } ) )
        
        self.assertTrue( ctc( ['a', 'b', 'c'],
                              self.domains(),
                              { 'a' : 8,  'c': 4 } ) )

    def test_forward_check( self ):
        tuples = [ (7, 1, 2),
                   (7, 2, 3),
                   (8, 1, 4),
                   (8, 9, 4) ]
        ctc = ConditionalTupleConstraint( tuples )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c'],
                              d,
                              { 'b' : 1, 'c': 1 },
                              forwardcheck = True ) )
        self.assertNotIn( 7, d['a'] )
        self.assertNotIn( 8, d['a'] )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c'],
                              d,
                              { 'a' : 7 },
                              forwardcheck = True ) )
        self.assertNotIn( 3, d['b'] )
        self.assertNotIn( 4, d['b'] )
        self.assertIn( 1, d['b'] )
        self.assertIn( 2, d['b'] )
        
        self.assertNotIn( 1, d['c'] )
        self.assertNotIn( 4, d['c'] )
        self.assertIn( 2, d['c'] )
        self.assertIn( 3, d['c'] )

        d = self.domains()
        d['b'] = Domain( [5, 6, 7] )
        self.assertFalse( ctc( ['a', 'b', 'c'],
                               d,
                               { 'a' : 8 },
                               forwardcheck = True ) )

    def test_bug( self ):
        tuples = [ (0, 0, 0, 0),
                   (0, 0, 1, 1) ]
        ctc = ConditionalTupleConstraint( tuples )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'a' : 0, 'b': 0, 'c' : 0, 'd' : 0 } ) )

        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'a' : 0, 'b': 0, 'c' : 0, 'd' : 0 },
                              forwardcheck = True ) )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'a' : 0 },
                              forwardcheck = True ) )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'b' : 0 },
                              forwardcheck = True ) )

        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'c' : 0 },
                              forwardcheck = True ) )
        
        d = self.domains()
        self.assertTrue( ctc( ['a', 'b', 'c', 'd'],
                              d,
                              { 'd' : 0 },
                              forwardcheck = True ) )

class TestOverlapConstraint(unittest.TestCase):
    def domains( self ):
        return { 'a' : Domain( range( 0, 10 ) ),
                 'b' : Domain( range( 0, 10 ) ),
                 'c' : Domain( range( 0, 10 ) ),
                 'd' : Domain( range( 0, 10 ) ) }

    def test_nonoverlapping_2var_complete( self ):
        firstSet = ['a']
        secondSet = ['b']
        nc = NonoverlappingSets( firstSet, secondSet )

        self.assertFalse( nc( ['a', 'b'],
                              self.domains(),
                              { 'a' : 1, 'b' : 1, 'c': 2, 'd': 3 } ) )

        self.assertTrue( nc( ['a', 'b'],
                              self.domains(),
                              { 'a' : 1, 'b' : 2 } ) )

    def test_nonoverlapping_2var_incomplete( self ):
        firstSet = ['a']
        secondSet = ['b']
        nc = NonoverlappingSets( firstSet, secondSet )

        self.assertTrue( nc( ['a', 'b'],
                             self.domains(),
                             { 'a' : 1 } ) )

        self.assertTrue( nc( ['a', 'b'],
                             self.domains(),
                             { 'b' : 1 } ) )

    def test_nonoverlapping_4var_complete( self ):
        firstSet = ['a', 'b']
        secondSet = ['c', 'd']
        nc = NonoverlappingSets( firstSet, secondSet )

        self.assertFalse( nc( ['a', 'b', 'c', 'd'],
                              self.domains(),
                              { 'a' : 1, 'b' : 2, 'c': 3, 'd': 1 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                              self.domains(),
                              { 'a' : 1, 'b' : 2, 'c': 3, 'd': 4 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                             self.domains(),
                             { 'a' : 1, 'b' : 1, 'c': 4, 'd': 4 } ) )

    def test_nonoverlapping_4var_incomplete( self ):
        firstSet = ['a', 'b']
        secondSet = ['c', 'd']
        nc = NonoverlappingSets( firstSet, secondSet )

        self.assertFalse( nc( ['a', 'b', 'c', 'd'],
                              self.domains(),
                              { 'a' : 1, 'b' : 2, 'd': 1 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                              self.domains(),
                              { 'a' : 1, 'c': 3, 'd': 4 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                              self.domains(),
                              { 'a' : 1, 'b' : 2, 'd': 4 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                             self.domains(),
                             { 'a' : 1, 'b' : 1 } ) )

        self.assertTrue( nc( ['a', 'b', 'c', 'd'],
                             self.domains(),
                             { 'a' : 1, 'b' : 1, 'd' : 4 } ) )

    def test_nonoverlapping_precprocess_empty( self ):
        nc = NonoverlappingSets( ['a', 'b'], [] )
        variables = [ 'a', 'b' ]
        d = self.domains()
        constraints = [ ( nc, variables ), ( nc, ['x', 'y', 'z'] ) ]
        vconstraints = {}
        vconstraints['a'] = [ constraints[0] ]
        vconstraints['b'] = [ constraints[0] ]
        vconstraints['x'] = [ constraints[1] ]
        nc.preProcess( variables, d, constraints, vconstraints )
        self.assertEqual( len( constraints ), 1 )
        self.assertEqual( len( vconstraints['a'] ), 0 )
        self.assertEqual( len( vconstraints['b'] ), 0 )
        self.assertEqual( len( vconstraints['x'] ), 1 )
        

class TestGraphConstraint(unittest.TestCase):
    def domains( self ):
        return { 'w' : Domain( range( 0, 10 ) ),
                 'x' : Domain( range( 0, 10 ) ),
                 'y' : Domain( range( 0, 10 ) ),
                 'z' : Domain( range( 0, 10 ) ) }

    def sampleGraph( self ):
        g = nx.DiGraph()
        g.add_node( 0 )
        g.add_node( 1, tag="foo" )
        g.add_node( 2, tag="foo" )
        g.add_node( 3, tag="bar" )
        for n in range (4, 10):
            g.add_node( n )
        g.add_edge( 1, 5, tag="A" )
        g.add_edge( 8, 9, tag="A" )
        g.add_edge( 2, 3, tag="B" )
        g.add_edge( 2, 4, tag="C" )
        return g
                
    def test_node_incomplete( self ):
        g = self.sampleGraph()
        nc = NodeTagConstraint( g, "foo" )
        self.assertTrue( nc( ['x', 'y', 'z'],
                             self.domains(),
                             { 'y': 1 } ) )
        self.assertFalse( nc( ['x', 'y', 'z'],
                              self.domains(),
                              { 'y': 3 } ) )        
        self.assertFalse( nc( ['x', 'y', 'z'],
                              self.domains(),
                              { 'y': 5, 'x' : 1 } ) )
        self.assertTrue( nc( ['x', 'y', 'z'],
                             self.domains(),
                             { 'y': 2, 'x' : 1 } ) )

    def test_node_complete( self ):
        g = self.sampleGraph()
        nc = NodeTagConstraint( g, "foo" )
        self.assertTrue( nc( ['x', 'y' ],
                             self.domains(),
                             { 'y': 1, 'x' : 2 } ) )
        self.assertFalse( nc( ['x', 'y' ],
                              self.domains(),
                              { 'y': 1, 'x' : 3 } ) )

        nc2 = NodeTagConstraint( g, None )        
        self.assertTrue( nc2( ['x', 'y', 'z'],
                              self.domains(),
                              { 'x' : 7, 'y' : 8, 'z' : 9 } ) )        
        self.assertFalse( nc2( ['x', 'y', 'z'],
                               self.domains(),
                               { 'x' : 1, 'y' : 8, 'z' : 9 } ) )        
                
    def test_node_forward_check( self ):
        g = self.sampleGraph()
        nc = NodeTagConstraint( g, "foo" )
        self.assertFalse( nc( ['x', 'y',],
                              self.domains(),
                              { 'x' : 7 } ) )
        self.assertFalse( nc( ['x', 'y',],
                              self.domains(),
                              { 'x' : 8 } ) )
        self.assertFalse( nc( ['x', 'y',],
                              self.domains(),
                              { 'x' : 9 } ) )
        d = self.domains()
        self.assertTrue( nc( ['x', 'y',],
                             d,
                             { 'x' : 1 },
                             True ) )
        self.assertTrue( 7 not in d['y'] )
        self.assertTrue( 8 not in d['y'] )
        self.assertTrue( 9 not in d['y'] )
        self.assertTrue( 1 in d['y'] )
        self.assertTrue( 2 in d['y'] )
        self.assertTrue( 3 in d['y'] )

    def test_node_preprocess( self ):
        g = self.sampleGraph()
        g.graph['node_tag_cache'] = {
            "foo" : [1,2],
            "bar" : [3],
            None : [0,4,5,6,7,8,9]
        }
        nc = NodeTagConstraint( g, "foo" )
        d = self.domains()
        nc.preProcess( ['x','y'], d, [], {} )
        self.assertNotIn( 3, d['x'] )
        self.assertNotIn( 7, d['y'] )
        self.assertIn( 1, d['x'] )
        self.assertIn( 2, d['x'] )
        self.assertIn( 1, d['y'] )
        self.assertIn( 2, d['y'] )

    def test_node_preprocess_empty( self ):        
        g2 = self.sampleGraph()
        nc2 = NodeTagConstraint( g2, "foo" )
        d2 = self.domains()
        nc2.preProcess( ['x','y'], d2, [], {} )
        self.assertIn( 1, d2['x'] )
        self.assertIn( 3, d2['x'] )

        g3 = self.sampleGraph()
        g3.graph['node_tag_cache'] = {}
        nc3 = NodeTagConstraint( g2, "foo" )
        d3 = self.domains()
        nc3.preProcess( ['x','y'], d3, [], {} )
        self.assertIn( 1, d3['x'] )
        self.assertIn( 3, d3['x'] )

    def test_edge_incomplete( self ):
        g = self.sampleGraph()
        ec = EdgeTagConstraint( g, "A" )
        self.assertTrue( ec( ['x', 'y'],
                             self.domains(),
                             { 'x': 1 } ) )
        self.assertFalse( ec( ['x', 'y'],
                              self.domains(),
                              { 'x': 2 } ) )        
        self.assertFalse( ec( ['x', 'y', 'w', 'z'],
                              self.domains(),
                              { 'x': 1, 'y' : 5, 'w' : 7 } ) )

    def test_edge_complete( self ):
        g = self.sampleGraph()
        ec = EdgeTagConstraint( g, "A" )
        
        self.assertTrue( ec( ['x', 'y' ],
                             self.domains(),
                             { 'x': 1, 'y' : 5 } ) )
        self.assertTrue( ec( ['x', 'y' ],
                             self.domains(),
                             { 'x': 8, 'y' : 9 } ) )
        self.assertFalse( ec( ['x', 'y' ],
                             self.domains(),
                             { 'x': 9, 'y' : 8 } ) )
        self.assertFalse( ec( ['x', 'y' ],
                             self.domains(),
                             { 'x': 2, 'y' : 3 } ) )

    def test_edge_forward_check( self ):
        g = self.sampleGraph()
        nc = EdgeTagConstraint( g, "A" )
        d = self.domains()
        self.assertTrue( nc( ['x', 'y',],
                             d,
                             { 'x' : 1 },
                             True ) )
        self.assertEqual( [5], list( d['y'] ) )
        
        d = self.domains()
        self.assertTrue( nc( ['x', 'y',],
                             d,
                             { 'y' : 9 },
                             True ) )
        self.assertEqual( [8], list( d['x'] ) )
        
if __name__ == '__main__':
    unittest.main()

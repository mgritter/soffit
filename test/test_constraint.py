"""Test extensions to constraint solver."""
#
#   test/test_constraint.py
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
from constraint import *
from soffit.constraint import *

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
        return { 'a' : list( range( 0, 10 ) ),
                 'b' : list( range( 0, 10 ) ),
                 'c' : list( range( 0, 10 ) ),
                 'd' : list( range( 0, 10 ) ) }
                 
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
        constraints = [ ( tc, [variables] ), ( tc, ['x', 'y', 'z'] ) ]
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
        return { 'a' : list( range( 0, 10 ) ),
                 'b' : list( range( 0, 10 ) ),
                 'c' : list( range( 0, 10 ) ),
                 'd' : list( range( 0, 10 ) ) }
    
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
                
if __name__ == '__main__':
    unittest.main()

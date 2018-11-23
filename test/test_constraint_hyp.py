"""Test extensions to constraint solver, using Hypothesis."""
#
#   test/test_constraint_hyp.py
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
from hypothesis import given, assume, note, reproduce_failure
import hypothesis.strategies as st
import itertools

class TestTupleConstraint(unittest.TestCase):
    @given( st.lists( st.text(), min_size=2, max_size=2, unique=True ),
            st.lists( st.integers( 1, 100 ),  min_size=2, max_size=2 ),
            st.data() )
    def test_satisfiability_2( self, variables, ranges, data ):        
        p = Problem()
        p.addVariable( variables[0], range( ranges[0] ) )
        p.addVariable( variables[1], range( ranges[1] ) )

        tuples = data.draw( st.sets( st.tuples( st.integers( 0, ranges[0] - 1 ),
                                                st.integers( 0, ranges[1] - 1 ) ) ) )

        p.addConstraint( TupleConstraint( tuples ), [variables[0], variables[1]] )
        solns = p.getSolutions()
        note( "Solutions: {}".format( solns ) )
        solnTuples = set( ( s[variables[0]], s[variables[1]]) for s in solns )
        self.assertEqual( solnTuples, tuples )

    @given( st.lists( st.text(), min_size=3, max_size=3, unique=True ),
            st.lists( st.integers( 1, 100 ), min_size=3, max_size=3 ),
            st.data() )
    def test_satisfiability_3( self, variables, ranges, data ):        
        p = Problem()
        p.addVariable( variables[0], range( ranges[0] ) )
        p.addVariable( variables[1], range( ranges[1] ) )
        p.addVariable( variables[2], range( ranges[2] ) )

        tuples = data.draw( st.sets( st.tuples( st.integers( 0, ranges[0] - 1 ),
                                                st.integers( 0, ranges[1] - 1 ),
                                                st.integers( 0, ranges[2] - 1 ) ) ) )
            
        p.addConstraint( TupleConstraint( tuples ), [variables[0], variables[1], variables[2]] )
        solns = p.getSolutions()
        note( "Solutions: {}".format( solns ) )
        solnTuples = set( ( s[variables[0]], s[variables[1]], s[variables[2]] ) for s in solns )
        self.assertEqual( solnTuples, tuples )


    @given( st.lists( st.text(), min_size=3, max_size=3, unique=True ),
            st.lists( st.integers( 1, 100 ), min_size=3, max_size=3 ),
            st.data() )
    def test_satisfiability_chain( self, variables, ranges, data ):        
        p = Problem()
        p.addVariable( variables[0], range( ranges[0] ) )
        p.addVariable( variables[1], range( ranges[1] ) )
        p.addVariable( variables[2], range( ranges[2] ) )

        tuples01 = data.draw( st.sets( st.tuples( st.integers( 0, ranges[0] - 1 ),
                                                  st.integers( 0, ranges[1] - 1 ) ) ) )
        
        tuples12 = data.draw( st.sets( st.tuples( st.integers( 0, ranges[1] - 1 ),
                                                  st.integers( 0, ranges[2] - 1 ) ) ) )

        p.addConstraint( TupleConstraint( tuples01 ), [variables[0], variables[1]] )
        p.addConstraint( TupleConstraint( tuples12 ), [variables[1], variables[2]] )
        solns = p.getSolutions()
        note( "Solutions: {}".format( solns ) )        
        solnTuples = set( ( s[variables[0]], s[variables[1]], s[variables[2]] ) for s in solns )
        for (a,b,c) in solnTuples:
            self.assertIn( (a,b), tuples01 )
            self.assertIn( (b,c), tuples12 )

        for (a,b) in tuples01:
            for (b2,c) in tuples12:
                if b == b2:
                    self.assertIn( (a,b,c), solnTuples )


variableNames = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

class TestConditionalConstraint(unittest.TestCase):
    def solnToTuple( self, numVariables, soln ):
        return tuple( soln[v] for v in variableNames[:numVariables] )
        
    @given( st.integers( 2, 4 ), st.data() )        
    def test_conditional( self, numVariables, data ):
        rangeSize = 10
        p1 = Problem()
        p2 = Problem()
        for i in range( numVariables ):
            p1.addVariable( variableNames[i], range( rangeSize ) )
            p2.addVariable( variableNames[i], range( rangeSize ) )

        conditions = data.draw( st.lists(
            st.lists( st.integers( 0, rangeSize ),
                      min_size = numVariables,
                      max_size = numVariables ),
            min_size = 0,
            max_size = 3 ** numVariables ) )
        conditions = [ tuple(c) for c in conditions ]

        p1.addConstraint( ConditionalTupleConstraint( conditions ),
                          variableNames[:numVariables] )

        conditions.sort()
        for k, g in itertools.groupby( conditions, key=lambda x : x[0] ):
            tc = TupleConstraint( list( t[1:] for t in g ) )
            cc = ConditionalConstraint( k, tc )
            p2.addConstraint( cc, variableNames[:numVariables] )

        soln1 = set( self.solnToTuple( numVariables, s )
                     for s in p1.getSolutions() )
        soln2 = set( self.solnToTuple( numVariables, s )
                     for s in p2.getSolutions() )

        self.assertEqual( soln1, soln2 )
        
        
            
        

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
import networkx as nx
import soffit.graph as sg
from soffit.parse import parseGraphString

class TestGraphRewrite(unittest.TestCase):
    def dump_text( self, g ):
        for n in g.nodes:
            if 'tag' in g.nodes[n]:
                print( "{} [{}];".format( n, g.nodes[n]['tag'] ) )
            else:
                print( "{};".format( n ) )

        for (a,b) in g.edges:
            if 'tag' in g.edges[a,b]:
                print( "{} -- {} [{}];".format( a, b, g.edges[a,b]['tag'] ) )
            else:
                print( "{} -- {};".format( a, b ) )
                    
    def setup_rewrite( self, l, r, g, realMatches = True ):
        l = parseGraphString( l )
        r = parseGraphString( r )
        g = sg.graphIdentifiersToNumbers( parseGraphString( g ) )
        print()
        print( "*** BEFORE ***" )
        self.dump_text( g )

        self.before = g
        
        finder = sg.MatchFinder( g, verbose=False)
        finder.leftSide( l )
        finder.rightSide( r )
        self.finder = finder

        if realMatches:
            return finder.matches()
        
    def test_linear_chain(self):
        mList = self.setup_rewrite( l = "A[left]; B[right]; A--B",
                                    r = "A; B[left]; C[right]; A--B--C",
                                    g = "X[left]; Y[right]; Z[head]; Z--X--Y" )
        for m in mList:
            print( m )

        match = mList[0]
        rule = sg.RuleApplication( self.finder, match )
        g2 = rule.result()
                            
        print()
        print( "*** AFTER ***" )
        self.dump_text( g2 )


if __name__ == '__main__':
    unittest.main()

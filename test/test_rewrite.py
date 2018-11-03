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

verbose = True

class TestGraphRewrite(unittest.TestCase):
    def dump_text( self, g ):
        for n in g.nodes:
            if 'tag' in g.nodes[n]:
                print( "{} [{}];".format( n, g.nodes[n]['tag'] ) )
            else:
                print( "{};".format( n ) )

        if nx.is_directed( g ):
            arrow  = "->"
        else:
            arrow = "--"
            
        for (a,b) in g.edges:
            if 'tag' in g.edges[a,b]:
                print( "{} {} {} [{}];".format( a, arrow, b, g.edges[a,b]['tag'] ) )
            else:
                print( "{} {} {};".format( a, arrow, b ) )

    def make_all_directed( self, l, r, g ):
        if nx.is_directed( l ) or nx.is_directed( r ) or nx.is_directed( g ):
            if not nx.is_directed( l ):
                l = l.to_directed()
            if not nx.is_directed( r ):
                r = r.to_directed()
            if not nx.is_directed( g ):
                g = g.to_directed()
        return (l, r, g)
        
    def setup_rewrite( self, l, r, g, realMatches = True ):
        l = parseGraphString( l )
        r = parseGraphString( r, joinAllowed=True )
        g = sg.graphIdentifiersToNumbers( parseGraphString( g ) )
        (l, r, g) = self.make_all_directed( l, r, g )
        
        self.before = g

        if verbose:
            print()
            print( "*** BEFORE ***" )
            self.dump_text( g )
        
        finder = sg.MatchFinder( g, verbose=False)
        #finder = sg.MatchFinder( g, verbose=True)
        finder.leftSide( l )
        finder.rightSide( r )
        self.finder = finder

        if realMatches:
            return finder.matches()

    def perform_rewrite( self, l, r, g ):
        mList = self.setup_rewrite( l, r, g, True )
        self.match = mList[0]
        if verbose:
            print( self.match )
            
        self.rule = sg.RuleApplication( self.finder, self.match )
        self.after = self.rule.result()

        if verbose:
            print()
            print( "*** AFTER ***" )
            self.dump_text( self.after )
        
    def find_any_tags( self, graph, *tt ):
        byTag = {}
        for n in graph.nodes:
            if 'tag' in graph.nodes[n]:
                byTag[graph.nodes[n]['tag']] = n
        return [ byTag.get( t, None ) for t in tt ]
    
    def test_linear_chain(self):
        self.perform_rewrite( l = "A[left]; B[right]; A--B",
                              r = "A; B[left]; C[right]; A--B--C",
                              g = "X[left]; Y[right]; Z[head]; Z--X--Y" )
        g2 = self.after
        ( n_head, n_left, n_right ) = self.find_any_tags( g2, 'head', 'left', 'right' )
        self.assertIsNotNone( n_head )
        self.assertIsNotNone( n_left )
        self.assertIsNotNone( n_right )
        self.assertIn( ( n_left, n_right ), g2.edges )
        self.assertNotIn( ( n_head, n_left ), g2.edges )

    def test_merge_delete(self):
        self.perform_rewrite( l = "A[target]; A--B; A--C; A--D",
                              r = "B^C^D [star]",
                              g = "X[target]; L--X--R; X--Y" )
        g2 = self.after
        self.assertEqual( len( g2.nodes ), 1 )
        self.assertEqual( len( g2.edges ), 0 )
        n = list( g2.nodes )[0]
        self.assertEqual( g2.nodes[n]['tag'], 'star' )
        
    def test_merge_delete_self_loop(self):
        self.perform_rewrite( l = "A[target]; A--B; A--C; A--D",
                              r = "B^C^D [star]; B--D",
                              g = "X[target]; L--X--R; X--S" )
        g2 = self.after
        self.assertEqual( len( g2.nodes ), 1 )
        self.assertEqual( len( g2.edges ), 1 )
        n = list( g2.nodes )[0]
        self.assertEqual( g2.nodes[n]['tag'], 'star' )
        self.assertIn( (n,n), g2.edges )

    def test_merge_attached(self):
        self.perform_rewrite( l = "A[1]; B[2]",
                              r = "A^B [3]",
                              g = "X[1]; Y[2]; Z[4]; X--Y--Z" )
        g2 = self.after
        self.assertEqual( len( g2.nodes ), 2 )
        self.assertEqual( len( g2.edges ), 2 )
        ( n_1, n_2, n_3, n_4 ) = self.find_any_tags( g2, '1', '2', '3', '4' )

        self.assertIsNone( n_1 )
        self.assertIsNone( n_2 )
        self.assertIsNotNone( n_3 )
        self.assertIsNotNone( n_4 )
        self.assertIn( (n_3,n_3), g2.edges )
        self.assertIn( (n_3,n_4), g2.edges )

    def test_two_merges(self):
        # The merged edge could get *either* tag, but it must get one.
        self.perform_rewrite( l = "A[1]; B[2]; C[3]; D[4];",
                              r = "A^B[12]; C^D[34]",
                              g = "W[1]; X[2]; Y[3]; Z[4]; X--Y[x]; Y--Z[y]; Z--W[z]; W--X[w]" )
        g2 = self.after
        ( n_12, n_34 ) = self.find_any_tags( g2, '12', '34' )
        self.assertIsNotNone( n_12 )
        self.assertIsNotNone( n_34 )
        self.assertIn( (n_12, n_34), g2.edges )
        self.assertIn( g2.edges[n_12,n_34]['tag'], ['x', 'z']  )
        
    def test_directed_delete(self):
        self.perform_rewrite( l = "A->B; A[target]",
                              r = "A [target]; B [other];",
                              g = "X--Y; X[target]" )
        g2 = self.after
        ( n_t, n_o ) = self.find_any_tags( g2, 'target', 'other' )
        self.assertIsNotNone( n_t )
        self.assertIsNotNone( n_o )
        self.assertNotIn( (n_t, n_o), g2.edges )
        self.assertIn( (n_o, n_t), g2.edges )

    def test_directed_tags(self):
        self.perform_rewrite( l = "A->B [target];",
                              r = "A[src]; B[dst];",
                              g = "X->Y [target]; Y->X [not];" )
        g2 = self.after
        self.assertEqual( len( g2.edges ), 1 )
        (s,t) = next( iter( g2.edges ) )
        self.assertEqual( g2.edges[s,t]['tag'], 'not' )

    def test_directed_creation(self):
        self.perform_rewrite( l = "A->B->D; A->C->D",
                              r = "A->B->D; A->C->D; A[src]; D[dst]; A->D [new]",
                              g = "m->n; n->o; p->o; m->p" )
        g2 = self.after
        self.assertEqual( len( g2.edges ), 5 )
        ( n_s, n_d ) = self.find_any_tags( g2, 'src', 'dst' )
        self.assertEqual( g2.edges[n_s,n_d]['tag'], 'new' )

if __name__ == '__main__':
    unittest.main()

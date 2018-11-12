"""Graph and grammar generation functions."""
#
#   soffit/graph.py
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

import networkx as nx

def nameGenerator():
    i = 0
    while True:
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            yield c + str( i )
        i += 1
    
def rename( g ):
    numNodes = len( g.nodes )
    remap = dict( zip( g.nodes, nameGenerator() ) )
    return nx.relabel.relabel_nodes( g, remap, copy=False )

def compactRep( g ):
    directed = nx.is_directed( g )
    components = []
    for n in g.nodes:
        if 'tag' in g.nodes[n]:
            # Specify all nodes that have tags
            components.append( str( n ) + "[" + g.nodes[n]['tag'] + "]" )
        else:
            # Specify nodes with no edges
            if directed:
                if len( g.predecessors( n ) ) == 0 and len( g.successors( n ) ) == 0:
                    components.append( str( n ) )            
            else:
                if len( g[n] ) == 0:
                    components.append( str( n ) )            

    for (s,t) in g.edges:
        if directed:
            edge = str(s) + "->" + str( t ) 
        else:
            edge = str(s) + "--" + str( t )
        if 'tag' in g.edges[s,t]:
            edge += ( "[" + g.edges[s,t]['tag'] + "]" )
        components.append( edge )
    return ";".join( components )

def applyTags( g, nodeTag, edgeTag ):
    if nodeTag is not None:
        for n in g.nodes:
            g.nodes[n]['tag'] = nodeTag
    if edgeTag is not None:
        for e in g.edges:
            g.edges[e]['tag'] = edgeTag

        
def undirectedSquareGrid( m, n, nodeTag = None, edgeTag = None ):
    g = nx.generators.lattice.grid_2d_graph( m, n )
    applyTags( g, nodeTag, edgeTag )
    return g

grammarTemplate = """\
{{
  "version" : "0.1",
  "start" : "{}"
}}
"""

def grammarWithStartRule( start ):
    rename( start )
    return grammarTemplate.format( compactRep( start ) )
    
if __name__ == "__main__":
    g = undirectedSquareGrid( 5, 5, nodeTag="x" )
    print( grammarWithStartRule( g ) )
    
    

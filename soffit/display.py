"""Display of graphs and graph grammar rules."""
#
#   soffit/display.py
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
import matplotlib.pyplot as plt
from soffit.parse import parseGraphString, ParseError

def drawGraphSimple( g ):
    pos = nx.spring_layout( g )    

    nx.draw_networkx_nodes( g, pos, node_size=500 )
    nx.draw_networkx_labels( g, pos )
    
    offset_right = { n : (x + 0.1, y) for ( n, (x,y) ) in pos.items() }
    node_tags = { n : "[{}]".format( g.nodes[n]['tag'] ) for n in g.nodes if 'tag' in g.nodes[n] }
    print( node_tags )
    nx.draw_networkx_labels( g, offset_right, labels = node_tags )
    
    nx.draw_networkx_edges( g, pos, edge_labels = {} )
    edge_tags = { e : g.edges[e]['tag'] for e in g.edges if 'tag' in g.edges[e] }
    nx.draw_networkx_edge_labels( g, pos, edge_labels = edge_tags )

    plt.savefig( "test.png" )

if __name__ == "__main__":
    import sys
    try:
        g = parseGraphString( sys.argv[1], joinAllowed=True )
    except ParseError as pe:
        pe.prettyPrint()
        exit( 1)
        
    drawGraphSimple( g )
        

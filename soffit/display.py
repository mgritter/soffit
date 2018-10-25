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
from soffit.parse import parseGraphString

def drawGraphString( text ):
    g = parseGraphString( text )
    nx.drawing.nx_pylab.draw_networkx( g )
    plt.savefig( "/u/mgritter/public_html/test.png" )

if __name__ == "__main__":
    import sys
    drawGraphString( sys.argv[1] )
    

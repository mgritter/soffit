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
from soffit.graph import MatchFinder, RuleApplication, graphIdentifiersToNumbers
from networkx.drawing.nx_agraph import to_agraph

def convertTagToLabel( attr ):
    if 'tag' in attr:
        attr['label'] = attr['tag']
        del attr['tag']

def convertTagToAttributeList( attr ):
    if 'tag' in attr and '=' in attr['tag']:
        # FIXME: allow semicolon
        aList = attr['tag'].split( "," )
        del attr['tag']
        for a in aList:
            (k,v) = a.strip().split( '=' )
            attr[k] = v
    else:
        convertTagToLabel( attr )

def tagsToLabels( g, ignoreEquals = False ):
    """Change all the tags in graph g into Dot labels for use with Graphviz.
    tag="x" will become label="x".
    
    Covert any tags which already appear to have an equal sign in them:

    tag="name"                     => { label : 'name' }
    tag="color=red; shape=circle;" => { color : 'red', shape : 'circle' }

    Returns a copy of the graph.
    """
    rg = g.copy()
    for n in rg.nodes:
        attr = rg.nodes[n]
        if ignoreEquals:
            convertTagToLabel( attr )
        else:
            convertTagToAttributeList( attr )            

    for e in rg.edges:
        attr = rg.edges[e]
        if ignoreEquals:
            convertTagToLabel( attr )
        else:
            convertTagToAttributeList( attr )            

    return rg

def drawSvg( g, filename ):
    toDraw = tagsToLabels( g )
    del toDraw.graph['join']
    del toDraw.graph['rename']
    aGraph = to_agraph( toDraw )
    aGraph.draw( filename, prog='dot' )

def colorElement( attr, color, name = ""):
    attr['color'] = color
    if 'tag' in attr:
        attr['label'] = str( name ) + ":" + attr['tag']
        del attr['tag']
    else:
        attr['label'] = str( name )
    
def colorGraph( g, color ):
    g = g.copy()
    del g.graph['join']
    del g.graph['rename']
    for n in g.nodes:
        colorElement( g.nodes[n], color, n )
    for e in g.edges:
        colorElement( g.edges[e], color )
    return g

def drawMatch( l, r, g, h, m, outputFile ):
    l = colorGraph( l, 'green' )
    r = colorGraph( r, 'red' )
    g = colorGraph( g, 'black' )
    h = colorGraph( h, 'blue' )

    for n in l.nodes:
        g.nodes[m.node(n)]['color'] = 'purple'
    for e in l.edges:
        g.edges[m.edge(e)]['color'] = 'purple'
    
    collection = nx.disjoint_union( l, r )
    collection = nx.disjoint_union( collection, g )
    collection = nx.disjoint_union( collection, h )
    
    lNums = range( 0, len( l.nodes ) )
    y = lNums[-1] + 1
    rNums = range( y, y + len( r.nodes ) )
    y = rNums[-1] + 1
    gNums = range( y, y + len( g.nodes ) )
    y = gNums[-1] + 1
    hNums = range( y, y + len( h.nodes ) )
    
    agraph = to_agraph( collection )
    agraph.graph_attr['rankdir']='LR'
    agraph.add_subgraph( lNums, "cluster_L", label="L", pos="10,10" )
    agraph.add_subgraph( rNums, "cluster_R", label="R" )
    agraph.add_subgraph( gNums, "cluster_G", label="G" )
    agraph.add_subgraph( hNums, "cluster_H", label="H" )
    agraph.write( "debug.gv" )
    agraph.draw( outputFile, prog='neato' )
    
def showMatches( l, r, g, outputFile ):
    try:
        l = parseGraphString( l )
        r = parseGraphString( r, joinAllowed=True )
        g = graphIdentifiersToNumbers( parseGraphString( g ) )
    except ParseError as pe:
        pe.prettyPrint()
        exit( 1 )

    finder = MatchFinder( g )
    finder.leftSide( l )
    finder.rightSide( r )
    allMatches = finder.matches()

    for (i,m) in enumerate( allMatches[:20] ):
        if len( allMatches ) > 0:
            fn = outputFile.split( "." )
            myFile = ".".join( fn[0:-1] + [str(i)] + fn[-1:] )
            print( myFile, m )
        else:
            myFile = outputFile

        h = RuleApplication( finder, m ).result()
        drawMatch( l, r, g, h, m, myFile )

def showGraph( graphString, outputFile ):
    try:
        g = parseGraphString( graphString, joinAllowed=True )
    except ParseError as pe:
        pe.prettyPrint()
        exit( 1 )

    drawSvg( g, outputFile )
    
def usage():
    print( "python -m soffit.display <string>" )
    print( "  Parse graph and output as test.png." )
    print( "python -m soffit.display <string> <filename>" )
    print( "  Parse graph and output as <filename>." )
    print( "python -m soffit.display --matches <l> <r> <g> <filename>" )
    print( "  Parse rule l=>r and show its application to g in <filename>." )
    print( "  If multiple matches, <filename> will have a number inserted." )               
    exit( 0 )

if __name__ == "__main__":
    import sys
    outputFile = "test.svg"
    if len( sys.argv ) == 1:
        usage()
    
    if len( sys.argv ) == 2:
        showGraph( sys.argv[1], outputFile )
        exit( 0 )
        
    if sys.argv[1] == "--matches":
        if len( sys.argv ) == 6:
            outputFile = sys.argv[5]
        showMatches( sys.argv[2], sys.argv[3], sys.argv[4], outputFile )
    else:
        usage()
            

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
from soffit.parse import parseGraphString, ParseError, loadGraphGrammar
from soffit.graph import MatchFinder, RuleApplication, graphIdentifiersToNumbers
import soffit.application
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
    aGraph.graph_attr['overlap'] = 'false'
    aGraph.graph_attr['outputorder'] = 'edgesfirst'
    aGraph.node_attr['style']='filled'
    aGraph.node_attr['fillcolor']='white'
    if len( g.nodes ) > 1000:
        aGraph.draw( filename, prog='sfdp' )
    else:
        aGraph.draw( filename, prog='neato' )

    
def reposition_pos( pos, yOffset, xOffset ):\
    return " ".join(
        ",".join( [ str( float( y ) + yOffset ),
                    str( float( x ) + xOffset ) ] )
        for coord in pos.split( " " )
        for (y,x) in [ coord.split( "," ) ]
    )

def position( graph ):
    """Render a graph with 'neato', and return its bounding box."""
    agraph = to_agraph( graph )
    agraph.layout( prog='neato' )
    for n in graph.nodes:
        graph.nodes[ n ]['pos'] = agraph.get_node( n ).attr['pos']
    for (s,t) in graph.edges:
        graph.edges[s,t]['pos'] = agraph.get_edge( s, t ).attr['pos']
    return [ float(i) for i in agraph.graph_attr['bb'].split( ',' ) ]

def reposition( graph, xOffset, yOffset ):
    """Update all pos attributes to a different location."""
    for n in graph.nodes:
        graph.nodes[ n ]['pos'] = reposition_pos( graph.nodes[n]['pos'],
                                                  yOffset, xOffset )
    for (s,t) in graph.edges:
        graph.edges[s,t]['pos'] = reposition_pos( graph.edges[s,t]['pos'],
                                                  yOffset, xOffset )
        
def colorElement( attr, color, name = ""):
    attr['color'] = color
    if 'tag' in attr:
        if name == "":
            attr['label'] = attr['tag']
        else:
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

    (_, _, leftX, leftY) = position( l )
    (_, _, gX, gY) = position( g )
    # FIXME: initialize r with l's positions
    (_, _, rightX, rightY) = position( r )
    # FIXME: initialize h with g's positions
    (_, _, hX, hY) = position( h )

    centerX = max( leftX, gX )
    centerY = max( gY, hY )
    # Lower left - Bring g up to the center line
    reposition( g, centerY - gY, 0.0 )
    # Lower right
    reposition( h, centerY - hY, centerX + 10 )
    # Upper left
    reposition( l, centerY + 10, 0.0 )
    # Upper right
    reposition( r, centerY + 10, centerX + 10 )
    
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

    dot = False
    if dot:
        # Add invisible nodes and edges to try to line up the clusters.
        agraph.add_node( "rank0", style="invis" )
        agraph.add_node( "rankL", style="invis" )
        agraph.add_node( "rankR", style="invis" )
        agraph.add_edge( "rank0", "rankL", style="invis" )
        agraph.add_edge( "rank0", "rankR", style="invis" )
        agraph.add_node( "rankG", style="invis" )
        agraph.add_node( "rankH", style="invis" )
        agraph.add_edge( "rankL", "rankG", style="invis" )
        agraph.add_edge( "rankR", "rankH", style="invis" )
        for g in gNums:
            agraph.add_edge( "rankL", g, style="invis" )
        for h in hNums:
            agraph.add_edge( "rankR", h, style="invis" )
        lNums = list( lNums ) + ["rankL"]
        rNums = list( rNums ) + ["rankR"]
        gNums = list( gNums ) + ["rankG"]
        hNums = list( hNums ) + ["rankH"]
            
    agraph.add_subgraph( lNums, "cluster_L", label="L" )
    agraph.add_subgraph( rNums, "cluster_R", label="R" )
    agraph.add_subgraph( gNums, "cluster_G", label="G" )
    agraph.add_subgraph( hNums, "cluster_H", label="H" )
    # agraph.write( "debug.gv" )
    agraph.draw( outputFile, prog="neato", args="-n" )
    
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

svgXmlHeader = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">"""

def removeHeader( svg ):
    try:
        i = svg.index( svgXmlHeader )
        return svg[:i] + svg[i+len( svgXmlHeader ):]
    except ValueError:
        return svg

def appendTag( g1 ):
    for n in g1:
        if 'tag' in g1.nodes[n]:
            g1.nodes[n]['label'] = str( n ) + ":" + g1.nodes[n]['tag']
    for e in g1.edges:
        if 'tag' in g1.edges[e]:
            g1.edges[e]['label'] = ":" + g1.edges[e]['tag']
    return g1

def transferPositions( g1, g2 ):
    for n in g1.nodes:
        if n in g2.nodes:
            g2.nodes[n]['pos'] = g1.nodes[n]['pos']
    
                      
def getSvgForGraphPair( before, after, leftToRight=False ):
    g1 = before.copy()
    g2 = after.copy()

    appendTag( g1 )
    appendTag( g2 )

    for n in g2:
        if 'tag' in g2.nodes[n] and n in g1:
            if g1.nodes[n].get( 'tag', None ) != g2.nodes[n].get( 'tag' ):
                g2.nodes[n]['fontcolor'] = 'red'

    edgesDeleted = [ e for e in g1.edges if e not in g2.edges ] 
    nodesDeleted = [ n for n in g1.nodes if n not in g2.nodes ]     
    edgesAdded = [ e for e in g2.edges if e not in g1.edges ] 
    nodesAdded = [ n for n in g2.nodes if n not in g1.nodes ]

    for n in nodesDeleted:
        g1.nodes[n]['color'] = 'red'
        g1.nodes[n]['fontcolor'] = 'red'
        g2.add_node( n, color="white", label="" )
    for n in nodesAdded:
        g2.nodes[n]['color'] = 'green'
        g2.nodes[n]['fontcolor'] = 'green'
        g1.add_node( n, color="white", label="" )

    for (s,t) in edgesDeleted:
        g1.edges[s,t]['color'] = 'red'
        g1.edges[s,t]['fontcolor'] = 'red'
        g2.add_edge( s, t, color="white" )

    for (s,t) in edgesAdded:
        g2.edges[s,t]['color'] = 'green'
        g2.edges[s,t]['fontcolor'] = 'green'
        g1.add_edge( s, t, color="white" )

    if leftToRight:
        (_,_,x1,y1) = position( g1 )
        transferPositions( g1, g2 )
        (_,_,x2,y2) = position( g2 )
    else:
        (_,_,x2,y2) = position( g2 )
        transferPositions( g2, g1 )
        (_,_,x1,y1) = position( g1 )

    # Graphviz uses 96 DPI by default
    desiredX = max( x1, x2 ) / 96.0
    desiredY = max( y1, y2 ) / 96.0

    sizeAttr = "{},{}!".format( desiredX, desiredY )

    ag1 = to_agraph( g1 )
    ag1.graph_attr['size'] = sizeAttr
    s1 = ag1.draw( format="svg", prog="neato" )
    
    ag2 = to_agraph( g2 )
    ag2.graph_attr['size'] = sizeAttr
    s2 = ag2.draw( format="svg", prog="neato" )
    
    return ( s1.decode("utf-8"), s2.decode("utf-8") )

htmlHeader = """<html>
<head>
</head>
<body>
<div style="display: grid; grid-template-columns: auto auto; grid-column-gap:50px; ">
"""

htmlFooter = """
</div></body></html>
"""

divFormat = """
<div>
{0}
</div>
<div>
{1}
</div>
<div style="grid-column: 1 /span 2;border-bottom: 4px solid gray;">
</div>
"""

def drawGrammar( ruleFilename, outputFilename ):
    try:
        with open( ruleFilename, "r" ) as inFile:
            grammar = loadGraphGrammar( inFile )
    except ParseError as pe:
        pe.prettyPrint()
        exit( 1 )

    with open( outputFilename, "w" ) as outFile:
        outFile.write( htmlHeader )
        for (l, r) in grammar.rulesIter():
            (sl, sr) = getSvgForGraphPair( l, r )
            outFile.write( divFormat.format( removeHeader( sl ),
                                             removeHeader( sr ) ) )
        outFile.write( htmlFooter )

movieFormat = """
<div>
{0}
</div>
<div style="border: 1px solid black;>
{1}
</div>
"""

def writeGraphIteration( outFile, i, size, lastGraph, g ):
    appendTag( g )
    if lastGraph is not None:
        transferPositions( lastGraph, g )
        for n in g.nodes:
            if n not in lastGraph:
                g.nodes[n]['color'] = 'green'
        
    g.graph['size'] = size
    position( g )
    
    ag = to_agraph( g )
    svg = ag.draw( format="svg", prog="neato" ).decode( 'utf-8' )
    print( movieFormat.format( i, svg ), file=outFile )

def drawMovie( ruleFilename, outputFilename ):
    # FIXME: move this to a common function
    try:
        with open( ruleFilename, "r" ) as inFile:
            grammar = loadGraphGrammar( inFile )
    except ParseError as pe:
        pe.prettyPrint()
        exit( 1 )

    with open( outputFilename, "w" ) as outFile:
        outFile.write( htmlHeader )
        lastGraph = None
        
        def callback( i, g ):
            nonlocal lastGraph
            myG = g.copy()
            writeGraphIteration( outFile=outFile,
                                 i=i,
                                 size="5,5",
                                 lastGraph=lastGraph,
                                 g=myG )
            lastGraph = myG

        soffit.application.applyRuleset( ruleFilename, "fixme.tmp.svg", callback=callback ) 
        outFile.write( htmlFooter )

def usage():
    print( "python -m soffit.display <string>" )
    print( "  Parse graph and output as test.svg." )
    print( "python -m soffit.display <string> <filename>" )
    print( "  Parse graph and output as <filename>." )
    print( "python -m soffit.display --matches <l> <r> <g> <filename>" )
    print( "  Parse rule l=>r and show its application to g in <filename>." )
    print( "  If multiple matches, <filename> will have a number inserted." )               
    print( "python -m soffit.display --grammar <rule.json> <outputfile>" )
    print( "  Parse a graph grammar and display it as an HTML page with embedded SVG images." )
    print( "python -m soffit.display --movie <rule.json> <outputfile>" )
    print( "  Apply a graph grammar and display it as an HTML page with embedded SVG images." )
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
    elif sys.argv[1] == "--grammar":
        drawGrammar( sys.argv[2], sys.argv[3] )
    elif sys.argv[1] == "--movie":
        drawMovie( sys.argv[2], sys.argv[3] )
    else:
        usage()
            

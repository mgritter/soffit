"""Parsing library for graphs and graph grammar rules."""
#
#   soffit/parse.py
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

import json
from pyparsing import Word, Literal, OneOrMore, Optional, Group, ParseException, StringEnd
from pyparsing import delimitedList
import networkx as nx
from soffit.grammar import GraphGrammar

# Copied from Swift,
# see https://docs.swift.org/swift-book/ReferenceManual/LexicalStructure.html

def inclusiveRange( a, b ):
    return range( a, b + 1 )

def _buildUnicodeWord():
    # FIXME: the startup time is horrendous and parsing a multi-megabyte
    # regular expression can't be helping.
    # Write our own pyparsing class that's a replacement for Word?
    # Or back off on the unicode ranges for now.
    _headRanges = [ 
        inclusiveRange( 0x0041,0x005A ),
        inclusiveRange( 0x0061,0x007A ),    
        inclusiveRange( 0x00B2,0x00B5 ),
        inclusiveRange( 0x00B7,0x00BA ),
        inclusiveRange( 0x00BC,0x00BE ),
        inclusiveRange( 0x00C0,0x00D6 ),
        inclusiveRange( 0x00D8,0x00F6 ),
        inclusiveRange( 0x00F8,0x00FF ),
        inclusiveRange( 0x0100,0x02FF ),
        inclusiveRange( 0x0370,0x167F ),
        inclusiveRange( 0x1681,0x180D ),
        inclusiveRange( 0x180F,0x1DBF ),
        inclusiveRange( 0x1E00,0x1FFF ),
        inclusiveRange( 0x200B,0x200D ),
        inclusiveRange( 0x202A,0x202E ),
        inclusiveRange( 0x203F,0x2040 ),
        inclusiveRange( 0x2060,0x206F ),
        inclusiveRange( 0x2070,0x20CF ),
        inclusiveRange( 0x2100,0x218F ),
        inclusiveRange( 0x2460,0x24FF ),
        inclusiveRange( 0x2776,0x2793 ),
        inclusiveRange( 0x2C00,0x2DFF ),
        inclusiveRange( 0x2E80,0x2FFF ),
        inclusiveRange( 0x3004,0x3007 ),
        inclusiveRange( 0x3021,0x302F ),
        inclusiveRange( 0x3031,0x303F ),
        inclusiveRange( 0x3040,0xD7FF ),
        inclusiveRange( 0xF900,0xFD3D ),
        inclusiveRange( 0xFD40,0xFDCF ),
        inclusiveRange( 0xFDF0,0xFE1F ),
        inclusiveRange( 0xFE30,0xFE44 ),
        inclusiveRange( 0xFE47,0xFFFD ),
        inclusiveRange( 0x10000,0x1FFFD ),
        inclusiveRange( 0x20000,0x2FFFD  ),
        inclusiveRange( 0x30000,0x3FFFD ),
        inclusiveRange( 0x40000,0x4FFFD ),
        inclusiveRange( 0x50000,0x5FFFD ),
        inclusiveRange( 0x60000,0x6FFFD ),
        inclusiveRange( 0x70000,0x7FFFD ),
        inclusiveRange( 0x80000,0x8FFFD ),
        inclusiveRange( 0x90000,0x9FFFD ),
        inclusiveRange( 0xA0000,0xAFFFD ),
        inclusiveRange( 0xB0000,0xBFFFD ),
        inclusiveRange( 0xC0000,0xCFFFD ),
        inclusiveRange( 0xD0000,0xDFFFD ),
        inclusiveRange( 0xE0000,0xEFFFD ),
    ]
    
    _headChars = \
        [ chr(c) for c in  [ 0x00A8, 0x00AA, 0x00AD, 0x00AF, 0x2054] ] + \
        [ chr(c) for r in _headRanges for c in r ]

    _identRanges = [
        inclusiveRange( 0x0030, 0x0039 ),
        inclusiveRange( 0x0300, 0x036F ),
        inclusiveRange( 0x1CD0, 0x1DFF ),
        inclusiveRange( 0x20D0, 0x20FF ),
        inclusiveRange( 0xFE20, 0xFE2F )
    ]
    
    _identChars = \
        [ chr(c) for r in _identRanges for c in r ]

    _identChars = _headChars + _identChars

    return Word( ''.join( _headChars ), ''.join( _identChars ) )( "vertex" )

biEdge = Literal( "--" )( "direction" )
unEdge = Literal( "->" )( "direction" )
unEdgeReversed = Literal( "<-" )( "direction" )
semicolon = Literal( ";" )

nodeName = _buildUnicodeWord()

destination = Group(
    ( biEdge + nodeName ) | 
    ( unEdge + nodeName ) | 
    ( unEdgeReversed + nodeName )
)

graphElements = Group( nodeName( "start" ) + OneOrMore( destination ) ) | \
                Group( nodeName( "solo" ) )

graph = delimitedList( graphElements, semicolon ) + Optional( semicolon ).suppress() + StringEnd()

class WorkingGraph(object):
    def __init__( self ):
        # Start with an undirected graph, convert if necessary
        self.graph = nx.Graph()
        self.undirected = True

    def addNode( self, n ):
        self.graph.add_node( n )
        
    def addDirected( self, a, b ):
        if self.undirected:
            self.undirected = False
            self.graph = self.graph.to_directed()

        self.graph.add_edge( a, b )

    def addUndirected( self, a, b ):
        if self.undirected:
            self.graph.add_edge( a, b )
        else:
            self.graph.add_edge( a, b )
            self.graph.add_edge( b, a )
        
def parseGraphString( inputString, quiet=False ):
    try:
        p = graph.parseString( inputString )
    except ParseException as err:
        # FIXME: handle big columns
        # FIXME: figure out how I want to report errors
        if not quiet:
            print( "Error parsing graph:" )
            print( inputString[0:err.column-1] )
            print( " " * (err.column-1) + inputString[err.column-1:] )
            print( " " * (err.column-1) + "^" )
            print( err )
        return None

    ret = WorkingGraph()
    
    for element in p:
        if 'solo' in element:
            ret.addNode( element['solo'] )
        elif 'start' in element:
            prev = element['start']
            for edge in element[1:]:
                if edge['direction'] == "--":
                    ret.addUndirected( prev, edge['vertex' ] )
                elif edge['direction'] == "->":
                    ret.addDirected( prev, edge['vertex'] )
                elif edge['direction'] == "<-":
                    ret.addDirected( edge['vertex'], prev )
                else:
                    print( "Unknown direction", edge['direction'] )
                    return None
                prev = edge['vertex']                        
        else:
            print( "Unknown element", element )
            return None

    return ret.graph
            
def _parseGraphGrammar_v01( obj, quiet = False ):
    gg = GraphGrammar()
    for (l,r) in obj.items():
        if l == "extensions":
            # FIXME: check for dict-like object?
            gg.extensions = r
        elif l == "version":
            pass
        elif l == "start":
            gg.start = parseGraphString( r )
            if gg.start == None:
                print( "Error parsing start position." )
                return None
        else:
            lg = parseGraphString( l )
            if lg == None:
                print( "Error parsing left-hand graph ", repr(lg) )
                return None
            
            if isinstance( r, list ):
                rgList = []
                for i in r:
                    rg = parseGraphString( i )
                    if rg == None:
                        print( "Error parsing right-hand graph ", repr(rg) )
                        return None
                    rgList.append( rg )
                gg.addChoice( lg, rgList )
            else:
                rg = parseGraphString( r )
                if rg == None:
                    print( "Error parsing right-hand graph ", repr(rg) )
                    return None
                gg.addRule( lg, rg )
        
    return gg                


def _dispatchGrammarParse( ggJson, quiet = False ):
    if 'version' not in ggJson or ggJson['version'] == "0.1":
        return _parseGraphGrammar_v01( ggJson )
    else:
        if not quiet:
            print( "Unknown version", ggJson['version'] )
        return None

def parseGraphGrammar( inputString, quiet=False ):
    # FIXME: handle parse error
    ggJson = json.loads( inputString )
    return _dispatchGrammarParse( ggJson )

def loadGraphGrammar( f, quiet=False ):
    # FIXME: handle parse error
    ggJson = json.load( f )
    return _dispatchGrammarParse( ggJson )



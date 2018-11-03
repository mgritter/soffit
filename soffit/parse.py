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
from pyparsing import Word, Literal, OneOrMore, Optional, Group, ParseException, StringEnd, QuotedString
from pyparsing import ParseResults
from pyparsing import delimitedList
import networkx as nx
from soffit.grammar import GraphGrammar
from itertools import zip_longest

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
#        inclusiveRange( 0x20000,0x2FFFD  ),
#        inclusiveRange( 0x30000,0x3FFFD ),
#        inclusiveRange( 0x40000,0x4FFFD ),
#        inclusiveRange( 0x50000,0x5FFFD ),
#        inclusiveRange( 0x60000,0x6FFFD ),
#        inclusiveRange( 0x70000,0x7FFFD ),
#        inclusiveRange( 0x80000,0x8FFFD ),
#        inclusiveRange( 0x90000,0x9FFFD ),
#        inclusiveRange( 0xA0000,0xAFFFD ),
#        inclusiveRange( 0xB0000,0xBFFFD ),
#        inclusiveRange( 0xC0000,0xCFFFD ),
#        inclusiveRange( 0xD0000,0xDFFFD ),
#        inclusiveRange( 0xE0000,0xEFFFD ),
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

biEdge = Literal( "--" )
unEdge = Literal( "->" )
unEdgeReversed = Literal( "<-" )
semicolon = Literal( ";" )

# This ought to be "v" for a join, not ^ for a meet.
# but, well, "v" isn't a special character, and "⋁" isn't on most keyboards.
join = Literal( "^" )

vertexId = _buildUnicodeWord()

def createJoinDictionary( s, loc, toks ):
    ret = ParseResults( toks[0] )
    # FIXME: raise an error if the same id appears more than once?
    # This just silently ignores the extra.
    ret['join'] = { t : toks[0] for t in toks[1:] if t != toks[0] }
    return ret

nodeName = delimitedList( vertexId, join ).setParseAction( createJoinDictionary )

destination = Group(
    ( biEdge + nodeName ) | 
    ( unEdge + nodeName ) | 
    ( unEdgeReversed + nodeName )
)

def mergeJoin( s, loc, toks, flatten = False ):
    union = {}
    flat = []
    # This only works if toks are all ParseObjects so we need to use
    # Group( nodeName ) to avoid getting just a string and having the
    # 'join' attribute lost.
    # But that's annoying, so we will collapse the list.
    for t in toks:
        if isinstance( t, str ):
            flat.append( t )
        else:
            flat.extend( t )
                
            if 'join' in t:
                for (k,v) in t['join'].items():
                    # Follow to the root of the set
                    # FIXME: replace with a real union-find?
                    while k in union:
                        k = union[k]
                    while v in union:
                        v = union[v]
                    if k != v:
                        union[k] = v

    if flatten:
        ret = ParseResults( flat )
        ret['join'] = union
        return ret
    else:
        toks['join'] = union

def mergeJoinFlatten( s, loc, toks ):
    return mergeJoin( s, loc, toks, flatten=True )
        
# Put in a tag but not in the result?
tag = QuotedString( quoteChar="[", endQuoteChar="]", escChar="\\" )("tag")

def dropTag( s, loc, toks ):
    if 'tag' in toks[0]:
        # The last element is copied into the 'tags' attribute already
        # so we don't need to parse it further
        # but... calling suppress() doesn't give it a result name.
        del toks[0][-1]
    return toks
            
edges = ( Group( nodeName ) + OneOrMore( destination ) ).setParseAction( mergeJoinFlatten ) + Optional( tag )

vertexOnly = nodeName + Optional( tag )

graphElement = Group( edges | vertexOnly ).setParseAction( dropTag )

def emptyJoinDictionary( s, loc, toks ):
    ret =  ParseResults( [] )
    ret['join'] = {}
    return ret
    
emptyGraph = Optional( semicolon ).suppress() + StringEnd().setParseAction( emptyJoinDictionary ) 

graph = ( delimitedList( graphElement, semicolon ).setParseAction( mergeJoin ) +
          Optional( semicolon ).suppress() + StringEnd() ) | emptyGraph

class ParseError(Exception):
    pass

    def prettyPrint( self ):
        print( "Unknown parser error." )

class MergeDisallowedError(ParseError):
    """A graph specified merged nodes in a situation where that was not permitted."""
    def __init__( self, graph ):
        self.graph = graph

    def prettyPrint( self ):
        print( "Graph has merged nodes." )

class MismatchedTagError(ParseError):
    """A vertex or node appeared with inconsistent tags attached."""
    pass

class MismatchedVertexError(MismatchedTagError):
    def __init__( self, node, newTag, oldTag ):        
        self.node = node 
        self.newTag = newTag
        self.oldTag = oldTag

    def prettyPrint( self ):
        print( "Vertex ID '{}' was given tag '{}' when it already had tag '{}'".format( self.node, self.newTag, self.oldTag ) )

class MismatchedEdgeError(MismatchedTagError):
    def __init__( self, src, dst, newTag, oldTag ):        
        self.src = src;
        self.dest = dst;
        self.newTag = newTag
        self.oldTag = oldTag

    def prettyPrint( self ):
        print( "Edge '{}->{}' was given tag '{}' when it already had tag '{}'".format( self.src, self.dst, self.newTag, self.oldTag ) )

class GraphParsingError(ParseError):
    """An error while parsing a graph."""
    def __init__( self, graph, parseError ):
        self.graph = graph
        self.parseError = parseError

    def prettyPrint( self ):
        print( "Error parsing graph: " + str( self.parseError ) )
        column = self.parseError.column
        # FIXME: for characters not equal-with, it would be better to split the line
        # FIXME: handle big columns by truncating?
        print( self.graph )
        text = "column {}".format( column ) 
        if column > len( text ) + 5:
            print( " " * (column-2-len(text)) + text + " ^" )
        else:
            print( " " * (column-1) + "^ " + text )

class GrammarParsingError(ParseError):
    """An error while parsing a rule."""
    def __init__( self, left, right, message, graphError = None, lineNumber = None ):
        self.left = left
        self.right = right
        self.message = message
        self.graphError = graphError
        self.lineNumber = None

    def updateLineNumber( self, inputText ):
        # This is a gross hack to try to find the rule in the
        # original JSON.
        try:
            startPos = 0
            index = inputText.index( '"' + self.left + '"', startPos )
            # FIXME: check that it's not on the right-hand side, probably
            # need to use an RE to get it right?
            self.lineNumber = 1 + inputText.count( "\n", 0, index )   
        except ValueError:
            pass

    def prettyPrint( self ):
        print()
        print( "Error parsing graph grammar: " + self.message )
        if self.lineNumber is not None:
            print( "  on line number", self.lineNumber )
        if self.graphError is not None:
            print( "  caused by:" )
            self.graphError.prettyPrint()
        else:
            print( '  Rule "' + self.left + '" : "' + self.right + '"' )

class WorkingGraph(object):
    def __init__( self, join = {} ):
        # Start with an undirected graph, convert if necessary
        # Annotate with merged nodes dictionary.
        # Ths dictionary should be used to canonicalize the graph so
        # merged nodes appear only once, and all tags can be checked
        # here rather than in a later step.

        self.join = join
        self.rename = {}

        # Make sure all nodes are correctly entered
        for (a,_) in self.join.items():
            self._followJoin( a )
        
        self.graph = nx.Graph( join = join, rename = self.rename )
        self.undirected = True

    def _followJoin( self, n ):
        if n in self.rename:
            return self.rename[n]

        path = [ n ]
        while n in self.join:
            n = self.join[n]
            # Did we meet an already-visited node?
            if n in self.rename:
                n = self.rename[n]
                break
            # No, but direct this intermediate node to the end too.
            path.append( n )

        for i in path:
            self.rename[i] = n
        return n
            
    def _checkEdge( self, a, b, tag ):
        if [a,b] in self.graph.edges:
            if 'tag' in self.graph[a][b]:
                if self.graph[a][b]['tag'] != tag:
                    raise MismatchedEdgeError( a, b, tag, self.graph[a][b]['tag'] )
    
    def addNode( self, n, tag = None ):
        n = self._followJoin( n )
        
        if tag is None:
            self.graph.add_node( n )
        else:
            if n not in self.graph.nodes: 
                self.graph.add_node( n, tag = tag )
            else:
                existing = self.graph.nodes[n]
                if 'tag' in existing:
                    if existing['tag'] != tag:
                        raise MismatchedVertexError( n, tag, existing['tag'] )
                else:
                    # Add it to a previously untagged node
                    self.graph.nodes[n]['tag'] = tag
            
    def addDirected( self, a, b, tag = None ):
        a = self._followJoin( a )
        b = self._followJoin( b )
        
        if self.undirected:
            self.undirected = False
            self.graph = self.graph.to_directed()
            # This breaks the connection betwen graph['rename'] and self.rename
            self.graph.graph['rename'] = self.rename

        if tag is None:
            self.graph.add_edge( a, b )
        else:
            self._checkEdge( a, b, tag ) 
            self.graph.add_edge( a, b, tag=tag )

    def addUndirected( self, a, b, tag = None ):
        a = self._followJoin( a )
        b = self._followJoin( b )

        if self.undirected:
            if tag is None:
                self.graph.add_edge( a, b )
            else:
                self._checkEdge( a, b, tag )
                self.graph.add_edge( a, b, tag=tag )
        else:
            if tag is None:
                self.graph.add_edge( a, b )
                self.graph.add_edge( b, a )
            else:
                self._checkEdge( a, b, tag )
                self._checkEdge( b, a, tag )
                self.graph.add_edge( a, b, tag=tag )
                self.graph.add_edge( b, a, tag=tag )
                

# From python 3 itertools recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def parseGraphString( inputString, quiet=False, joinAllowed=False ):
    try:
        p = graph.parseString( inputString )
    except ParseException as err:
        raise GraphParsingError( inputString, err )

    if ( joinAllowed is False ) and ( len( p['join']  ) > 0 ):
        raise MergeDisallowedError( p )
        
    ret = WorkingGraph( join=p['join'] )
    
    for element in p:
        if len( element ) == 1:            
            ret.addNode( element[0], element.get( 'tag', None ) )
        else:
            prev = element[0]
            tag = element.get( 'tag', None )
            for (direction, vertex) in grouper( element[1:], 2 ):
                if direction == "--":
                    ret.addUndirected( prev, vertex, tag )
                elif direction == "->":
                    ret.addDirected( prev, vertex, tag )
                elif direction == "<-":
                    ret.addDirected( vertex, prev, tag )
                else:
                    assert False, "Invalid direction slipped through parser"
                prev = vertex

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
            try:
                gg.start = parseGraphString( r, joinAllowed=False )
            except GraphParsingError as gpe:
                raise GrammarParsingError( l, r, "bad start graph", gpe )
            except MergeDisallowedError as mde:
                raise GrammarParsingError( l, r, "merge syntax not allowed in starting rule" )
            except MismatchedTagError as mte:
                raise GrammarParsingError( l, r, "inconsistent tags in start graph", mte )                        
        else:
            try:
                lg = parseGraphString( l, joinAllowed=False )
            except GraphParsingError as gpe:
                raise GrammarParsingError( l, r, "bad left-hand graph", gpe )
            except MergeDisallowedError as mde:
                raise GrammarParsingError( l, r, "merge syntax not allowed in left side of rule" )
            except MismatchedTagError as mte:
                raise GrammarParsingError( l, r, "inconsistent tags in left side of rule", mte )
                        
            if isinstance( r, list ):
                rgList = []
                for i in r:
                    try:
                        rg = parseGraphString( i, joinAllowed=True )
                        rgList.append( rg )
                    except GraphParsingError as gpe:
                        raise GrammarParsingError( l, i, "bad right-hand graph in choice", gpe )                        
                    except MismatchedTagError as mte:
                        raise GrammarParsingError( l, i, "bad right-hand graph in choice", mte )                        
                gg.addChoice( lg, rgList )
            else:
                try:
                    rg = parseGraphString( r, joinAllowed=True )
                    gg.addRule( lg, rg )
                except GraphParsingError as gpe:
                    raise GrammarParsingError( l, r, "bad right-hand graph", gpe )                        
                except MismatchedTagError as mte:
                    raise GrammarParsingError( l, r, "bad right-hand graph", mte )                        

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
    try:
        return _dispatchGrammarParse( ggJson )
    except GrammarParsingError as pe:
        pe.updateLineNumber( inputString )
        raise pe
        
def loadGraphGrammar( f, quiet=False ):
    # FIXME: handle parse error
    ggJson = json.load( f )
    return _dispatchGrammarParse( ggJson )



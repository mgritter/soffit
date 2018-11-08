"""Application of rule sets to graphs."""
#
#   soffit/application.py
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
from soffit.graph import MatchFinder, RuleApplication, graphIdentifiersToNumbers
import soffit.parse as parse
import soffit.display
import random
from functools import reduce
import time

class NoMatchException(Exception):
    def __init__( self ):
        self.message = "No match found in graph."

def makeAllDirected( *graphs ):
    """If any one of the input graphs is directed, make directed versions of all
    of the inputs and return them.  Otherwise, return the input unchanged."""
    someDirected = reduce( lambda x, y: x or y, map( nx.is_directed, graphs ) )
    if someDirected:
        return [ ( g.to_directed() if (not nx.is_directed( g )) else g )
                 for g in graphs ]
    else:
        return graphs

class Timing(object):
    def __init__( self ):
        self.keyCache = {}
        self.samples = {}
        
    def key( self, left, right ):
        k = self.keyCache.get( (left,right), None )
        if k is not None:
            return k

        from networkx.drawing.nx_agraph import to_agraph
        
        nk = ( to_agraph( left ).string().replace( "\n", " " ),
               to_agraph( right ).string().replace( "\n", " " ) )
        self.keyCache[(left,right)] = nk
        return nk
        
    def addSample( self, left, right, sec ):
        k = self.key( left, right )
        if k in self.samples:
            self.samples[k].append( sec )
        else:
            self.samples[k] = [ sec ]

    def report( self ):
        for ( k, v ) in self.samples.items():
            print( "******" )
            print( k[0] )
            print( k[1] )
            print( "Average:", sum( v ) / len( v ) )
            print( "Max:", max( v ) )
                
def chooseAndApply( grammar, graph, timing = None ):
    nRules = len( grammar.rules )
    # This is a little wasteful but simpler than removing rules
    # since they don't currently have an equality check.
    ruleAttemptOrder = random.sample( grammar.rules, nRules )
    
    for r in ruleAttemptOrder:
        left = r.leftSide()
        for right in r.rightSide():

            # Covert to directed on-demand
            # FIXME: do it ahead of time if any directed graphs exist in the rule set?
            (left, right, graph) = makeAllDirected( left, right, graph )

            start = time.time()
            finder = MatchFinder( graph )
            finder.leftSide( left )
            finder.rightSide( right )

            possibleMatches = finder.matches()
            end = time.time()
            if timing is not None:
                timing.addSample( left, right, end - start )
            if len( possibleMatches ) == 0:
                # Try next right side
                continue
            
            chosenMatch = random.choice( possibleMatches )
            print( chosenMatch )
            rule = RuleApplication( finder, chosenMatch )
            return rule.result()

    raise NoMatchException()
        
        
def applyRuleset( rulesetFilename, 
                  outputFile,
                  maxIterations = 100,
                  callback = None ):
    """Apply the graph grammar found in rulesetFilename, up to maxItertions times.
    Write the final SVG to outputFile.
    The callback function is called with (iteration, graph) at each step."""

    #timing = Timing()
    timing = None
    
    # FIXME: split the load and iteration loop into separate functions.    
    print( "Loading grammar from", rulesetFilename )
    # FIXME: catch file not found error
    with open( rulesetFilename, "r" ) as f:
        try:
            grammar = parse.loadGraphGrammar( f  )
        except parse.ParseError as pe:
            pe.prettyPrint()
            exit( 1 )
            
    g = graphIdentifiersToNumbers( grammar.start )

    if callback is not None:
        callback( 0, g )
    
    iteration = 1
    try:
        while iteration <= maxIterations:
            g = chooseAndApply( grammar, g, timing=timing )
            print( "Iteration {}: graph size {}".format( iteration,
                                                         len( g.nodes ) ) )
            if callback is not None:
                callback( iteration, g )
            iteration += 1
        print( "Stopping expansion after {} iterations".format( iteration - 1 ) )
    except NoMatchException:
        print( "No matching rule found at iteration {}".format( iteration ) )

    timing.report()
    
    print( "Writing SVG to", outputFile )
    soffit.display.drawSvg( g, outputFile )

if __name__ == "__main__":
    import sys
    maxIter = 100
    outputFile = "soffit.svg"
    if len( sys.argv ) > 2:
        outputFile = sys.argv[2]
    if len( sys.argv ) > 3:
        maxIter = int( sys.argv[3] )
    
    applyRuleset( sys.argv[1], outputFile, maxIter )


    

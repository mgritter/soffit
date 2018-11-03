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
import soffit.display as display
import random

class NoMatchException(Exception):
    def __init__( self ):
        self.message = "No match found in graph."

def chooseAndApply( grammar, graph ):
    nRules = len( grammar.rules )
    # This is a little wasteful but simpler than removing rules
    # since they don't currently have an equality check.
    ruleAttemptOrder = random.sample( grammar.rules, nRules )
    
    for r in ruleAttemptOrder:
        left = r.leftSide()
        for right in r.rightSide():
            finder = MatchFinder( graph )
            finder.leftSide( left )
            finder.rightSide( right )

            possibleMatches = finder.matches()
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
                  maxIterations = 100 ):
    print( "Loading grammar from", rulesetFilename )
    # FIXME: catch file not found error
    with open( rulesetFilename, "r" ) as f:
        try:
            grammar = parse.loadGraphGrammar( f  )
        except parse.ParseError as pe:
            pe.prettyPrint()
            exit( 1 )
            
    g = graphIdentifiersToNumbers( grammar.start )

    iteration = 1
    try:
        while iteration <= maxIterations:
            g = chooseAndApply( grammar, g )
            print( "Iteration {}: graph size {}".format( iteration,
                                                         len( g.nodes ) ) )
            iteration += 1
        print( "Stopping expansion after {} iterations".format( iteration - 1 ) )
    except NoMatchException:
        print( "No matching rule found at iteration {}".format( iteration ) )

    print( "Writing SVG to", outputFile )
    display.drawSvg( g, outputFile )

if __name__ == "__main__":
    import sys
    maxIter = 100
    outputFile = "soffit.svg"
    if len( sys.argv ) > 2:
        outputFile = sys.argv[2]
    if len( sys.argv ) > 3:
        maxIter = int( sys.argv[3] )
    
    applyRuleset( sys.argv[1], outputFile, maxIter )


    

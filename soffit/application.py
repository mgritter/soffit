"""Application of rule sets to graphs."""
#
#   soffit/application.py
#
#   Copyright 2018-2019 Mark Gritter
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
import re
import argparse

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

def to_dot( g ):
    from networkx.drawing.nx_agraph import to_agraph
    
    ag = to_agraph( g )
    try:
        del ag.graph_attr['join']
        del ag.graph_attr['rename']
    except KeyError:
        pass
    dotFormat = ag.string().replace( "\n", " " )
    return re.sub( r"\s\s+", " ", dotFormat ) 
    
class Timing(object):
    def __init__( self ):
        self.keyCache = {}
        self.samples = {}
        self.enumSamples = {}
        
    def key( self, left, right ):
        k = self.keyCache.get( (left,right), None )
        if k is not None:
            return k

        nk = ( to_dot( left ), to_dot( right ) )
        self.keyCache[(left,right)] = nk
        return nk
        
    def addSample( self, left, right, total, enum ):
        k = self.key( left, right )
        if k in self.samples:
            self.samples[k].append( total )
            self.enumSamples[k].append( enum )
        else:
            self.samples[k] = [ total ]
            self.enumSamples[k] = [ enum ]

    def report( self ):
        for ( k, v ) in self.samples.items():
            print( "******" )
            print( "Left:", k[0] )
            print( "Right:", k[1] )
            avg = sum( v ) / len( v )
            enumAvg = sum( self.enumSamples[k] ) / len( self.enumSamples[k] )
            print( "Mean: {:.3f} / {:3f}".format( enumAvg, avg ) )
            print( "Max: {:.3f}".format( max( v ) ) )
                
def chooseAndApply( grammar, graph, timing = None, verbose = False,
                    pick_first = False ):
    nRules = len( grammar.rules )
    # This is a little wasteful but simpler than removing rules
    # since they don't currently have an equality check.
    ruleAttemptOrder = random.sample( grammar.rules, nRules )

    rule_count = 0

    # Only convert the graph once!
    # FIXME: could we do it even less often than that, maybe carry over from
    # one interaction to the next?
    graph = nx.convert_node_labels_to_integers( graph, label_attribute="orig" )
    for n in graph:
        graph.node[n]['orig'] = n
    graph.graph['node_tag_cache'] = {}
    graph.graph['edge_tag_cache'] = {}

    for r in ruleAttemptOrder:
        left = r.leftSide()
        for right in r.rightSide():
            rule_count += 1
            
            # Covert to directed on-demand
            # FIXME: do it ahead of time if any directed graphs exist in the rule set?
            (left, right, graph) = makeAllDirected( left, right, graph )

            start = time.time()
            finder = MatchFinder( graph, already_labeled = True )
            if pick_first:
                finder.maxMatches = 1
            finder.leftSide( left )
            finder.rightSide( right )
            possibleMatches = finder.matches()
            end = time.time()

            if timing is not None:
                timing.addSample( left, right, end - start, 0 )
            if len( possibleMatches ) == 0:
                # Try next right side
                continue
            
            chosenMatch = random.choice( possibleMatches )
            rule = RuleApplication( finder, chosenMatch )
            return rule.result(), rule_count, len( possibleMatches ), chosenMatch

    raise NoMatchException()

class ApplicationState:
    """Apply a graph grammar to a rule.  Contains capabilities for profiling the
    graph grammar, logging output as it runs, and limiting the amount of runtime. (TBD)"""
    def __init__( self, initialGraph, grammar = None, callback = None ):
        """Specify the initial graph and (optionally) a starting grammar.
        The "callback" function will be called once per iteration with the
        iteration number and the current graph.
        """
        self.grammar = grammar
        self.graph = graphIdentifiersToNumbers( initialGraph )
        self.iteration = 0
        self.callback = callback
        self.verbose = True
        self.timing = None
        self.fast_mode = False
        
    def startProfile( self ):
        self.timing = Timing()
        self.verbose = True

    def reportProfile( self ):
        if self.timing is not None:
            self.timing.report()
        
    def changeGrammar( self, grammar ):
        self.grammar = grammar
        self.iteration = 0 # FIXME?
        
    def runSingleIter( self ):
        self.graph, rules_checked, matches_found, match = \
                chooseAndApply( self.grammar, self.graph,
                                timing=self.timing,
                                verbose=self.verbose,
                                pick_first=self.fast_mode )

        if self.verbose:
            print( "Iteration {:6} | {:6} nodes | {:4} attempts | {:4} matches | {} ".format(
                self.iteration,
                len( self.graph.nodes ),
                rules_checked,
                matches_found,
                match ) )            
        if self.callback is not None:
            self.callback( self.iteration, self.graph )
            
        self.iteration += 1
        
    def run( self, maxIterations ):
        # FIXME: double callback when we switch grammars?
        if self.callback is not None:
            self.callback( self.iteration, self.graph )

        try:
            while self.iteration <= maxIterations:
                self.runSingleIter()
            if self.verbose:
                print( "Stopping expansion after {} iterations".format( self.iteration - 1 ) )
            return True
        except NoMatchException:
            if self.verbose:
                print( "No matching rule found at iteration {}".format( self.iteration ) )
            return False

def loadGrammar( rulesetFilename, verbose=True ):
    if verbose:
        print( "Loading grammar from", rulesetFilename )
        
    # FIXME: catch file not found error
    with open( rulesetFilename, "r" ) as f:
        try:
            return parse.loadGraphGrammar( f  )
        except parse.ParseError as pe:
            pe.prettyPrint()
            exit( 1 )
    
def applyRuleset( rulesetFilename, 
                  outputFile,
                  maxIterations = 100,
                  callback = None ):
    """Apply the graph grammar found in rulesetFilename, up to maxItertions times.
    Write the final SVG to outputFile.
    The callback function is called with (iteration, graph) at each step."""

    grammar = loadGrammar( rulesetFilename )            
    app = ApplicationState( initialGraph=grammar.start,
                            grammar=grammar,
                            callback=callback )
    app.run( maxIterations=maxIterations )
    soffit.display.drawSvg( app.graph, outputFile )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "grammar", nargs="+", help="Soffit grammar file, may specify multiple to chain them together." )
    # TODO: allow time-based bounds?
    parser.add_argument( "-i", "--iterations",
                         type=int,
                         default=100,
                         help="Maximum nummber of iterations to run, default 100" )
    # TODO: allow multiple output!
    # TODO: respect file format (graphviz may do this automatically)88 
    parser.add_argument( "-o", "--output",
                         default="soffit.svg",
                         help="Output file to write, default soffit.svg" )
    parser.add_argument( "--profile",
                         help="Profile the graph grammar.",
                         action="store_true" )
    a = parser.parse_args()

    grammars = [ loadGrammar( fn ) for fn in a.grammar ]
    app = ApplicationState( initialGraph = grammars[0].start )

    for g in grammars:
        app.changeGrammar( g )
        if a.profile:
            app.startProfile()
        app.run( maxIterations = a.iterations )
        if a.profile:
            app.reportProfile()

    print( "Writing final graph to", a.output )
    soffit.display.drawSvg( app.graph, a.output )

if __name__ == "__main__":
    main()

    

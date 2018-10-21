"""Class definitions for graph grammars."""
#
#   soffit/grammar.py
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
import random

class DeterministicRule(object):
    def __init__( self, left, right ):
        self.left = left
        self.right = right

    def leftSide( self ):
        return self.left
    
    def rightSide( self ):
        return self.right
    
class RandomRule(object):
    def __init__( self, left, rightChoices ):
        self.left = left
        self.rightChoices = rightChoices

    def leftSide( self ):
        return self.left

    def rightSide( self ):
        return random.choice( self.rightChoices )
        
class GraphGrammar(object):
    def __init__( self ):
        self.rules = []

    def addRule( self, left, right ):
        """Add a rule to the grammar; left and right should be networkx
        graph objects or lists of graph objects.

        Corresponding node names between the two graphs will be used to 
        determine the changes requested by the rule."""
        self.rules.append( DeterministicRule( left, right ) )

    def addChoice( self, left, rightChoices ):
        """Add a rule to the grammar with multiple right-hand choices."""
        self.rules.append( RandomRule( left, rightChoices ) )

    

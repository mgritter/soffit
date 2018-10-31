"""Additional constraint helpers."""
#
#   soffit/constraint.py
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

from constraint import Constraint, Unassigned, Domain

class TupleConstraint(Constraint):
    """Provided a collection of tuples, verify that the variable values
    appear as a tuple (in the order specified for the variables.)."""
    
    def __init__( self, tupleList ):
        self.allowedSet = set( tuple( t ) for t in tupleList )
        # print( "AllowedSet:", self.allowedSet )
        if len( self.allowedSet ) > 0:
            someTuple = next( iter( self.allowedSet ) )
            self.nthSet = [ set( t[i] for t in self.allowedSet )
                            for i in range( len( someTuple ) ) ]
        else:
            self.nthSet = []
            
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        current = tuple( assignments.get( v, Unassigned ) for v in variables )
        if Unassigned in current:
            return True
        else:
            return current in self.allowedSet

    def preProcess(self, variables, domains, constraints, vconstraints):
        # If only a single variable allowed, variables must be equal to that.
        # If domain already chopped, then what?
        if len( self.allowedSet ) == 0:
            # Impossible
            for v in variables:
                domains[v] = Domain( [] )
                vcontraints[v].remove( (self,variables) )
                
            constraints.remove( (self,variables) )
            return
        elif len( self.allowedSet ) == 1:
            allowed = next( iter( self.allowedSet ) )
            for (v, val) in zip( variables, allowed ):
                if val in domains[v]:
                    domains[v] = Domain( [val] )
                else:
                    domains[v] = Domain( [] )
                vconstraints[v].remove( (self,variables) )

            constraints.remove( (self,variables) )
            return
        
        # If some variable is only allowed a subset of values in its domain,
        # then restrict to that subset.
        for (i,v) in enumerate( variables ):
            for val in domains[v][:]:
                if val not in self.nthSet[i]:
                    domains[v].remove( val )
        

class ConditionalConstraint(Constraint):
    """Apply a constraint to variables 1..n-1 only if variable 0 matches
    the given value."""
    def __init__( self, value, otherConstraint ):
        self.value = value
        self.otherConstraint = otherConstraint

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        current = [ assignments.get( v, Unassigned ) for v in variables ]
        if current[0] is Unassigned or current[0] != self.value:
            return True

        return self.otherConstraint( variables[1:], domains, assignments, forwardcheck )


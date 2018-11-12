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

    def insertTrees( self, a, b ):
        if a in self.forward:
            self.forward[a].add( b )
        else:
            self.forward[a] = set( [b] )

        if b in self.backward:
            self.backward[b].add( a )
        else:
            self.backward[b] = set( [a] )

    def __init__( self, tupleList ):
        self.allowedSet = set( tuple( t ) for t in tupleList )
        self.forward = {}
        self.backward = {}
        
        #print( "AllowedSet:", self.allowedSet )
        if len( self.allowedSet ) > 0:
            someTuple = next( iter( self.allowedSet ) )
            self.nthSet = [ set() for i in range( len( someTuple ) ) ]
            if len( someTuple ) == 2:
                for t in self.allowedSet:
                    self.nthSet[0].add( t[0] )
                    self.nthSet[1].add( t[1] )
                    self.insertTrees( t[0], t[1] )
            else:
                for t in self.allowedSet:
                    for (i,x) in enumerate( t ):
                        self.nthSet[i].add( x )

            #print( "Forward: ", self.forward )
            #print( "Backward: ", self.backward )
            #print( "nth: ", self.nthSet )
            
        else:
            self.nthSet = []

    def pairCheck( self, current, domain, whichMap ):
        domainValues = set( domain )
        restrictedValues = whichMap[ current ]
        #print( "domainValues", domainValues )
        #print( "restrictedValues", restrictedValues )
        for val in domainValues.difference( restrictedValues ):
            #print( "Hiding value", val )
            domain.hideValue( val )
            if not domain:
                return False
        return True
        
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        current = tuple( assignments.get( v, Unassigned ) for v in variables )
        if Unassigned not in current:
            return current in self.allowedSet
        
        if len( variables ) != 2:
            return True

        if current[0] is not Unassigned:
            if current[0] not in self.forward:
                return False                
            if forwardcheck:
                return self.pairCheck( current[0],
                                       domains[variables[1]],
                                       self.forward )
                    

        if current[1] is not Unassigned:
            if current[1] not in self.backward:
                return False
            
            if forwardcheck:
                return self.pairCheck( current[1],
                                       domains[variables[0]],
                                       self.backward )

        return True


    def preProcess(self, variables, domains, constraints, vconstraints):
        # If only a single variable allowed, variables must be equal to that.
        # If domain already chopped, then what?
        if len( self.allowedSet ) == 0:
            # Impossible
            for v in variables:
                domains[v] = Domain( [] )
                vconstraints[v].remove( (self,variables) )
                
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

class NonoverlappingSets(Constraint):
    """Provided set of variables A and B, ensure that variables in A
    do not share any values with variables in B."""
    
    def __init__( self, firstSet, secondSet ):
        self.firstSet = firstSet
        self.secondSet = secondSet

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        setA = set( assignments[v]
                    for v in self.firstSet
                    if v in assignments )
            
        for v in self.secondSet:
            if v in assignments:
                if assignments[v] in setA:
                    return False

        return True

    def preProcess(self, variables, domains, constraints, vconstraints):
        if len( self.firstSet ) == 0 or len( self.secondSet ) == 0:
            constraints.remove( (self, variables) )
            for v in variables:
                vconstraints[v].remove( (self, variables) )

class NonoverlappingUnorderedPairs(Constraint):
    """Provided sets A and B of pairs of variables, ensure that the
    corresponding pairs of values do not overlap."""
    def __init__( self, firstSet, secondSet ):
        self.firstSet = firstSet
        self.secondSet = secondSet

    def __call__(self, variables, domains, assignments, forwardcheck=False):
        setA = set( ( assignments[x], assignments[y] )
                    for (x,y) in self.firstSet
                    if x in assignments and y in assignments )
            
        for (x,y) in self.secondSet:
            if x in assignments and y in assignments:
                xv = assignments[x]
                yv = assignments[y]
                if (xv,yv) in setA or (yv,xv) in setA:
                    return False

        return True

    def preProcess(self, variables, domains, constraints, vconstraints):
        if len( self.firstSet ) == 0 or len( self.secondSet ) == 0:
            constraints.remove( (self, variables) )
            for v in variables:
                vconstraints[v].remove( (self, variables) )
    

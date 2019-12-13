"""Additional constraint helpers."""
#
#   soffit/constraint.py
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

from constraint import Constraint, Unassigned, Domain

# These two Constraint implementations are much, much slower than using
# TupleConstraint. I don't understand why.
# Profiling shows a lot of hideValue calls by the Edge constraint.

class NodeTagConstraint(Constraint):
    """Given a graph and a tag, make sure any variables identify a node
    with matching tag. This seems more efficient than enumerating all the 
    nodes to find one up front, at least in some cases."""
    def __init__( self, graph, tag ):
        self.graph = graph
        self.tag = tag
        self.mismatch_cache = set()
            
    def preProcess(self, variables, domains, constraints, vconstraints):
        if 'node_tag_cache' not in self.graph.graph:
            return
        
        cache = self.graph.graph['node_tag_cache']
        if self.tag not in cache:
            nodes = []
            for n,t in self.graph.nodes( data="tag" ):
                if t == self.tag:
                    nodes.append( n )
            cache[self.tag] = nodes
        else:
            nodes = cache[self.tag]
            
        for v in variables:
            domains[v] = Domain( nodes )
        
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        current = [ (v,assignments.get( v, Unassigned )) for v in variables ]

        for v,n in current:
            if n is not Unassigned:
                if n not in self.graph.nodes:
                    self.mismatch_cache.add( n )
                    return False
                if self.graph.nodes[n].get( 'tag', None ) != self.tag:
                    self.mismatch_cache.add( n )
                    return False
            elif forwardcheck:
                domainValues = set( domains[v] )
                for x in self.mismatch_cache.intersection( domainValues ):
                    domains[v].hideValue( x )
                    
        return True
    
class EdgeTagConstraint(Constraint):
    """Given a graph and a tag, make sure any pairs of variables identify an 
    edge with matching tag."""
    def __init__( self, graph, tag ):
        self.graph = graph
        self.tag = tag

    def preProcess(self, variables, domains, constraints, vconstraints):
        if 'edge_tag_cache' not in self.graph.graph:
            return
        
        cache = self.graph.graph['edge_tag_cache']
        if self.tag not in cache:
            edges = []
            e_0 = set()
            e_1 = set()
            for i,j,t in self.graph.edges( data="tag" ):
                if t == self.tag:
                    e_0.add( i )
                    e_1.add( j )
                    edges.append( (i,j) )
            cache[self.tag] = edges
        else:
            # FIXME: would it be better to switch to representing edges as
            # edge variables, instead of a pair of node variables?
            edges = cache[self.tag]
            e_0 = set( e[0] for e in edges )
            e_1 = set( e[1] for e in edges )

        vb = iter( variables )
        for i, j in zip( vb, vb ):
            if self.graph.is_directed():
                domains[i] = Domain( e_0 )
                domains[j] = Domain( e_1 )
            else:
                all_nodes = e_0.union( e_1 )
                domains[i] = Domain( all_nodes )
                domains[j] = Domain( all_nodes )
                

    def edge_view( self, i, j ):
        if self.graph.is_directed():
            if i is Unassigned:
                for (i2,j2,t2) in self.graph.in_edges( nbunch=[j], data='tag' ):
                    if t2 == self.tag:
                        yield (i2,j2)
            elif j is Unassigned:
                for (i2,j2,t2) in self.graph.out_edges( nbunch=[i], data='tag' ):
                    if t2 == self.tag:
                        yield (i2,j2)
            else:
                assert False
        else:
            if i is Unassigned:
                for (i2,j2,t2) in self.graph.edges( nbunch=[j], data='tag' ):
                    if t2 == self.tag:
                        if j2 == j:
                            yield (i2,j2)
                        else:
                            yield (j2,i2)
            elif j is Unassigned:
                for (i2,j2,t2) in self.graph.edges( nbunch=[i], data='tag' ):
                    if t2 == self.tag:
                        if i2 == i:
                            yield (i2,j2)
                        else:
                            yield (j2,i2)
            else:
                assert False
            
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        assert len(variables) % 2 == 0

        current = iter( (v, assignments.get( v, Unassigned ))
                        for v in variables )
        
        for (v_i,i),(v_j,j) in zip( current, current ):
            if i is not Unassigned and j is not Unassigned:
                if (i,j) not in self.graph.edges:
                    return False
                if self.graph.edges[(i,j)].get( 'tag', None ) != self.tag:
                    return False
            else:
                if i is Unassigned:
                    prev_i = set( domains[v_i] )
                    allowed_i = set()                    
                    for (i2,j2) in self.edge_view( i, j ):
                        allowed_i.add( i2 )
                        if not forwardcheck:
                            return True

                    if len( allowed_i ) == 0:
                        return False
                    
                    if forwardcheck:
                        for i2 in prev_i.difference( allowed_i ):
                            domains[v_i].hideValue( i2 )
                        if not domains[v_i]:
                            return False
                        
                if j is Unassigned:
                    prev_j = set( domains[v_j] )
                    allowed_j = set()
                    for (i2,j2) in self.edge_view( i, j ):
                        allowed_j.add( j2 )
                        if not forwardcheck:
                            return True
                            
                    if len( allowed_j ) == 0:
                        return False
                    
                    if forwardcheck:
                        for j2 in prev_j.difference( allowed_j ):
                            domains[v_j].hideValue( j2 )
                        if not domains[v_j]:
                            return False
                            
        return True
    
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

class ConditionalTupleConstraint(Constraint):
    """Apply a tuple constraint to variables 1..n-1 only if variable 0 matches
    the given value.  The inputs are tuples (a0, a1, a2, ...) and if 
    v0 == a0 then it must be the case that v1==a1, v2==a2, v3==a3 for some 
    tuple.  If v0 doesn't match any a0, the constraint is met."""
    def __init__( self, tupleSet ):
        self.byValue = {}
        for t in tupleSet:
            first = t[0]
            rest = tuple( t[1:] )
            if first in self.byValue:
                self.byValue[first].add( rest )
            else:
                self.byValue[first] = set( [ rest ] )

    def isCompatible( self, currentValues, allowedValues ):
        for (c,a) in zip( currentValues, allowedValues ):
            if c is not Unassigned and c != a:
                return False
        return True
        
    def possibleFirstValue( self, first, currentValues ):
        if first not in self.byValue:
            # Always allowable
            return True

        # TODO: could we do forward checking on the remaining values by
        # seeing if there are elements which *never* appear?  The problem
        # is that the first case could open things up a lot and make all our
        # work moot.
        for allowed in self.byValue[first]:
            if self.isCompatible( currentValues, allowed ):
                return True
        
    def __call__(self, variables, domains, assignments, forwardcheck=False):
        # print( "Call", assignments, domains, bool(forwardcheck) )
        current = [ assignments.get( v, Unassigned ) for v in variables ]
        # print( "Current", current )
        if current[0] is Unassigned:
            # We don't know which value to look up, but if we can rule it
            # out from the other assignments, we can do some forward checking.
            if not forwardcheck:
                return True
            
            domain = domains[variables[0]]
            for v in list( domain ):
                if not self.possibleFirstValue( v, current[1:] ):
                    domain.hideValue( v )
                    if not domain:
                        return False
                    
            return True

        if current[0] not in self.byValue:
            # Unrestricted
            return True
        
        # OK, we can narrow down to just a subset of the tuples now
        allowedTuples = self.byValue[current[0]]

        if Unassigned not in current:
            return tuple( current[1:] ) in allowedTuples
        
        compatibleTuples = [
            allowed for allowed in allowedTuples
            if self.isCompatible( current[1:], allowed )
        ]
        # print( "compatibleTuples", compatibleTuples ) 

        if len( compatibleTuples ) == 0:
            return False

        if not forwardcheck:
            return True

        for i, variable in enumerate( variables[1:] ):
            # I think we're allowed to do this only for unassigned variables,
            # I got a missing solution otherwise.
            if variable in assignments:
                continue
            
            domain = domains[variable]
            ithValues = set( ct[i] for ct in compatibleTuples )
            # print( "ithValues",ithValues )
            for v in list( domain ):
                if v not in ithValues:
                    # print( "Hide", v, "from", variable )
                    domain.hideValue( v )
                    if not domain:
                        # print( "Domain emptied!" )
                        return False
                    
        return True
        
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
    

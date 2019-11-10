minValue = 0
maxValue = 20

def genShiftRules():
    for a in range( minValue, maxValue + 1 ):
        for b in range( minValue, maxValue + 1 ):
            clauses = []
            lhs = 'A->B[+]; A[{0}]; B[{1}];'.format( a, b )
            if a > minValue and b < maxValue:
                clauses.append( 'A->B [+]; A[{0}]; B[{1}]'.format( a-1, b+1 ) )

            if a < maxValue and b > minValue:
                clauses.append( 'A->B [+]; A[{0}]; B[{1}]'.format( a+1, b-1 ) )

            if a < maxValue and b == 0:
                clauses.append( 'A->B [-]; A[{0}]; B[{1}]'.format( a+1, 1 ) )                

            if len( clauses ) > 0:
                print( '"{}" : [ "{}" ],'.format( lhs,
                                                 '", "'.join( clauses ) ) )

            clauses = []
            lhs = 'A->B[-]; A[{0}]; B[{1}];'.format( a, b )
            if a < maxValue and b < maxValue:
                clauses.append( 'A->B [-]; A[{0}]; B[{1}]'.format( a+1, b+1 ) )

            if a > minValue and b > minValue:
                clauses.append( 'A->B [-]; A[{0}]; B[{1}]'.format( a-1, b-1 ) )

            if a > minValue and b == 0:
                clauses.append( 'A->B [+]; A[{0}]; B[{1}]'.format( a-1, 1 ) )
            
            if len( clauses ) > 0:
                print( '"{}" : [ "{}" ],'.format( lhs,
                                                 '", "'.join( clauses ) ) )

def genExpandRules():
    for a in range( minValue, maxValue + 1 ):
        for b in range( minValue, maxValue + 1 ):
            clauses = []
            lhs = 'A->B[+]; A--X; B--Y; X--Y; A[{0}]; B[{1}]; X[x]; Y[x]'.format( a, b )
            clauses.append( 'A--B; A->X[+]; Y->B[+]; X->Y[+]; A[{0}]; B[{1}]; X[0]; Y[0]'.format( a, b ) )
            
            if len( clauses ) > 0:
                print( '"{}" : [ "{}" ],'.format( lhs,
                                                  '", "'.join( clauses ) ) )
                

if __name__ == "__main__":
    genShiftRules()
    genExpandRules()

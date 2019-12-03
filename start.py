if __name__ == "__main__":
    import sys
    from soffit.application import applyRuleset
    
    maxIter = 100
    outputFile = "soffit.svg"
    if len( sys.argv ) > 2:
        outputFile = sys.argv[2]
    if len( sys.argv ) > 3:
        maxIter = int( sys.argv[3] )
    
    applyRuleset( sys.argv[1], outputFile, maxIter )



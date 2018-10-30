"""Workarounds for bugs discovered in 3rd party libraries."""
#
#   soffit/hacks.py
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

from ortools.sat.python import cp_model
from ortools.sat.python import cp_model_helper
from ortools.sat.python.cp_model import Constraint

def cautiousSearch( solver, model, callback ):
    """Work around issue https://github.com/google/or-tools/issues/907
    SearchForAllSolutions seems to crash on an unsatisfiable model,
    but Search does not.  So use that first."""
    
    status = solver.Solve( model )
    if status != cp_model.INFEASIBLE:
        solver.SearchForAllSolutions( model, callback )

def AddAllowedAssignments(model, variables, tuples_list):
    """Work around issue https://github.com/google/or-tools/issues/909
    A version of AddAllowedAssignments that correctly returns
    the Constraint object."""
    
    if not variables:
        raise ValueError('AddAllowedAssignments expects a non empty variables '
                             'array')

    ct = Constraint(model._CpModel__model.constraints)
    model_ct = model._CpModel__model.constraints[ct.Index()]
    model_ct.table.vars.extend([model.GetOrMakeIndex(x) for x in variables])
    arity = len(variables)
    for t in tuples_list:
        if len(t) != arity:
            raise TypeError('Tuple ' + str(t) + ' has the wrong arity')
        for v in t:
            cp_model_helper.AssertIsInt64(v)
        model_ct.table.values.extend(t)
    return ct

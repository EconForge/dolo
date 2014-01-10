import numpy
from numpy import linspace, zeros, atleast_2d



def find_steady_state(model, e=None, force_values=None, return_jacobian=False):
    '''
    Finds the steady state corresponding to exogenous shocks :math:`e`.

    :param model: an "fg" model.
    :param e: a vector with the value for the exogenous shocks.
    :param force_values: (optional) a vector where finite values override the equilibrium conditions. For instance a vector :math:`[0,nan,nan]` would impose that the first state must be equal to 0, while the two next ones, will be determined by the model equations. This is useful, when the deterministic model has a unit root.
    :return: a list containing a vector for the steady-states and the corresponding steady controls.
    '''

    s0 = model.calibration['states']
    x0 = model.calibration['controls']
    p = model.calibration['parameters']
    z = numpy.concatenate([s0, x0])

    if e is None:
        e = numpy.zeros( len(model.symbols['shocks']) )
    else:
        e = e.ravel()

    if force_values is not None:
        if isinstance(force_values, (list, tuple)):
            inds =  numpy.where( numpy.isfinite( force_values ) )[0]
            vals = force_values[inds]
        elif isinstance(force_values, dict):
            inds = [model.symbols['states'].index(k) for k in force_values.keys()]
            vals = force_values.values()

    def fobj(z):
        s = z[:len(s0)]
        x = z[len(s0):]
        S = model.functions['transition'](s,x,e,p)
        r = model.functions['arbitrage'](s,x,s,x,p)
        res = numpy.concatenate([S-s, r,  ])
        if force_values is not None:
            add = S[inds]-vals
            res = numpy.concatenate([res, add])
        return res

    from dolo.numeric.solver import MyJacobian
    jac = MyJacobian(fobj)( z )
    if return_jacobian:
        return jac
   

    rank = numpy.linalg.matrix_rank(jac)
    if rank < len(z):
        import warnings
        warnings.warn("There are {} equilibrium variables to find, but the jacobian matrix is only of rank {}. The solution is indeterminate.".format(len(z),rank))

    from scipy.optimize import root
    sol = root(fobj, z, method='lm')
    steady_state = sol.x
   
    return [steady_state[:len(s0)], steady_state[len(s0):]]
    
if __name__ == '__main__':
   
    from dolo import *
    from numpy import nan

    from dolo.algos.steady_state import find_steady_state

    model = yaml_import("examples/global_models/open_economy.yaml")
    
    
    ss = find_steady_state( model )

    print("Steady-state variables")
    print("states: {}".format(ss[0]))
    print("controls: {}".format(ss[1]))
    
    jac = find_steady_state(model, return_jacobian=True)

    rank = numpy.linalg.matrix_rank(jac)

    
    sol2 = find_steady_state(model, force_values=[0.3,nan] )  # -> returns steady-state, using calibrated values as starting point
    sol3 = find_steady_state(model, force_values={'W_1':0.3} )  # -> returns steady-state, using calibrated values as starting point

    print(sol2)
    print(sol3)
    
#    steady_state( model, e ) # -> sets exogenous values for shocks
    
#    steady_state( model, {'e_a':1, 'e':9}, {'k':[8,9]})
    
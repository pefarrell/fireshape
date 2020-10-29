from firedrake import *
from fireshape import *
import numpy as np
import ROL

# goal: update the mesh coordinates of a periodic mesh
# so that a function defined on the mesh becomes a given one
mesh = PeriodicSquareMesh(30, 30, 1)
Q = PeriodicControlSpace(mesh)  #how can we fix the boundary?
inner = LaplaceInnerProduct(Q)
q = ControlVector(Q, inner)

# save shape evolution in file domain.pvd
V = FunctionSpace(Q.mesh_m, "DG", 0)
sigma = Function(V)
x, y = SpatialCoordinate(Q.mesh_m)
perturbation = 0.1*sin(x*np.pi)*sin(y*np.pi)**2
sigma.interpolate(sin(y*np.pi)*(cos(2*np.pi*x*(1+perturbation))))
f = cos(2*np.pi*x)*sin(y*np.pi)

class LevelsetFct(ShapeObjective):
    def __init__(self, sigma, f, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sigma = sigma  #initial
        self.f = f          #target
        Vdet = FunctionSpace(Q.mesh_r, "DG", 0)
        self.detDT = Function(Vdet)

    def value_form(self):
        # volume integral
        self.detDT.interpolate(det(grad(self.Q.T)))
        if min(self.detDT.vector()) > 0.05:
            return (self.sigma - self.f)**2 * dx(metadata={"quadrature_degree":1})
        else:
            return np.nan*(self.sigma - self.f)**2 * dx(metadata={"quadrature_degree":1})

CB = File("domain.pvd")
J = LevelsetFct(sigma, f, Q, cb=lambda: CB.write(sigma))

# ROL parameters
params_dict = {'Step': {'Type': 'Trust Region'},
'General': {'Secant': {'Type': 'Limited-Memory BFGS',
                       'Maximum Storage': 25}},
'Status Test': {'Gradient Tolerance': 1e-4,
                'Step Tolerance': 1e-4,
                'Iteration Limit': 30}}

params = ROL.ParameterList(params_dict, "Parameters")
problem = ROL.OptimizationProblem(J, q)
solver = ROL.OptimizationSolver(problem, params)
solver.solve()

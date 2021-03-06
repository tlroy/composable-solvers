# flake8: noqa: F403
from __future__ import absolute_import
from argparse import ArgumentParser
from firedrake import *
from firedrake.utils import cached_property
import numpy

from . import baseproblem


class Problem(baseproblem.Problem):

    name = "Poisson"

    @property
    def random(self):
        return self.args.random

    parameter_names = ("hypre", "schwarz_rich")

    @property
    def hypre(self):
        return {"snes_type": "ksponly",
                "ksp_type": "cg",
                "ksp_rtol": 1e-8,
                "ksp_monitor": True,
                "ksp_view": True,
                "pc_type": "hypre",
                "pc_hypre_type": "boomeramg",
                "pc_hypre_boomeramg_no_CF": True,
                "pc_hypre_boomeramg_coarsen_type": "hmis",
                "pc_hypre_boomeramg_interp_type": "ext+i",
                "pc_hypre_boomeramg_P_max": 4,
                "pc_hypre_boomeramg_agg_nl": 1}

    @property
    def schwarz_rich(self):
        return {"snes_type": "ksponly",
                "ksp_type": "cg",
                "ksp_view": True,
                "ksp_rtol": 1e-8,
                "ksp_monitor": True,
                "mat_type": "matfree",
                "pc_type": "python",
                "pc_python_type": "ssc.SSC",
                "ssc_pc_composite_type": "additive",
                # Patch config
                   "ssc_sub_0_pc_patch_save_operators": True,
                "ssc_sub_0_pc_patch_sub_mat_type": "seqaij",
                "ssc_sub_0_sub_ksp_type": "preonly",
                "ssc_sub_0_sub_pc_type": "lu",
                # Low-order config
                   "ssc_sub_1_lo_pc_type": "telescope",
                "ssc_sub_1_lo_pc_telescope_reduction_factor": 6,
                "ssc_sub_1_lo_telescope_ksp_type": "preonly",
                "ssc_sub_1_lo_telescope_pc_type": "gamg"}

    @staticmethod
    def argparser():
        parser = ArgumentParser(description="""Set options for Poisson problem""", add_help=False)

        parser.add_argument("--degree", action="store", default=1,
                            help="Polynomial degree",
                            type=int)

        parser.add_argument("--size", action="store",  default=10,
                            help="Number of cells in each spatial direction",
                            type=int)

        parser.add_argument("--dimension", action="store", default=2, choices=[2, 3],
                            help="Spatial dimension of problem",
                            type=int)

        parser.add_argument("--random", action="store_true",
                            help="Use a random right hand side (otherwise use one with an exact solution)")

        parser.add_argument("--output_solution", action="store_true",
                            help="Output the solution for visualisation in paraview")

        parser.add_argument("--help", action="store_true",
                            help="Show help")
        return parser

    @cached_property
    def function_space(self):
        return FunctionSpace(self.mesh, "CG", self.degree)

    @cached_property
    def forcing(self):
        V = self.function_space
        if self.random:
            f = Function(V)
            numpy.random.seed(f.comm.rank + 101)
            f.dat.data[:] = numpy.random.exponential(scale=10, size=f.dat.data_ro.shape)
        else:
            f = Constant(1)

        return f

    @cached_property
    def F(self):
        V = self.function_space
        v = TestFunction(V)
        return inner(grad(self.u), grad(v))*dx - self.forcing*v*dx

    @cached_property
    def bcs(self):
        return DirichletBC(self.function_space, 0, "on_boundary")

    @cached_property
    def output_fields(self):
        return (self.u, )

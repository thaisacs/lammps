# ----------------------------------------------------------------------
#   LAMMPS - Large-scale Atomic/Molecular Massively Parallel Simulator
#   http://lammps.sandia.gov, Sandia National Laboratories
#   Steve Plimpton, sjplimp@sandia.gov
#
#   Copyright (2003) Sandia Corporation.  Under the terms of Contract
#   DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government retains
#   certain rights in this software.  This software is distributed under
#   the GNU General Public License.
#
#   See the README file in the top-level LAMMPS directory.
# -------------------------------------------------------------------------

# ----------------------------------------------------------------------
#   Contributing author: Nicholas Lubbers (LANL)
# -------------------------------------------------------------------------

import numpy as np
import torch

def calc_n_params(model):
    return sum(p.nelement() for p in model.parameters())

class TorchWrapper(torch.nn.Module):
    def __init__(self, model,n_descriptors,n_elements,n_params=None):
        super().__init__()
        self.model = model
        self.model.to(self.dtype)
        if n_params is None:
            n_params = calc_n_params(model)
        self.n_params = n_params
        self.n_descriptors = n_descriptors
        self.n_elements = n_elements

    def __call__(self, elems, bispectrum, beta, energy):

        bispectrum = torch.from_numpy(bispectrum).to(self.dtype).requires_grad_(True)
        elems = torch.from_numpy(elems).to(torch.long) - 1

        with torch.autograd.enable_grad():

            energy_nn = self.model(bispectrum, elems)
            if energy_nn.ndim > 1:
                energy_nn = energy_nn.flatten()

            beta_nn = torch.autograd.grad(energy_nn.sum(), bispectrum)[0]

        beta[:] = beta_nn.detach().cpu().numpy().astype(np.float64)
        energy[:] = energy_nn.detach().cpu().numpy().astype(np.float64)

class TorchWrapper32(TorchWrapper):
    dtype = torch.float32

class TorchWrapper64(TorchWrapper):
    dtype = torch.float64

class IgnoreElems(torch.nn.Module):
    def __init__(self,subnet):
        super().__init__()
        self.subnet = subnet

    def forward(self,bispectrum,elems):
        return self.subnet(bispectrum)

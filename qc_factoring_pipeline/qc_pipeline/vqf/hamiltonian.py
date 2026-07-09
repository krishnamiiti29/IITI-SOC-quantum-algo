"""
Variational Quantum Factoring (VQF): scales better to real N than QPE.

QPE needs deep controlled-U^(2^k) circuits that blow up for real N (up to
254 in this pipeline). VQF instead casts "does p*q == N?" as a QUBO/Ising
cost function and searches for low-cost bitstrings with QAOA -- shallower,
more NISQ-friendly.

Requires: pip install sympy dimod

Extracted from the notebook's "Variational Quantum Factoring (VQF)" cell.
"""

import dimod
import numpy as np
import sympy as sp
from qiskit.quantum_info import SparsePauliOp


def build_vqf_hamiltonian(N, strength=50.0):
    """
    Cost Hamiltonian (SparsePauliOp) whose ground state encodes a
    nontrivial ODD factor pair of N.

    Returns:
        (hamiltonian, var_to_qubit, p_syms, q_syms, k), or None if N is
        even (2 is then a trivial factor -- no quantum step needed) or too
        small to have any free bits to search over.
    """
    if N % 2 == 0:
        return None

    k = int(np.ceil(np.log2(N)))
    p_syms = [sp.Symbol(f"p{i}") for i in range(k)]
    q_syms = [sp.Symbol(f"q{i}") for i in range(k)]

    # LSB fixed to 1 (odd factors), MSB fixed to 1 (both assumed k-bit numbers)
    p_expr = 1 + sum(p_syms[i] * (2 ** i) for i in range(1, k - 1)) + 2 ** (k - 1)
    q_expr = 1 + sum(q_syms[i] * (2 ** i) for i in range(1, k - 1)) + 2 ** (k - 1)

    free_vars = p_syms[1:k - 1] + q_syms[1:k - 1]
    if not free_vars:
        return None

    cost = sp.expand((sp.expand(p_expr * q_expr) - N) ** 2)
    changed = True
    while changed:
        changed = False
        for v in free_vars:
            reduced = sp.expand(cost.subs(v ** 2, v))
            if reduced != cost:
                cost = reduced
                changed = True

    cost_poly = sp.Poly(cost, *free_vars)
    poly_dict = {}
    for monom, coeff in cost_poly.terms():
        var_tuple = tuple(
            str(free_vars[i]) for i, power in enumerate(monom) for _ in range(power)
        )
        poly_dict[var_tuple] = poly_dict.get(var_tuple, 0.0) + float(coeff)

    bqm = dimod.make_quadratic(poly_dict, strength, vartype=dimod.BINARY)
    h, J, offset = bqm.to_ising()

    variables = sorted(bqm.variables, key=str)
    var_to_qubit = {v: i for i, v in enumerate(variables)}
    n_qubits = len(variables)

    pauli_list = []
    for v, bias in h.items():
        if bias == 0:
            continue
        label = ["I"] * n_qubits
        label[var_to_qubit[v]] = "Z"
        pauli_list.append(("".join(label), bias))
    for (u, v), bias in J.items():
        if bias == 0:
            continue
        label = ["I"] * n_qubits
        label[var_to_qubit[u]] = "Z"
        label[var_to_qubit[v]] = "Z"
        pauli_list.append(("".join(label), bias))

    hamiltonian = SparsePauliOp.from_list(pauli_list)
    print(
        f"VQF for N={N}: {n_qubits} qubits "
        f"({len(free_vars)} original + {n_qubits - len(free_vars)} auxiliary from quadratization)"
    )
    return hamiltonian, var_to_qubit, p_syms, q_syms, k

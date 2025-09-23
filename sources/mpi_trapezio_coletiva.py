# mpi_trapezio_coletiva.py
from mpi4py import MPI
import math

def f(x: float) -> float:
    return math.exp(x)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

a, b = 0.0, 1.0
n = 100_000_000
h = (b - a) / n

# rank 0 mede tempo e adiciona 1/2*(f(a)+f(b))
local_sum = 0.0
if rank == 0:
    t0 = MPI.Wtime()
    local_sum += 0.5 * (f(a) + f(b))

# pontos internos intercalados por rank: i = rank+1, rank+1+size, ...
i = rank + 1
while i < n:
    x = a + i * h
    local_sum += f(x)
    i += size

local_integral = local_sum * h

# Redução coletiva (soma) para o processo 0
total = comm.reduce(local_integral, op=MPI.SUM, root=0)
# (alternativa: total = comm.allreduce(local_integral, op=MPI.SUM)  # todos recebem)

if rank == 0:
    t1 = MPI.Wtime()
    print(f"Foram gastos {t1 - t0:3.1f} segundos")
    print(f"Com n = {n} trapezoides, a estimativa")
    print(f"da integral de {a:.6f} até {b:.6f} = {total:.12f}")

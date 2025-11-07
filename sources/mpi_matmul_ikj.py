# mpi_matmul_ikj.py
# Multiplicação de matrizes NxN em paralelo com MPI (scatter linhas de A)
# Execução:
# mpiexec -n 2 python3  mpi_matmul_ikj.py
# C[0,0] = 1000
# Tempo de multiplicacao (rank 0 mediu): 387.464 s
#   mpiexec -n 4 python mpi_matmul_ikj.py  (altere N no código se quiser)
# mpiexec -n 4 python3  mpi_matmul_ikj.py
# C[0,0] = 1000
# Tempo de multiplicacao (rank 0 mediu): 270.732 s
# mpiexec -n 8 python3  mpi_matmul_ikj.py
# C[0,0] = 1000
# Tempo de multiplicacao (rank 0 mediu): 184.815 s
# Requer: mpi4py instalado e um MPI (ex.: Open MPI)

from mpi4py import MPI
import numpy as np
import sys
import time

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# tamanho da matriz
N = 1000   # cuidado com N muito grande se seu nó for pequeno

# rank 0 cria as matrizes
if rank == 0:
    A = np.ones((N, N), dtype=np.int32)
    B = np.ones((N, N), dtype=np.int32)
else:
    A = None
    B = np.empty((N, N), dtype=np.int32)  # vai receber o broadcast

# todo mundo precisa saber quantas linhas vai receber
# vamos supor N % size == 0 para simplificar
if N % size != 0:
    if rank == 0:
        print("Para simplicidade, use N múltiplo do número de processos.")
    MPI.Finalize()
    sys.exit(0)

rows_per_rank = N // size

# cada processo recebe um bloco contíguo de linhas de A
local_A = np.empty((rows_per_rank, N), dtype=np.int32)

# dissemina B inteira para todos
comm.Bcast(B, root=0)

# espalha A por linhas
comm.Scatter([A, rows_per_rank * N, MPI.INT],  # sendbuf (no root)
             [local_A, rows_per_rank * N, MPI.INT],  # recvbuf (todos)
             root=0)

# agora cada processo faz: local_C = local_A @ B
# mas usando o mesmo padrão i-k-j do seu C++
local_C = np.zeros((rows_per_rank, N), dtype=np.int32)

t0 = time.perf_counter()

for i in range(rows_per_rank):
    for k in range(N):
        aik = local_A[i, k]
        # acessar linha k de B
        for j in range(N):
            local_C[i, j] += aik * B[k, j]

t1 = time.perf_counter()

# junta tudo no rank 0
if rank == 0:
    C = np.empty((N, N), dtype=np.int32)
else:
    C = None

comm.Gather([local_C, rows_per_rank * N, MPI.INT],
            [C,       rows_per_rank * N, MPI.INT],
            root=0)

# rank 0 confere e mostra tempo
if rank == 0:
    print("C[0,0] =", C[0, 0])   # deve dar N (soma de N produtos 1*1)
    print(f"Tempo de multiplicacao (rank 0 mediu): {t1 - t0:0.3f} s")

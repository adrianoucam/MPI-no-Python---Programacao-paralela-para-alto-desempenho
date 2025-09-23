# mpi_maxloc_criancas.py
# Emula MPI_MAXLOC:
# 1) Allreduce(MAX) encontra o maior valor por posição.
# 2) Reduce(MIN) encontra o menor rank que atingiu esse maior valor.

from mpi4py import MPI
import numpy as np

TAM = 10
ROOT = 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Vetor de entrada: 0.0, 1.0, ..., 9.0
    vetor_entrada = np.arange(TAM, dtype=np.float64)

    # Crianças com rank PAR colocam 50.0 na posição igual ao seu rank (se couber no vetor)
    if rank % 2 == 0 and rank < TAM:
        vetor_entrada[rank] = 50.0

    # 1) MAX por posição entre todos os processos
    max_global = np.empty(TAM, dtype=np.float64)
    comm.Allreduce(vetor_entrada, max_global, op=MPI.MAX)

    # 2) Entre os que têm o valor máximo naquela posição, escolher o menor rank
    #    Quem não tem o máximo, manda "infinito" (um número bem grande).
    INF = np.int32(2**31 - 1)
    candidatos = np.full(TAM, INF, dtype=np.int32)
    mask = (vetor_entrada == max_global)   # True onde este processo atingiu o máximo
    candidatos[mask] = np.int32(rank)

    # Reduce (MIN) para o ROOT descobrir o menor rank que bateu o máximo em cada posição
    ranks_max = None
    if rank == ROOT:
        ranks_max = np.empty(TAM, dtype=np.int32)
        comm.Reduce(candidatos, ranks_max, op=MPI.MIN, root=ROOT)
    else:
        comm.Reduce(candidatos, None, op=MPI.MIN, root=ROOT)

    # ROOT imprime resultado por posição
    if rank == ROOT:
        for i in range(TAM):
            valor = max_global[i]
            proc  = int(ranks_max[i])
            print(f"Posicao {i:2d}: Resultado = {valor:4.1f}  Processo = {proc}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

# mpi_scatter_criancas.py
# - O líder (rank 0) cria um vetor de 0 a (TAM_VET*size-1).
# - Scatter divide esse vetor em blocos de TAM_VET e entrega 1 bloco para cada rank.
# - Cada processo imprime seu pacotinho recebido.

from mpi4py import MPI
import numpy as np

TAM_VET = 10
ROOT = 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # No líder: vetor grandão com size * TAM_VET elementos (0, 1, 2, ..., N-1)
    if rank == ROOT:
        vet_envia = np.arange(size * TAM_VET, dtype=np.int32)
    else:
        vet_envia = None  # nos outros, não há buffer de envio

    # Em todos: buffer para receber exatamente TAM_VET inteiros
    vet_recebe = np.empty(TAM_VET, dtype=np.int32)

    # Scatter no modo "buffer": eficiente e igual ao C (sem pickling)
    comm.Scatter(
        [vet_envia, TAM_VET, MPI.INT] if rank == ROOT else None,
        [vet_recebe, TAM_VET, MPI.INT],
        root=ROOT,
    )

    # Cada processo mostra seu pacotinho
    print(f"Processo {rank} recebeu:", vet_recebe.tolist())

if __name__ == "__main__":
    main()

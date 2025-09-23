# mpi_sincrona_criancas.py
# - Exige número de processos potência de 2 (2, 4, 8, ...).
# - Trocas em "recursive doubling" usando envio SINCRONO (Ssend) + Recv.
# - Metade envia primeiro e a outra metade recebe primeiro, evitando deadlock.
#
# Linguagem para crianças:
# - "Ssend" = eu só termino de falar quando tenho certeza que você já está ouvindo.
# - Para ninguém falar ao mesmo tempo sem ouvinte, metade fala primeiro, metade escuta primeiro.

from mpi4py import MPI
import numpy as np
import sys

def eh_potencia_de_2(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Conferir potência de 2
    if not eh_potencia_de_2(size):
        if rank == 0:
            print("Por favor, execute com numero de processos potencia de 2 (ex.: 2, 4, 8, 16).")
        MPI.Finalize()
        sys.exit(0)

    tag = 1

    # Meu número inicial
    meu_valor = rank * size
    reducao = np.array([meu_valor], dtype=np.int32)  # buffer local (1 inteiro)
    recebido = np.empty(1, dtype=np.int32)           # buffer para receber (1 inteiro)

    # Rodadas: i = 1, 2, 4, ..., enquanto i <= size/2
    i = 1
    while i <= (size // 2):
        # Quem é meu par nesta rodada?
        destino = rank + i if (rank // i) % 2 == 0 else rank - i

        if (rank // i) % 2 == 0:
            # Este grupo ENVIA primeiro, depois RECEBE
            comm.Ssend([reducao, MPI.INT], dest=destino, tag=tag)
            comm.Recv([recebido, MPI.INT], source=destino, tag=tag)
        else:
            # Este grupo RECEBE primeiro, depois ENVIA
            comm.Recv([recebido, MPI.INT], source=destino, tag=tag)
            comm.Ssend([reducao, MPI.INT], dest=destino, tag=tag)

        # Redução: guardo o MAIOR número
        if recebido[0] > reducao[0]:
            reducao[0] = recebido[0]

        i *= 2  # dobra a distância

    print(f"Rank {rank}: meu_valor = {meu_valor}, reducao = {int(reducao[0])}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

# mpi_isend_criancas.py
# - Número de processos precisa ser potência de 2 (2, 4, 8, 16, ...).
# - Em cada rodada i (1, 2, 4, ...), cada rank troca com um parceiro (rank ± i).
# - Usamos Isend/Irecv (não bloqueantes) e depois Wait/Waitall para concluir.

from mpi4py import MPI
import numpy as np
import sys

def eh_potencia_de_2(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Exigir potência de 2
    if not eh_potencia_de_2(size):
        if rank == 0:
            print("Por favor, execute com numero de processos potencia de 2 (ex.: 2, 4, 8, 16).")
        MPI.Finalize()
        sys.exit(0)

    etiq = 1

    # Cada criança começa com "seu número"
    meu_valor = rank * size
    reducao = np.array([meu_valor], dtype=np.int32)  # buffer de envio (1 inteiro)
    recebido = np.empty(1, dtype=np.int32)           # buffer de recepcao (1 inteiro)

    # Rodadas de recursive doubling: i = 1, 2, 4, ..., <= size/2
    i = 1
    while i <= (size // 2):
        # Escolhe o parceiro desta rodada
        destino = rank + i if (rank // i) % 2 == 0 else rank - i

        # Posta envio e recepcao NAO BLOQUEANTES
        req_send = comm.Isend([reducao, MPI.INT], dest=destino, tag=etiq)
        req_recv = comm.Irecv([recebido, MPI.INT], source=destino, tag=etiq)

        # Garante que terminaram
        MPI.Request.Waitall([req_send, req_recv])

        # Redução: guarda o MAIOR valor
        if recebido[0] > reducao[0]:
            reducao[0] = recebido[0]

        i *= 2  # dobra a distância para a próxima rodada

    print(f"Rank {rank}: meu_valor = {meu_valor}, reducao = {int(reducao[0])}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

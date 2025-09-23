# mpi_bsend_criancas.py
# Versão didática: troca em "dobro recursivo" usando Bsend (envio bufferizado)
from mpi4py import MPI
import numpy as np
import sys

TAM = 4  # tamanho do cartão (número de inteiros por mensagem)

def eh_potencia_de_2(x: int) -> bool:
    return x > 0 and (x & (x - 1)) == 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # 1) Conferir se o número de processos é potência de 2
    if not eh_potencia_de_2(size):
        if rank == 0:
            print("Por favor, execute com número de processos potência de 2 (ex.: 2, 4, 8, 16).")
        MPI.Finalize()
        sys.exit(0)

    # 2) Preparar o buffer do Bsend (sem usar MPI.Pack_size)
    tam_msg = TAM * MPI.INT.Get_size()        # bytes da mensagem (TAM inteiros)
    tam_buffer = tam_msg + MPI.BSEND_OVERHEAD # + overhead do Bsend
    buffer_envio = bytearray(tam_buffer)
    MPI.Attach_buffer(buffer_envio)

    if rank == 0:
        print(f"[INFO] Buffer de Bsend anexado com {tam_buffer} bytes.")

    try:
        # 3) Cada processo cria seu "cartão" com 4 números iguais
        meu_valor = rank * size  # ex.: com 4 processos: 0, 4, 8, 12
        reducao = np.full(TAM, meu_valor, dtype=np.int32)
        recebido = np.empty(TAM, dtype=np.int32)
        etiq = 1

        # 4) Trocas em padrão "recursive doubling": i = 1, 2, 4, ..., <= size/2
        i = 1
        while i <= (size // 2):
            destino = rank + i if (rank // i) % 2 == 0 else rank - i

            # envia (bufferizado) e recebe
            comm.Bsend([reducao, TAM, MPI.INT], dest=destino, tag=etiq)
            comm.Recv([recebido, TAM, MPI.INT], source=destino, tag=etiq)

            # redução por máximo elemento a elemento
            np.maximum(reducao, recebido, out=reducao)
            i *= 2

        print(f"[Rank {rank}] Valor inicial = {meu_valor} | Cartao final (maximos) = {reducao.tolist()}")

    finally:
        # mpi4py retorna APENAS o objeto de buffer
        _buf = MPI.Detach_buffer()
        # opcional: descartar referência explicitamente
        del _buf

if __name__ == "__main__":
    main()

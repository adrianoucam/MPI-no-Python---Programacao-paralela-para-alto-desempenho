# mpi_alltoall_sensores.py
# Objetivo acadêmico:
# - Cada processo gera 1 leitura para cada "sensor" (0..size-1) => vetor de tamanho "size".
# - Usando MPI_Alltoall, o elemento j vai para o processo j.
# - Assim, o processo j recebe todas as leituras do "sensor j" (uma de cada processo) e calcula a média.

from mpi4py import MPI
import numpy as np

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # ----- 1) Cada processo gera 1 leitura por sensor (inteiros para ficar igual ao C)
    # Exemplo simples: leitura = (rank * 100) + sensor_id
    # Assim fica fácil de ver quem mandou o quê.
    sendbuf = (rank * 100 + np.arange(size, dtype=np.int32)).astype(np.int32)

    # Apenas para visualização (como no C):
    print(f"[Entrada]  rank {rank}: {sendbuf.tolist()}")

    # ----- 2) All-to-all: cada posição j de 'sendbuf' vai para o processo j.
    recvbuf = np.empty(size, dtype=np.int32)
    comm.Alltoall([sendbuf, 1, MPI.INT], [recvbuf, 1, MPI.INT])

    # Visualização (como no C):
    print(f"[Saida]    rank {rank}: {recvbuf.tolist()}")

    # ----- 3) Interpretação acadêmica
    # Agora 'recvbuf' contém TODAS as leituras do "sensor rank".
    # Podemos calcular estatísticas desse sensor:
    media = float(np.mean(recvbuf))
    min_v = int(np.min(recvbuf))
    max_v = int(np.max(recvbuf))

    # Para cada processo, mostramos o "sensor rank" e suas métricas
    print(f"[Sensor {rank}] min={min_v}  max={max_v}  media={media:.2f}")

if __name__ == "__main__":
    main()

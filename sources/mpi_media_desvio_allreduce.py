# mpi_media_desvio_allreduce.py
# Ideia para estudo academico:
# - Cada criança (processo) tem 1024 bolinhas com números entre 0 e 1.
# - Cada uma soma e calcula sua MEDIA LOCAL.
# - Com MPI_Allreduce (allreduce), TODO MUNDO soma junto e descobre a MEDIA DA TURMA.
# - Depois cada uma mede "o quao longe" suas bolinhas estao da media (diferenca^2),
#   e com outro Allreduce todas descobrem o DESVIO PADRÃO da turma.

from mpi4py import MPI
import numpy as np
import math

NELEM = 1024  # bolinhas por criança

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()   # qual criança eu sou?
    size = comm.Get_size()   # quantas crianças tem na sala?

    # Semente "igual a do C" (determinística por rank): rank + rank*rank
    seed = rank + rank * rank
    rng = np.random.default_rng(seed)

    # Minhas bolinhas: números aleatórios entre 0 e 1
    nums = rng.random(NELEM, dtype=np.float32)

    # Soma e média locais (da minha sacolinha)
    soma_local = float(np.sum(nums, dtype=np.float64))
    media_local = soma_local / NELEM
    print(f"[Criança {rank}] Soma local = {soma_local:.6f} | Media local = {media_local:.6f}")

    # === Allreduce 1: somar as SOMAS de todo mundo (resultado aparece em todos) ===
    soma_global = comm.allreduce(soma_local, op=MPI.SUM)
    media_turma = soma_global / (NELEM * size)

    # Cada uma mede quanto suas bolinhas estão longe da média da turma (diferença ao quadrado)
    dif_quad_local = float(np.sum((nums - media_turma) ** 2, dtype=np.float64))

    # === Allreduce 2: somar as "diferenças^2" de todo mundo (resultado em todos) ===
    dif_quad_global = comm.allreduce(dif_quad_local, op=MPI.SUM)

    # Desvio padrão = raiz( média das diferenças^2 )
    desvio_padrao = math.sqrt(dif_quad_global / (NELEM * size))

    print(f"[Crianca {rank}] Media da turma = {media_turma:.6f} | Desvio padrao = {desvio_padrao:.6f}")

if __name__ == "__main__":
    main()

# mpi_primos_bag_fixed.py
from mpi4py import MPI
import numpy as np
import math
import sys

CHUNK = 500_000
TAG_WORK = 1
TAG_STOP = 99
ROOT = 0

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if (n % 2) == 0:
        return False
    limit = int(math.isqrt(n))
    for i in range(3, limit + 1, 2):
        if (n % i) == 0:
            return False
    return True

def master(comm: MPI.Comm, n: int, size: int):
    t0 = MPI.Wtime()

    total = 0
    next_start = 3  # primeiro ímpar >=3

    # 1) Distribuição inicial + CONTAGEM de trabalhadores ATIVOS
    active = 0
    for dest in range(1, size):
        if next_start < n:
            start_arr = np.array([next_start], dtype='i')
            comm.Send([start_arr, MPI.INT], dest=dest, tag=TAG_WORK)
            next_start += CHUNK
            active += 1              # <--- só conta quem recebeu TRABALHO
        else:
            dummy = np.array([0], dtype='i')
            comm.Send([dummy, MPI.INT], dest=dest, tag=TAG_STOP)
            # não incrementa 'active' (esse worker já parou e não mandará nada)

    # 2) Enquanto houver trabalhadores ATIVOS, receba parciais e reabasteça
    status = MPI.Status()
    recv_cont = np.empty(1, dtype='i')

    while active > 0:
        comm.Recv([recv_cont, MPI.INT], source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        src = status.Get_source()
        total += int(recv_cont[0])

        if next_start < n:
            start_arr = np.array([next_start], dtype='i')
            comm.Send([start_arr, MPI.INT], dest=src, tag=TAG_WORK)
            next_start += CHUNK
            # 'active' permanece igual (o mesmo worker segue ativo)
        else:
            dummy = np.array([0], dtype='i')
            comm.Send([dummy, MPI.INT], dest=src, tag=TAG_STOP)
            active -= 1              # <--- esse worker encerrou

    # 3) Ajuste do primo 2 (se aplicável)
    if n >= 2:
        total += 1

    t1 = MPI.Wtime()
    print(f"Quant. de primos entre 1 e {n}: {total}")
    print(f"Tempo de execucao: {t1 - t0:0.3f} s")

def worker(comm: MPI.Comm, n: int):
    status = MPI.Status()
    start_buf = np.empty(1, dtype='i')

    while True:
        comm.Recv([start_buf, MPI.INT], source=ROOT, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()
        if tag == TAG_STOP:
            break

        start = int(start_buf[0])
        # Garante que o início seja ÍMPAR (para não pular ímpares)
        if start % 2 == 0:
            start += 1

        upper = min(start + CHUNK, n)  # i < n (compatível com o C)

        count = 0
        for i in range(start, upper, 2):  # só ímpares
            if is_prime(i):
                count += 1

        cont_arr = np.array([count], dtype='i')
        comm.Send([cont_arr, MPI.INT], dest=ROOT, tag=TAG_WORK)

def main():
    if len(sys.argv) < 2:
        print("Entre com o valor do maior inteiro como parâmetro para o programa.")
        sys.exit(0)
    try:
        n = int(sys.argv[1])
    except Exception:
        print("Parametro invalido. Use um inteiro, por exemplo: 100000000")
        sys.exit(1)

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if size < 2:
        if rank == 0:
            print("Este programa deve ser executado com no mínimo dois processos.")
        MPI.COMM_WORLD.Abort(1)

    if rank == ROOT:
        master(comm, n, size)
    else:
        worker(comm, n)

    comm.Barrier()
    MPI.Finalize()

if __name__ == "__main__":
    main()

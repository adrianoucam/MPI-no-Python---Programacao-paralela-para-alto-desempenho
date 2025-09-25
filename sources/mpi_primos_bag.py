# mpi_primos_bag.py
# Contagem de primos em 1..n com distribuição dinâmica de tarefas (bag-of-tasks)
# Mestre (rank 0) envia blocos de tamanho CHUNK para trabalhadores (ranks >= 1).
# Trabalhadores contam primos ímpares no bloco e devolvem a parcial.
# Ao final, o mestre soma +1 para o primo 2 (se n >= 2).
# pip install mpi4py
# mpiexec -n 4 python mpi_primos_bag.py 100000000

from mpi4py import MPI
import numpy as np
import math
import sys

CHUNK = 500_000        # equivalente a #define TAMANHO 500000
TAG_WORK = 1
TAG_STOP = 99
ROOT = 0

def is_prime(n: int) -> bool:
    """Teste simples de primalidade para inteiros positivos."""
    if n < 2:
        return False
    if n == 2:
        return True
    if (n % 2) == 0:
        return False
    # testa ímpares até sqrt(n)
    limit = int(math.isqrt(n))
    for i in range(3, limit + 1, 2):
        if (n % i) == 0:
            return False
    return True

def master(comm: MPI.Comm, n: int, size: int):
    """Lógica do mestre: distribui blocos, agrega parciais, envia STOP."""
    t0 = MPI.Wtime()

    total = 0
    next_start = 3  # começamos pelos ímpares >= 3

    # Envia um primeiro bloco para cada trabalhador; se não houver trabalho, já envia STOP
    workers = range(1, size)
    for dest in workers:
        if next_start < n:
            start_arr = np.array([next_start], dtype='i')
            comm.Send([start_arr, MPI.INT], dest=dest, tag=TAG_WORK)
            next_start += CHUNK
        else:
            dummy = np.array([0], dtype='i')
            comm.Send([dummy, MPI.INT], dest=dest, tag=TAG_STOP)

    # Recebe parciais e reenvia novo trabalho até esgotar; depois manda STOP
    stopped = 0
    status = MPI.Status()
    recv_cont = np.empty(1, dtype='i')

    while stopped < (size - 1):
        # recebe de qualquer trabalhador que terminou
        comm.Recv([recv_cont, MPI.INT], source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        src = status.Get_source()
        total += int(recv_cont[0])

        # há mais trabalho?
        if next_start < n:
            start_arr = np.array([next_start], dtype='i')
            comm.Send([start_arr, MPI.INT], dest=src, tag=TAG_WORK)
            next_start += CHUNK
        else:
            dummy = np.array([0], dtype='i')
            comm.Send([dummy, MPI.INT], dest=src, tag=TAG_STOP)
            stopped += 1

    # acrescenta o primo 2, se aplicável
    if n >= 2:
        total += 1

    t1 = MPI.Wtime()
    print(f"Quant. de primos entre 1 e {n}: {total}")
    print(f"Tempo de execucao: {t1 - t0:0.3f} s")

def worker(comm: MPI.Comm, n: int):
    """Lógica do trabalhador: recebe bloco, conta primos ímpares e devolve parcial."""
    status = MPI.Status()
    start_buf = np.empty(1, dtype='i')

    while True:
        comm.Recv([start_buf, MPI.INT], source=ROOT, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()
        if tag == TAG_STOP:
            break

        start = int(start_buf[0])
        # limite superior do bloco (sem ultrapassar n); respeita semântica i < n do C original
        upper = min(start + CHUNK, n)

        # contamos apenas ímpares (start sempre ímpar)
        count = 0
        for i in range(start, upper, 2):
            if is_prime(i):
                count += 1

        cont_arr = np.array([count], dtype='i')
        comm.Send([cont_arr, MPI.INT], dest=ROOT, tag=TAG_WORK)

def main():
    # leitura do parâmetro n
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

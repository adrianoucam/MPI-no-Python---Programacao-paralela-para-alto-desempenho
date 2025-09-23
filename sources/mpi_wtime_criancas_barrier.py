# mpi_wtime_criancas_barrier.py
# Mede o tempo de um "trabalho qualquer" com sincronização prévia (Barrier).

from mpi4py import MPI
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Medição de tempo com MPI.Wtime() e sincronização (Barrier)"
    )
    parser.add_argument("--n", type=int, default=10_000_000,
                        help="Número de iterações do 'trabalho' (default: 10 milhões)")
    args = parser.parse_args()
    n = args.n

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # Sincroniza todos antes de começar a medir
    comm.Barrier()
    t0 = MPI.Wtime()

    # Trabalho: converter i -> float e guardar em 'a'
    a = 0.0
    for i in range(n):
        a = float(i)

    t1 = MPI.Wtime()
    tick = MPI.Wtick()

    print(f"[Rank {rank}] Tempo = {t1 - t0:0.6f} s | a = {a:0.0f} | precisão = {tick:0.3e} s")

    MPI.Finalize()

if __name__ == "__main__":
    main()

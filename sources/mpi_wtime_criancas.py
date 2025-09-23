# mpi_wtime_criancas.py
# Mede o tempo de um "trabalho qualquer" usando MPI.Wtime()
# e imprime também a precisão do relógio com MPI.Wtick().

from mpi4py import MPI
import argparse

def main():
    parser = argparse.ArgumentParser(description="Exemplo de medição de tempo com MPI.Wtime()")
    parser.add_argument("--n", type=int, default=10_000_000,  # ajuste conforme sua máquina
                        help="Número de iterações do 'trabalho' (default: 10 milhões)")
    args = parser.parse_args()
    n = args.n

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # Início da medição
    t0 = MPI.Wtime()

    # "Trabalho qualquer": converter i -> float e guardar em 'a'
    a = 0.0
    for i in range(n):
        a = float(i)

    # Fim da medição
    t1 = MPI.Wtime()
    tick = MPI.Wtick()

    # Cada processo imprime seu tempo (como no C, mas identificando o rank)
    print(f"[Rank {rank}] Gastos {t1 - t0:0.6f} s para calcular a = {a:0.0f} "
          f"com precisão {tick:0.3e} s")

    MPI.Finalize()

if __name__ == "__main__":
    main()

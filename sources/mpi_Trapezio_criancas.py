# mpi_trapezio_criancas.py
# Integração numérica por trapézios de exp(x) no intervalo [a, b]
# Cada processo soma um subconjunto dos pontos (passo intercalado por 'size')
# e o rank 0 recolhe as parciais via Send/Recv (como no código C).

from mpi4py import MPI
import numpy as np
import math

def f(x: float) -> float:
    return math.exp(x)  # função exponencial

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Parâmetros da integral
    a = 0.0
    b = 1.0
    n = 100_000_000  # número de trapézios (igual ao C)

    h = (b - a) / n   # largura de cada trapézio
    tag = 3           # etiqueta de mensagem (qualquer)

    # Rank 0 mede o tempo e adiciona 1/2*(f(a)+f(b)) como no C
    soma_local = 0.0
    if rank == 0:
        t0 = MPI.Wtime()
        soma_local += 0.5 * (f(a) + f(b))

    # Cada processo acumula f(x) nos pontos internos: x = a + h*(rank+1), a cada 'size' passos
    x = a + h * (rank + 1)
    while x < b:
        soma_local += f(x)
        x += size * h

    integral_local = soma_local * h

    # Envio/Recepção explícitos (como no C)
    if rank == 0:
        total = integral_local
        recv = np.empty(1, dtype=np.float64)
        for origem in range(1, size):
            comm.Recv([recv, MPI.DOUBLE], source=origem, tag=tag)
            total += float(recv[0])
        t1 = MPI.Wtime()
        print(f"Foram gastos {t1 - t0:3.1f} segundos")
        print(f"Com n = {n} trapezoides, a estimativa")
        print(f"da integral de {a:.6f} até {b:.6f} = {total:.12f}")
    else:
        send = np.array([integral_local], dtype=np.float64)
        comm.Send([send, MPI.DOUBLE], dest=0, tag=tag)

    MPI.Finalize()

if __name__ == "__main__":
    main()

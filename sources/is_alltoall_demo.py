# is_alltoall_demo.py
# Exemplo acadêmico do NAS-IS: bucket sort paralelo com mpi4py.
# Usa: Allreduce (histograma global), Alltoall (contagens) e Alltoallv (dados).
# Execução: mpiexec -n 4 python is_alltoall_demo.py --n 10000 --K 1000 --debug

from mpi4py import MPI
import numpy as np
import argparse
import sys
import time

def integer_sort_alltoall(N, K, debug=False):
    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()
    size  = comm.Get_size()

    # ---------- 0) Preparação ----------
    rng = np.random.default_rng(seed=1234 + rank)
    # Gera N chaves inteiras em [0, K)
    keys_local = rng.integers(low=0, high=K, size=N, dtype=np.int32)

    # ---------- 1) Histograma local por destino ----------
    # destino = bucket(key)
    # bucket: divide K em 'size' faixas iguais (assuma K >= size)
    # dest \in [0, size-1]
    dests = (keys_local.astype(np.int64) * size // K).astype(np.int32)
    dests = np.clip(dests, 0, size - 1)  # segurança

    send_counts = np.zeros(size, dtype=np.int32)
    for d in dests:
        send_counts[d] += 1

    # ---------- 2) Histograma global (apenas p/ monitorar) ----------
    global_counts = np.zeros_like(send_counts)
    comm.Allreduce(send_counts, global_counts, op=MPI.SUM)

    # ---------- 3) Alltoall de contagens (para saber quanto vou receber) ----------
    recv_counts = np.zeros(size, dtype=np.int32)
    # Forma “vetorial” explícita: usa buffers numpy com tipo MPI.INT
    comm.Alltoall([send_counts, MPI.INT], [recv_counts, MPI.INT])

    # Displacements (em número de elementos, não bytes)
    sdispls = np.zeros(size, dtype=np.int32)
    rdispls = np.zeros(size, dtype=np.int32)
    if size > 1:
        sdispls[1:] = np.cumsum(send_counts[:-1])
        rdispls[1:] = np.cumsum(recv_counts[:-1])

    # Reorganiza as chaves no buffer de envio agrupadas por destino
    sendbuf = np.empty(N, dtype=np.int32)
    curs = np.zeros(size, dtype=np.int32)
    curs[:] = sdispls  # cursor de escrita por destino
    for key, d in zip(keys_local, dests):
        idx = curs[d]
        sendbuf[idx] = key
        curs[d] += 1

    # Buffer de recepção (tamanho = total que vou receber)
    total_recv = int(np.sum(recv_counts))
    recvbuf = np.empty(total_recv, dtype=np.int32)

    # ---------- 4) Alltoallv de dados ----------
    comm.Alltoallv([sendbuf, (send_counts, sdispls), MPI.INT],
                   [recvbuf, (recv_counts, rdispls), MPI.INT])

    # ---------- 5) Ordenação local e checagens ----------
    recvbuf.sort()  # ordena localmente o “meu” intervalo de chaves
    # Cada rank deve ter chaves na faixa [rank*K/size, (rank+1)*K/size)
    lo = (rank * K) // size
    hi = ((rank + 1) * K) // size  # limite superior exclusivo
    ok_range = (recvbuf.size == 0) or (recvbuf.min() >= lo and recvbuf.max() < hi)

    # Checagem global de consistência:
    # - soma total de elementos
    total_after = comm.allreduce(recvbuf.size, op=MPI.SUM)
    ok_total = (total_after == size * N)

    # Podemos também verificar fronteiras (max local <= min do próximo)
    #  -> junta mins e maxs
    loc_min = recvbuf[0] if recvbuf.size > 0 else +2**31-1
    loc_max = recvbuf[-1] if recvbuf.size > 0 else -2**31
    mins = comm.allgather(loc_min)
    maxs = comm.allgather(loc_max)
    borders_ok = True
    for r in range(size - 1):
        if maxs[r] > mins[r + 1]:
            borders_ok = False
            break

    if debug and rank == 0:
        print(f"[DEBUG] global_counts = {global_counts.tolist()}")
    if debug:
        print(f"[rank {rank}] recv={recvbuf.size}  faixas_ok={ok_range}  "
              f"total_ok={ok_total} borders_ok={borders_ok}  "
              f"range=({lo},{hi})")

    return recvbuf, ok_range and ok_total and borders_ok

def main():
    parser = argparse.ArgumentParser(description="IS (Integer Sort) com Allreduce + Alltoall(v) — mpi4py")
    parser.add_argument("--n",  type=int, default=10_000, help="número de chaves por processo")
    parser.add_argument("--K",  type=int, default=1000,   help="universo das chaves (0..K-1)")
    parser.add_argument("--debug", action="store_true",   help="imprime diagnósticos")
    args = parser.parse_args()

    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()

    # Pequena sincronização p/ medir tempo só do núcleo
    comm.Barrier()
    t0 = MPI.Wtime()
    _, ok = integer_sort_alltoall(args.n, args.K, debug=args.debug)
    comm.Barrier()
    t1 = MPI.Wtime()

    if rank == 0:
        print(f"[OK={ok}] tempo total = {t1 - t0:0.6f} s  (P={comm.Get_size()}, N={args.n}, K={args.K})")

if __name__ == "__main__":
    main()

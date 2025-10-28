# mpi_vector_ops.py
# ============================================================
# Operações de vetores em larga escala com mpi4py (uso acadêmico)
#   - sum  : soma de todos os elementos de x (reduce + broadcast do resultado)
#   - dot  : produto interno x·y (reduce do parcial via Allreduce)
#   - saxpy: y <- a*x + y (distribui com Scatterv e recolhe com Allgatherv)
#
# Execute:
#   mpiexec -n 4 python3 mpi_vector_ops.py --op dot     --n 200000000
#   mpiexec -n 8 python3 mpi_vector_ops.py --op saxpy   --n 100000000 --alpha 2.0
#   mpiexec -n 8 python3 mpi_vector_ops.py --op sum     --n 50000000
#
# Notas:
# - Gera vetores com PRNG determinístico (seed) e dtype float64 por padrão.
# - Usa Scatterv/Allgatherv com contagens diferentes para tratar N % P != 0.
# - Reporta tempo, throughput aproximado (GiB/s) e, quando aplicável, erro de checagem.
# ============================================================

from mpi4py import MPI
import numpy as np
import argparse
import time

comm = MPI.COMM_WORLD
RANK = comm.Get_rank()
SIZE = comm.Get_size()
HOST = MPI.Get_processor_name()

def log(msg: str):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] [rank {RANK}] [host {HOST}] {msg}", flush=True)

def make_counts_displs(n: int, p: int):
    """Divide n elementos entre p processos -> counts, displs (para Scatterv/Allgatherv)."""
    base = n // p
    rem = n % p
    counts = np.array([base + (1 if r < rem else 0) for r in range(p)], dtype=np.int64)
    displs = np.zeros(p, dtype=np.int64)
    displs[1:] = np.cumsum(counts[:-1])
    return counts, displs

def gib(nbytes):
    return nbytes / (1024**3)

def op_sum(n: int, seed: int):
    """Soma global dos elementos de x (gerado apenas no rank 0 para medir tráfego)."""
    # rank 0 gera os dados e distribui
    counts, displs = make_counts_displs(n, SIZE)
    local_n = int(counts[RANK])

    if RANK == 0:
        rng = np.random.default_rng(seed)
        x = rng.random(n, dtype=np.float64)
    else:
        x = None

    x_local = np.empty(local_n, dtype=np.float64)

    # Scatterv
    t0 = MPI.Wtime()
    comm.Scatterv([x, counts, displs, MPI.DOUBLE] if RANK == 0 else [None, None, None, MPI.DOUBLE],
                  x_local, root=0)

    # Reduce (soma local -> global)
    local_sum = float(np.sum(x_local))
    global_sum = comm.allreduce(local_sum, op=MPI.SUM)
    t1 = MPI.Wtime()

    # Métrica: tráfego aproximado = N * 8 bytes (uma passagem) + meta (ignorado)
    moved_gib = gib(n * 8.0)  # aproximação
    if RANK == 0:
        log(f"[sum] N={n:,}  soma={global_sum:.6e}  tempo={t1-t0:0.3f}s  ~movido={moved_gib:.2f} GiB  ~{moved_gib/(t1-t0):.2f} GiB/s")

def op_dot(n: int, seed: int):
    """Produto interno x·y (Allreduce de parciais)."""
    counts, displs = make_counts_displs(n, SIZE)
    local_n = int(counts[RANK])

    # rank 0 gera e espalha; demais recebem
    if RANK == 0:
        rng = np.random.default_rng(seed)
        x = rng.random(n, dtype=np.float64)
        y = rng.random(n, dtype=np.float64)
    else:
        x = y = None

    x_local = np.empty(local_n, dtype=np.float64)
    y_local = np.empty(local_n, dtype=np.float64)

    t0 = MPI.Wtime()
    comm.Scatterv([x, counts, displs, MPI.DOUBLE] if RANK == 0 else [None, None, None, MPI.DOUBLE],
                  x_local, root=0)
    comm.Scatterv([y, counts, displs, MPI.DOUBLE] if RANK == 0 else [None, None, None, MPI.DOUBLE],
                  y_local, root=0)

    # parcela local
    local_dot = float(np.dot(x_local, y_local))
    # soma global
    global_dot = comm.allreduce(local_dot, op=MPI.SUM)
    t1 = MPI.Wtime()

    # tráfego ~ 2*N*8 (duas distribuições) + Allreduce escalar (irrelevante)
    moved_gib = gib(2 * n * 8.0)
    if RANK == 0:
        log(f"[dot] N={n:,}  x·y={global_dot:.6e}  tempo={t1-t0:0.3f}s  ~movido={moved_gib:.2f} GiB  ~{moved_gib/(t1-t0):.2f} GiB/s")

def op_saxpy(n: int, alpha: float, seed: int, check: bool):
    """SAXPY: y <- alpha*x + y. Distribui com Scatterv e recolhe com Allgatherv."""
    counts, displs = make_counts_displs(n, SIZE)
    local_n = int(counts[RANK])

    if RANK == 0:
        rng = np.random.default_rng(seed)
        x = rng.random(n, dtype=np.float64)
        y = rng.random(n, dtype=np.float64)
        if check:
            y_ref = y.copy()  # para validação
    else:
        x = y = None
        y_ref = None

    x_local = np.empty(local_n, dtype=np.float64)
    y_local = np.empty(local_n, dtype=np.float64)

    # Distribui x e y locais
    t0 = MPI.Wtime()
    comm.Scatterv([x, counts, displs, MPI.DOUBLE] if RANK == 0 else [None, None, None, MPI.DOUBLE],
                  x_local, root=0)
    comm.Scatterv([y, counts, displs, MPI.DOUBLE] if RANK == 0 else [None, None, None, MPI.DOUBLE],
                  y_local, root=0)

    # Cálculo local
    y_local = alpha * x_local + y_local

    # Recolhe y final em todos (Allgatherv), para que todos tenham y completo (útil em aulas/demos)
    y_out = None
    if RANK == 0:
        y_out = np.empty(n, dtype=np.float64)

    comm.Gatherv(y_local,
                 [y_out, counts, displs, MPI.DOUBLE] if RANK == 0 else None,
                 root=0)
    t1 = MPI.Wtime()

    # tráfego ~ 2*N*8 (Scatterv de x e y) + N*8 (Gatherv de y)
    moved_gib = gib(3 * n * 8.0)
    if RANK == 0:
        log(f"[saxpy] N={n:,}  alpha={alpha}  tempo={t1-t0:0.3f}s  ~movido={moved_gib:.2f} GiB  ~{moved_gib/(t1-t0):.2f} GiB/s")
        if check:
            y_ref = alpha * x + y_ref
            max_abs_err = float(np.max(np.abs(y_out - y_ref)))
            log(f"[saxpy] max|erro| = {max_abs_err:.3e}")

def main():
    ap = argparse.ArgumentParser(description="Operações de vetor com MPI (mpi4py) — acadêmico")
    ap.add_argument("--op", choices=["sum", "dot", "saxpy"], required=True, help="qual operação executar")
    ap.add_argument("--n", type=int, default=10_000_000, help="tamanho do(s) vetor(es)")
    ap.add_argument("--alpha", type=float, default=2.0, help="alpha do SAXPY")
    ap.add_argument("--seed", type=int, default=42, help="seed do gerador aleatório")
    ap.add_argument("--check", action="store_true", help="valida SAXPY com referência no rank 0")
    args = ap.parse_args()

    if SIZE < 2:
        if RANK == 0:
            print("Execute com pelo menos 2 processos: mpiexec -n 4 python3 mpi_vector_ops.py --op dot --n 1e7")
        MPI.COMM_WORLD.Abort(1)

    if RANK == 0:
        log(f"INÍCIO | op={args.op} | N={args.n:,} | P={SIZE}")

    if args.op == "sum":
        op_sum(args.n, args.seed)
    elif args.op == "dot":
        op_dot(args.n, args.seed)
    elif args.op == "saxpy":
        op_saxpy(args.n, args.alpha, args.seed, args.check)

    comm.Barrier()
    if RANK == 0:
        log("FIM")

if __name__ == "__main__":
    main()

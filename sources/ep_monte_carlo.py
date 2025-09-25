# ep_monte_carlo.py
# -----------------------------------------------------------
# EP - Embarrassingly Parallel (NAS): Monte Carlo para estimar π
# Cada rank gera amostras independentes; só há comunicação no fim.
#
# Use Reduce (root agrega) ou Allreduce (todos recebem o total).
#
# Execução:
#   mpiexec -n 4 python ep_monte_carlo.py --samples-per-rank 2000000 --op allreduce
#   mpiexec -n 4 python ep_monte_carlo.py --samples-per-rank 2000000 --op reduce
#   mpiexec -n 4 python ep_monte_carlo.py --samples-per-rank 2000000 --op both
# -----------------------------------------------------------

from mpi4py import MPI
import numpy as np
import math
import argparse

def local_hits_monte_carlo(n_samples: int, seed: int, chunk: int = 1_000_000) -> int:
    """
    Gera n_samples pontos (x,y) ~ U[0,1]^2 e conta quantos caem no quarto de círculo x^2+y^2 <= 1.
    Processa em blocos (chunk) para não estourar memória.
    """
    rng = np.random.default_rng(seed)
    hits = 0
    full_chunks, rest = divmod(n_samples, chunk)

    for _ in range(full_chunks):
        x = rng.random(chunk, dtype=np.float64)
        y = rng.random(chunk, dtype=np.float64)
        hits += int(np.count_nonzero(x*x + y*y <= 1.0))

    if rest:
        x = rng.random(rest, dtype=np.float64)
        y = rng.random(rest, dtype=np.float64)
        hits += int(np.count_nonzero(x*x + y*y <= 1.0))

    return hits

def run(mode: str, samples_per_rank: int, base_seed: int, chunk: int):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # EP: trabalho independente por rank
    # semente distinta por rank para independência estatística
    seed = base_seed + rank * 1_000_003

    comm.Barrier()
    t0 = MPI.Wtime()
    local_hits = local_hits_monte_carlo(samples_per_rank, seed, chunk=chunk)
    local_samples = samples_per_rank

    if mode.lower() in ("reduce", "both"):
        # Apenas o ROOT recebe os somatórios
        glob_hits_r = comm.reduce(local_hits, op=MPI.SUM, root=0)
        glob_samp_r = comm.reduce(local_samples, op=MPI.SUM, root=0)
        if rank == 0:
            pi_r = 4.0 * (glob_hits_r / glob_samp_r)
            err_r = abs(pi_r - math.pi)
        else:
            pi_r = None
            err_r = None
    else:
        pi_r = err_r = None

    if mode.lower() in ("allreduce", "both"):
        # Todos recebem os somatórios
        glob_hits_a = comm.allreduce(local_hits, op=MPI.SUM)
        glob_samp_a = comm.allreduce(local_samples, op=MPI.SUM)
        pi_a = 4.0 * (glob_hits_a / glob_samp_a)
        err_a = abs(pi_a - math.pi)
    else:
        pi_a = err_a = None

    comm.Barrier()
    t1 = MPI.Wtime()

    # Impressão organizada
    if rank == 0:
       print(f"\n[EP Monte Carlo] P={size} | samples_per_rank={samples_per_rank:,} | total={samples_per_rank*size:,}")
       print(f"Tempo total: {t1 - t0:0.6f} s")

       if mode.lower() in ("reduce", "both"):
           print(f"  Reduce    -> pi ~= {pi_r:.12f} | erro={err_r:.3e}")

       if mode.lower() in ("allreduce", "both"):
           print(f"  Allreduce -> pi ~= {pi_a:.12f} | erro={err_a:.3e}")

       if mode.lower() == "both":
           print(f"  Diferença (abs): {abs(pi_a - pi_r):.3e}")

def main():
    parser = argparse.ArgumentParser(description="EP Monte Carlo (π) com Reduce/Allreduce — mpi4py")
    parser.add_argument("--samples-per-rank", type=int, default=1_000_000,
                        help="número de amostras que cada processo gera")
    parser.add_argument("--op", type=str, default="allreduce", choices=["reduce", "allreduce", "both"],
                        help="qual operação coletiva usar na agregação")
    parser.add_argument("--seed", type=int, default=1234, help="semente base do gerador de números")
    parser.add_argument("--chunk", type=int, default=1_000_000, help="tamanho do bloco para gerar amostras")
    args = parser.parse_args()

    run(args.op, args.samples_per_rank, args.seed, args.chunk)

    MPI.Finalize()

if __name__ == "__main__":
    main()

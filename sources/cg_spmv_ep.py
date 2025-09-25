# cg_spmv_ep.py
# ------------------------------------------------------------
# CG paralelo (mpi4py) para A x = b com A = Laplaciano 2D (5-pontos, Dirichlet u=0).
# - Decomposição 1D por linhas (cada rank fica com um bloco de linhas).
# - SpMV distribuído com troca de halos (linhas superiores/inferiores).
# - Comunicação configurável: --mode sendrecv | isendirecv
# - Produtos internos e norma global via Allreduce.
#
# Execução:
#   mpiexec -n 4 python cg_spmv_ep.py --Nx 256 --Ny 256 --mode sendrecv
# ------------------------------------------------------------

from mpi4py import MPI
import numpy as np
import argparse
import math
from typing import Tuple

# ---------- util: partição de linhas ----------
def split_rows(Ny: int, size: int) -> Tuple[np.ndarray, np.ndarray]:
    """Distribui Ny linhas entre 'size' processos de forma balanceada."""
    counts = np.full(size, Ny // size, dtype=int)
    counts[: Ny % size] += 1
    displs = np.zeros(size, dtype=int)
    displs[1:] = np.cumsum(counts[:-1])
    return counts, displs

# ---------- alocação com halos ----------
def alloc_with_halos(nx: int, ny_local: int) -> np.ndarray:
    """Array (ny_local+2, nx+2) com halos nas bordas."""
    return np.zeros((ny_local + 2, nx + 2), dtype=np.float64)

# ---------- troca de halos: duas variantes ----------
def halo_exchange_sendrecv(arr: np.ndarray, comm: MPI.Comm, up: int, down: int, tagbase: int = 100):
    """Troca de linhas fantasmas usando MPI.Sendrecv (bloqueante e simétrica)."""
    # Envia 1ª linha interior para 'up'; recebe última linha interior de 'down' (ghost inferior)
    if up != MPI.PROC_NULL or down != MPI.PROC_NULL:
        send_up = arr[1, 1:-1].copy()
        recv_from_down = np.empty_like(send_up)
        comm.Sendrecv(sendbuf=send_up, dest=up,   sendtag=tagbase+0,
                      recvbuf=recv_from_down, source=down, recvtag=tagbase+0)
        if down != MPI.PROC_NULL:
            arr[-1, 1:-1] = recv_from_down
        else:
            arr[-1, 1:-1] = 0.0

        # Envia última linha interior para 'down'; recebe 1ª linha interior de 'up' (ghost superior)
        send_down = arr[-2, 1:-1].copy()
        recv_from_up = np.empty_like(send_down)
        comm.Sendrecv(sendbuf=send_down, dest=down, sendtag=tagbase+1,
                      recvbuf=recv_from_up, source=up,   recvtag=tagbase+1)
        if up != MPI.PROC_NULL:
            arr[0, 1:-1] = recv_from_up
        else:
            arr[0, 1:-1] = 0.0
    else:
        # Sem vizinhos (apenas 1 processo)
        arr[0, 1:-1]  = 0.0
        arr[-1, 1:-1] = 0.0

def halo_exchange_isendirecv(arr: np.ndarray, comm: MPI.Comm, up: int, down: int, tagbase: int = 200):
    """Troca de linhas fantasmas usando Isend/Irecv (não-bloqueante)."""
    reqs = []

    # Recebe topo do 'up' (ele manda a linha de baixo dele para cima)
    if up != MPI.PROC_NULL:
        reqs.append(comm.Irecv(arr[0, 1:-1], source=up, tag=tagbase+11))
    else:
        arr[0, 1:-1] = 0.0

    # Recebe base do 'down' (ele manda a linha de cima dele para cima)
    if down != MPI.PROC_NULL:
        reqs.append(comm.Irecv(arr[-1, 1:-1], source=down, tag=tagbase+10))
    else:
        arr[-1, 1:-1] = 0.0

    # Envia linha de cima para 'up' (sobe)
    if up != MPI.PROC_NULL:
        reqs.append(comm.Isend(arr[1, 1:-1].copy(), dest=up, tag=tagbase+10))

    # Envia linha de baixo para 'down' (desce)
    if down != MPI.PROC_NULL:
        reqs.append(comm.Isend(arr[-2, 1:-1].copy(), dest=down, tag=tagbase+11))

    if reqs:
        MPI.Request.Waitall(reqs)

# ---------- SpMV (A·v) com Laplaciano 5-pontos ----------
def spmv_Ax(v: np.ndarray, out: np.ndarray, nx: int, comm: MPI.Comm, up: int, down: int, mode: str):
    """
    Aplica A (Laplaciano 5-pontos com Dirichlet 0) sobre 'v' e grava em 'out'.
    'v' e 'out' têm halos (ny_local+2, nx+2). Decomp. por linhas => trocar apenas linhas fantasmas.
    A v = 4*v - (v_l + v_r + v_u + v_d)   (sem 1/h^2; b já é h^2 f)
    """
    # Bordas esquerda/direita são Dirichlet 0 → halos laterais = 0
    v[:, 0]  = 0.0
    v[:, -1] = 0.0

    # Halos superior/inferior vindos dos vizinhos
    if mode == "sendrecv":
        halo_exchange_sendrecv(v, comm, up, down, tagbase=100)
    else:
        halo_exchange_isendirecv(v, comm, up, down, tagbase=200)

    # Aplica stencil no interior
    # out = A v
    out[1:-1, 1:-1] = (4.0 * v[1:-1, 1:-1]
                       - (v[1:-1, 2:] + v[1:-1, :-2] + v[2:, 1:-1] + v[:-2, 1:-1]))

# ---------- produtos internos globais ----------
def dot_global(a: np.ndarray, b: np.ndarray, comm: MPI.Comm) -> float:
    """<a, b> global (só interior)."""
    loc = float(np.dot(a.ravel(), b.ravel()))
    return comm.allreduce(loc, op=MPI.SUM)

# ---------- CG principal ----------
def conjugate_gradient(nx: int, ny: int, max_iters: int, tol: float, mode: str):
    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()
    size  = comm.Get_size()

    # Partição de linhas
    counts, displs = split_rows(ny, size)
    ny_local = int(counts[rank])

    # Vizinhos 1D (por linhas)
    up   = rank - 1 if rank > 0        else MPI.PROC_NULL
    down = rank + 1 if rank < size - 1 else MPI.PROC_NULL

    # Passo de malha para b = h^2 f   (f=1)
    hx = 1.0 / (nx + 1)
    hy = 1.0 / (ny + 1)
    assert abs(hx - hy) < 1e-12, "Exemplo assume hx == hy; use Nx == Ny."
    h2 = hx * hy  # com hx==hy, isso vira hx^2

    # Vetores com halos
    x  = alloc_with_halos(nx, ny_local)  # solução
    r  = alloc_with_halos(nx, ny_local)  # resíduo
    p  = alloc_with_halos(nx, ny_local)  # direção de busca
    Ap = alloc_with_halos(nx, ny_local)  # A·p

    # Monta b (interior): b = h^2 * f, com f=1 → b = h^2
    b = alloc_with_halos(nx, ny_local)
    b[1:-1, 1:-1] = h2

    # Inicialização CG
    # x = 0 ⇒ r = b - A x = b
    r[1:-1, 1:-1] = b[1:-1, 1:-1]
    p[1:-1, 1:-1] = r[1:-1, 1:-1]

    # Norma relativa do resíduo
    rr = dot_global(r[1:-1, 1:-1], r[1:-1, 1:-1], comm)
    rr0 = max(rr, 1e-30)  # evita divisões por zero se b=0
    rel = math.sqrt(rr / rr0)
    if rank == 0:
        print(f"[init] ||r||/||r0|| = {rel:.3e}  (rr={rr:.3e})")

    # Iterações CG
    for it in range(1, max_iters + 1):
        # Ap = A p
        spmv_Ax(p, Ap, nx, comm, up, down, mode)

        pAp = dot_global(p[1:-1, 1:-1], Ap[1:-1, 1:-1], comm)
        if abs(pAp) < 1e-30:
            if rank == 0:
                print(f"[CG] p^T(Ap) ~ 0 na iteração {it}, parando.")
            break

        alpha = rr / pAp

        # Atualizações locais (somente interior)
        x[1:-1, 1:-1]  += alpha * p[1:-1, 1:-1]
        r[1:-1, 1:-1]  -= alpha * Ap[1:-1, 1:-1]

        rr_new = dot_global(r[1:-1, 1:-1], r[1:-1, 1:-1], comm)
        rel = math.sqrt(rr_new / rr0)

        if rank == 0 and (it == 1 or it % 10 == 0 or rel < tol):
            print(f"[it {it:4d}] ||r||/||r0|| = {rel:.3e}")

        if rel < tol:
            break

        beta = rr_new / rr
        # p = r + beta * p
        p[1:-1, 1:-1] = r[1:-1, 1:-1] + beta * p[1:-1, 1:-1]
        rr = rr_new

    return x, rel, it

# ---------- main ----------
def main():
    parser = argparse.ArgumentParser(description="CG paralelo (SpMV + halo + Allreduce) — mpi4py")
    parser.add_argument("--Nx", type=int, default=128, help="pontos interiores em X (global)")
    parser.add_argument("--Ny", type=int, default=128, help="pontos interiores em Y (global)")
    parser.add_argument("--max-iters", type=int, default=200, help="máximo de iterações do CG")
    parser.add_argument("--tol", type=float, default=1e-8, help="tolerância de parada (resíduo relativo)")
    parser.add_argument("--mode", type=str, default="sendrecv", choices=["sendrecv", "isendirecv"],
                        help="método de troca de halos (bloqueante ou não-bloqueante)")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    comm.Barrier()
    t0 = MPI.Wtime()
    x, rel, it = conjugate_gradient(args.Nx, args.Ny, args.max_iters, args.tol, args.mode)
    comm.Barrier()
    t1 = MPI.Wtime()

    if rank == 0:
        print(f"\n[Resumo] modo={args.mode}  P={comm.Get_size()}  Nx={args.Nx} Ny={args.Ny}")
        print(f"Convergiu (||r||/||r0|| = {rel:.3e}) em {it} iterações. Tempo total: {t1 - t0:0.6f} s")

    MPI.Finalize()

if __name__ == "__main__":
    main()

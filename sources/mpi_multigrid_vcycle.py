# mpi_multigrid_vcycle.py
# ============================================================
# Exemplo acadêmico de Multigrid (Ciclo-V) 2D com mpi4py (sem deadlock)
# mpiexec -n 4 python3 mpi_multigrid_vcycle_fixed.py --Nx 128 --Ny 128 --cycles 5
#
# Problema: -∇² u = f em [0,1]x[0,1], u=0 nas bordas (Dirichlet)
# Discretização 5-pontos; domínio particionado em grade cartesiana de processos.
# Comunicação: troca de halos com MPI_Sendrecv; norma global com Allreduce.
# mpiexec -n 4 python3 mpi_multigrid_vcycle.py --Nx 128 --Ny 128 --cycles 5
# ============================================================

from mpi4py import MPI
import numpy as np
import math
import argparse

# ---------------------------
# util: fatoração 2D de size
# ---------------------------
def choose_dims(size: int):
    """Cria um grid 2D de processos [Py, Px] equilibrado."""
    try:
        return MPI.Compute_dims(size, [0, 0])  # [Py, Px]
    except Exception:
        px = int(math.sqrt(size))
        while px > 1 and size % px != 0:
            px -= 1
        py = size // px
        return [py, px]

# --------------------------------
# construir comunicador cartesiano
# --------------------------------
def make_cart_comm(comm: MPI.Comm):
    dims = choose_dims(comm.Get_size())            # [Py, Px]
    periods = [False, False]                       # não-periódico
    comm2d = comm.Create_cart(dims, periods=periods, reorder=True)
    coords = comm2d.Get_coords(comm2d.Get_rank())  # [y, x]
    return comm2d, dims, coords

# ---------------------------------
# malha local + alocação
# ---------------------------------
def local_shape(Nx: int, Ny: int, dims, coords):
    Py, Px = dims
    assert Nx % Px == 0 and Ny % Py == 0, "Nx/Ny devem ser divisíveis por Px/Py."
    nx = Nx // Px
    ny = Ny // Py
    return nx, ny  # interior (sem halos)

def alloc_with_halos(nxi: int, nyi: int):
    """Aloca array com halos (ghosts): (nyi+2, nxi+2)."""
    return np.zeros((nyi + 2, nxi + 2), dtype=np.float64)

# --------------------------
# TROCA DE HALOS (sem deadlock)
# --------------------------
def exchange_halos(u: np.ndarray, comm2d: MPI.Cartcomm, tagbase: int = 100):
    """
    Troca 4 fronteiras (W,E,N,S) com Sendrecv.
    Padrão seguro:
      1) send->LEFT , recv<-RIGHT  (preenche ghost EAST)
      2) send->RIGHT, recv<-LEFT   (preenche ghost WEST)
      3) send->UP   , recv<-DOWN   (preenche ghost SOUTH)
      4) send->DOWN , recv<-UP     (preenche ghost NORTH)
    """
    ny = u.shape[0] - 2  # linhas do interior
    nx = u.shape[1] - 2  # colunas do interior

    # --- Eixo X (colunas)
    left, right = comm2d.Shift(1, +1)  # source=left, dest=right

    # (1) recebe da direita -> preenche EAST
    if right != MPI.PROC_NULL:
        send_col = u[1:-1, 1].copy()         # 1ª coluna interior (vai para o vizinho da ESQUERDA)
        recv_col = np.empty(ny, dtype=u.dtype)
        comm2d.Sendrecv(sendbuf=send_col, dest=left,  sendtag=tagbase+0,
                        recvbuf=recv_col, source=right, recvtag=tagbase+0)
        u[1:-1, -1] = recv_col               # ghost EAST
    else:
        u[1:-1, -1] = 0.0

    # (2) recebe da esquerda -> preenche WEST
    if left != MPI.PROC_NULL:
        send_col = u[1:-1, -2].copy()        # última coluna interior (vai para o vizinho da DIREITA)
        recv_col = np.empty(ny, dtype=u.dtype)
        comm2d.Sendrecv(sendbuf=send_col, dest=right, sendtag=tagbase+1,
                        recvbuf=recv_col, source=left,  recvtag=tagbase+1)
        u[1:-1, 0] = recv_col                # ghost WEST
    else:
        u[1:-1, 0] = 0.0

    # --- Eixo Y (linhas)
    up, down = comm2d.Shift(0, +1)  # source=up, dest=down

    # (3) recebe de baixo -> preenche SOUTH
    if down != MPI.PROC_NULL:
        send_row = u[1, 1:-1].copy()         # 1ª linha interior (vai para o vizinho de CIMA)
        recv_row = np.empty(nx, dtype=u.dtype)
        comm2d.Sendrecv(sendbuf=send_row, dest=up,   sendtag=tagbase+2,
                        recvbuf=recv_row, source=down, recvtag=tagbase+2)
        u[-1, 1:-1] = recv_row               # ghost SOUTH
    else:
        u[-1, 1:-1] = 0.0

    # (4) recebe de cima -> preenche NORTH
    if up != MPI.PROC_NULL:
        send_row = u[-2, 1:-1].copy()        # última linha interior (vai para o vizinho de BAIXO)
        recv_row = np.empty(nx, dtype=u.dtype)
        comm2d.Sendrecv(sendbuf=send_row, dest=down, sendtag=tagbase+3,
                        recvbuf=recv_row, source=up,   recvtag=tagbase+3)
        u[0, 1:-1] = recv_row                # ghost NORTH
    else:
        u[0, 1:-1] = 0.0

# --------------------------
# operador A u (5 pontos)
# --------------------------
def apply_A(u: np.ndarray, h2inv: float):
    """A u = (-4 u + somavizinhos) / h^2   (equivale a -∇² u) — usa apenas interior."""
    return ( -4.0 * u[1:-1,1:-1]
             + u[1:-1,2:] + u[1:-1,:-2] + u[2:,1:-1] + u[:-2,1:-1] ) * h2inv

# --------------------------
# resíduo r = f - A u
# --------------------------
def residual(u: np.ndarray, f_int: np.ndarray, h2inv: float):
    return f_int - apply_A(u, h2inv)

# --------------------------
# suavização: Jacobi relaxado (CORRIGIDO: sinal do f)
# --------------------------
def jacobi(u: np.ndarray, f_int: np.ndarray, h2: float, omega: float, iters: int, comm2d: MPI.Cartcomm):
    """
    Atualiza u (in-place) com Jacobi relaxado.
      u_new = (1-ω) u + ω * ( (soma_vizinhos - h^2 f) / 4 )
    """
    for _ in range(iters):
        exchange_halos(u, comm2d)            # halos atualizados antes de usar vizinhos
        un = u.copy()
        u[1:-1,1:-1] = (1.0 - omega) * un[1:-1,1:-1] + \
                       omega * ( (un[1:-1,2:] + un[1:-1,:-2]
                                  + un[2:,1:-1] + un[:-2,1:-1] - h2 * f_int) * 0.25 )

# --------------------------
# restrição (full-weighting 2D)
# --------------------------
def restrict_full_weighting(r: np.ndarray):
    """
    r: resíduo fino (com halos)
    rc: resíduo grosso (com halos), interior metade
    (1/16)*(4 centro + 2 ortogonais + 1 diagonais)
    """
    nyf = r.shape[0] - 2
    nxf = r.shape[1] - 2
    nyc = nyf // 2
    nxc = nxf // 2
    rc = np.zeros((nyc + 2, nxc + 2), dtype=r.dtype)
    for I in range(1, nyc+1):
        i = 2 * I
        for J in range(1, nxc+1):
            j = 2 * J
            rc[I,J] = ( 4.0 * r[i, j]
                       + 2.0 * ( r[i-1, j] + r[i+1, j] + r[i, j-1] + r[i, j+1] )
                       +       ( r[i-1, j-1] + r[i-1, j+1] + r[i+1, j-1] + r[i+1, j+1] )
                      ) / 16.0
    return rc

# --------------------------
# prolongamento (bilinear)
# --------------------------
def prolong_bilinear(ec: np.ndarray, nxf: int, nyf: int):
    """Interp. bilinear da correção do nível grosso (ec) para o fino (ef)."""
    ef = np.zeros((nyf + 2, nxf + 2), dtype=ec.dtype)
    nyc = ec.shape[0] - 2
    nxc = ec.shape[1] - 2
    for I in range(0, nyc+1):
        for J in range(0, nxc+1):
            eIJ   = ec[I,   J]
            eI1J  = ec[I+1, J]
            eIJ1  = ec[I,   J+1]
            eI1J1 = ec[I+1, J+1]
            i = 2 * I
            j = 2 * J
            ef[i,   j]   += eIJ
            ef[i+1, j]   += 0.5*(eIJ + eI1J)
            ef[i,   j+1] += 0.5*(eIJ + eIJ1)
            ef[i+1, j+1] += 0.25*(eIJ + eI1J + eIJ1 + eI1J1)
    return ef

# --------------------------
# um ciclo-V recursivo
# --------------------------
def v_cycle(u: np.ndarray, f_int: np.ndarray, h: float, comm2d: MPI.Cartcomm,
            nu1: int = 3, nu2: int = 3, omega: float = 2/3, level: int = 0):
    """Executa 1 ciclo-V no nível atual (u,f)."""
    h2 = h*h
    h2inv = 1.0 / h2
    ny = u.shape[0] - 2
    nx = u.shape[1] - 2

    # Base: subdomínio muito pequeno → só suaviza mais
    if nx < 4 or ny < 4:
        jacobi(u, f_int, h2, omega, iters=20, comm2d=comm2d)
        return

    # 1) pré-suavização
    jacobi(u, f_int, h2, omega, iters=nu1, comm2d=comm2d)

    # 2) resíduo e restrição
    exchange_halos(u, comm2d)             # garante halos atualizados
    r = residual(u, f_int, h2inv)         # interior
    r_full = np.zeros_like(u)
    r_full[1:-1,1:-1] = r
    rc = restrict_full_weighting(r_full)

    # 3) resolve no nível grosso (recursivo)
    hc = 2.0*h
    ec = np.zeros_like(rc)                # correção no grosso
    v_cycle(ec, rc[1:-1,1:-1], hc, comm2d, nu1, nu2, omega, level+1)

    # 4) prolonga e corrige
    ef = prolong_bilinear(ec, nx, ny)
    u[1:-1,1:-1] += ef[1:-1,1:-1]

    # 5) pós-suavização
    jacobi(u, f_int, h2, omega, iters=nu2, comm2d=comm2d)

# --------------------------
# norma global do resíduo
# --------------------------
def global_residual_norm(u: np.ndarray, f_int: np.ndarray, h: float, comm2d: MPI.Cartcomm):
    h2inv = 1.0/(h*h)
    exchange_halos(u, comm2d, tagbase=300)
    rloc = residual(u, f_int, h2inv)
    loc = float(np.sum(rloc * rloc))
    tot = comm2d.allreduce(loc, op=MPI.SUM)
    return math.sqrt(tot)

# --------------------------
# main
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Multigrid 2D (ciclo-V) com mpi4py — exemplo acadêmico (sem deadlock)")
    parser.add_argument("--Nx", type=int, default=128, help="pontos interiores em X (global)")
    parser.add_argument("--Ny", type=int, default=128, help="pontos interiores em Y (global)")
    parser.add_argument("--cycles", type=int, default=5, help="quantidade de ciclos-V")
    parser.add_argument("--nu1", type=int, default=3, help="pré-suavizações por nível")
    parser.add_argument("--nu2", type=int, default=3, help="pós-suavizações por nível")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # comunicador cartesiano
    comm2d, dims, coords = make_cart_comm(comm)
    Py, Px = dims
    Ny, Nx = args.Ny, args.Nx

    # shapes locais
    nxi, nyi = local_shape(Nx, Ny, dims, coords)
    if (nxi % 2 != 0) or (nyi % 2 != 0):
        if rank == 0:
            print("Aviso: nxi/nyi deveriam ser pares para coarsening limpo. Ajuste Nx/Ny e o grid de processos.")

    # passo de malha (uniforme em [0,1])
    hx = 1.0 / (Nx + 1)
    hy = 1.0 / (Ny + 1)
    assert abs(hx - hy) < 1e-12, "Este exemplo assume hx==hy. Use Nx==Ny para simplificar."
    h = hx

    # campos com halos
    u = alloc_with_halos(nxi, nyi)                   # chute inicial: zeros
    f = np.zeros((nyi+2, nxi+2), dtype=np.float64)
    f[1:-1,1:-1] = 1.0                               # fonte constante (didático)

    # norma inicial
    r0 = global_residual_norm(u, f[1:-1,1:-1], h, comm2d)
    if rank == 0:
        print(f"[L0]  ||r||2 = {r0:.6e}  | Px x Py = {Px} x {Py} | n_local = {nxi}x{nyi}")

    # ciclos-V
    for k in range(1, args.cycles+1):
        v_cycle(u, f[1:-1,1:-1], h, comm2d, nu1=args.nu1, nu2=args.nu2, omega=2/3, level=0)
        rk = global_residual_norm(u, f[1:-1,1:-1], h, comm2d)
        if rank == 0:
            print(f"[V-cycle {k}] ||r||2 = {rk:.6e}  (fator {rk/max(r0,1e-30):.3e} vs. inicial)")

    # amostra (opcional)
    if rank == 0:
        nyc, nxc = u.shape[0]//2, u.shape[1]//2
        print(f"[rank 0] amostra u[centro-1:centro+2, centro-1:centro+2]:\n{u[nyc-1:nyc+2, nxc-1:nxc+2]}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

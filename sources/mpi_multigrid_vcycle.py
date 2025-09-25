# mpi_multigrid_vcycle.py
# ============================================================
# Exemplo acadêmico de Multigrid (Ciclo-V) 2D com mpi4py
# mpiexec -n 4 python3 mpi_multigrid_vcycle.py --Nx 128 --Ny 128 --cycles 5
#
# ------------------------------------------------------------
# Problema: -∇² u = f em [0,1]x[0,1], u = 0 nas bordas (Dirichlet)
#
# Como funciona (visão didática):
# 1) Discretizamos com stencil 5-pontos: 
#       (-4*u[i,j] + u[i±1,j] + u[i,j±1]) / h^2 = f[i,j]
# 2) Particionamos a malha em um grid 2D de processos (MPI Cartesiano).
#    Cada rank mantém um subdomínio com células de halo (ghost cells).
# 3) Um ciclo-V faz:
#    - ν1 iterações de suavização (Jacobi relaxado) no nível atual
#    - computa o resíduo r = f − A u e o "restringe" (full-weighting) p/ a malha 2x mais grossa
#    - resolve aproximadamente o erro no nível grosso (recursivo)
#    - "prolonga" (bilinear) a correção de volta p/ a malha fina e corrige u
#    - ν2 iterações de suavização no nível fino após a correção
# 4) Comunicação:
#    - Em cada suavização: troca de halos com vizinhos (N, S, L, O) via MPI_Sendrecv.
#    - Norma global do resíduo: MPI.Allreduce (soma global).
#
# Requisitos e suposições para simplificar:
# - Nx, Ny divisíveis pelas dimensões de processos (Px, Py).
# - Nx_local e Ny_local devem ser pares para permitir coarsening (dividir por 2).
# - Rodar com N que permita pelo menos 2-3 níveis (ex.: 64, 128, 256, ...).
#
# Execução:
#   mpiexec -n 4 python mpi_multigrid_vcycle.py --Nx 128 --Ny 128 --cycles 5
#
# Saída (rank 0):
#   [L0] ||r||2 = ...
#   [V-cycle 1] ||r||2 = ...
#   ...
# Comentários “para sala de aula” estão marcados ao longo do código.
# ============================================================

from mpi4py import MPI
import numpy as np
import math
import argparse

# ---------------------------
# util: fatoração 2D de size
# ---------------------------
def choose_dims(size):
    """
    Tenta criar um grid 2D de processos Px x Py "equilibrado".
    Se MPI.Compute_dims existir, usamos; caso contrário, fatoramos manualmente.
    """
    try:
        # mpi4py geralmente expõe Compute_dims
        dims = MPI.Compute_dims(size, [0, 0])
        return dims  # [Py, Px]
    except Exception:
        # fallback simples: pega fator inteiro mais próximo da raiz
        px = int(math.sqrt(size))
        while px > 1 and size % px != 0:
            px -= 1
        py = size // px
        return [py, px]  # [Py, Px]

# --------------------------------
# construir comunicador cartesiano
# --------------------------------
def make_cart_comm(comm):
    size = comm.Get_size()
    dims = choose_dims(size)          # dims = [Py, Px]
    periods = [False, False]          # não periódica
    comm2d = comm.Create_cart(dims, periods=periods, reorder=True)
    coords = comm2d.Get_coords(comm2d.Get_rank())  # [y, x]
    # vizinhos (N,S) na dimensão 0 (linhas), (W,E) na dimensão 1 (colunas)
    srcN, dstS = comm2d.Shift(0, -1)  # subir/ descer
    srcS, dstN = comm2d.Shift(0, +1)
    srcW, dstE = comm2d.Shift(1, -1)  # esquerda/ direita
    srcE, dstW = comm2d.Shift(1, +1)
    nbrs = dict(N=srcN, S=srcS, W=srcW, E=srcE, sendN=dstN, sendS=dstS, sendW=dstW, sendE=dstE)
    return comm2d, dims, coords, nbrs

# ---------------------------------
# criação de malha local + parâmetros
# ---------------------------------
def local_shape(Nx, Ny, dims, coords):
    Py, Px = dims
    y, x = coords
    assert Nx % Px == 0 and Ny % Py == 0, "Nx/Ny devem ser divisíveis por Px/Py."
    nx = Nx // Px
    ny = Ny // Py
    return nx, ny  # interior (sem halos)

def alloc_with_halos(nxi, nyi):
    """aloca array com halos (ghosts): (nyi+2, nxi+2)"""
    return np.zeros((nyi + 2, nxi + 2), dtype=np.float64)

# --------------------------
# troca de halos com vizinhos
# --------------------------
def exchange_halos(u, comm2d, nbrs, tagbase=100):
    # horizontais (W/E): colunas
    if nbrs["W"] != MPI.PROC_NULL:
        send_col = u[1:-1, 1].copy()           # 1ª coluna interior
        recv_col = np.empty_like(send_col)
        comm2d.Sendrecv(send_col, dest=nbrs["sendW"], sendtag=tagbase+1,
                        recvbuf=recv_col, source=nbrs["W"], recvtag=tagbase+2)
        u[1:-1, 0] = recv_col                  # enche ghost da esquerda
    else:
        u[1:-1, 0] = 0.0                       # Dirichlet 0 se borda global

    if nbrs["E"] != MPI.PROC_NULL:
        send_col = u[1:-1, -2].copy()          # última coluna interior
        recv_col = np.empty_like(send_col)
        comm2d.Sendrecv(send_col, dest=nbrs["sendE"], sendtag=tagbase+3,
                        recvbuf=recv_col, source=nbrs["E"], recvtag=tagbase+4)
        u[1:-1, -1] = recv_col                 # enche ghost da direita
    else:
        u[1:-1, -1] = 0.0

    # verticais (N/S): linhas
    if nbrs["N"] != MPI.PROC_NULL:
        send_row = u[1, 1:-1].copy()           # 1ª linha interior
        recv_row = np.empty_like(send_row)
        comm2d.Sendrecv(send_row, dest=nbrs["sendN"], sendtag=tagbase+5,
                        recvbuf=recv_row, source=nbrs["N"], recvtag=tagbase+6)
        u[0, 1:-1] = recv_row                  # ghost de cima
    else:
        u[0, 1:-1] = 0.0

    if nbrs["S"] != MPI.PROC_NULL:
        send_row = u[-2, 1:-1].copy()          # última linha interior
        recv_row = np.empty_like(send_row)
        comm2d.Sendrecv(send_row, dest=nbrs["sendS"], sendtag=tagbase+7,
                        recvbuf=recv_row, source=nbrs["S"], recvtag=tagbase+8)
        u[-1, 1:-1] = recv_row                 # ghost de baixo
    else:
        u[-1, 1:-1] = 0.0

# --------------------------
# operador A u (5 pontos)
# --------------------------
def apply_A(u, h2inv):
    """
    Retorna Au (somente interior). Assumimos fantasmas já atualizados.
    A u = (-4 u + somavizinhos) / h^2   (equivale a -∇² u)
    """
    return ( -4.0 * u[1:-1,1:-1]
             + u[1:-1,2:] + u[1:-1,:-2] + u[2:,1:-1] + u[:-2,1:-1] ) * h2inv

# --------------------------
# resíduo r = f - A u
# --------------------------
def residual(u, f, h2inv):
    return f - apply_A(u, h2inv)

# --------------------------
# suavização: Jacobi relaxado
# --------------------------
def jacobi(u, f, h2, omega, iters, comm2d, nbrs):
    """
    Atualiza u (in-place) com Jacobi relaxado.
    Fórmula de atualização:
        u_new = (1-ω) u + ω * ( (h^2 f + somavizinhos) / 4 )
    """
    for _ in range(iters):
        exchange_halos(u, comm2d, nbrs)
        un = u.copy()
        u[1:-1,1:-1] = (1.0 - omega) * un[1:-1,1:-1] + \
                       omega * ( (h2 * f + un[1:-1,2:] + un[1:-1,:-2] + un[2:,1:-1] + un[:-2,1:-1]) * 0.25 )

# --------------------------
# restrição (full-weighting 2D)
# --------------------------
def restrict_full_weighting(r):
    """
    r: resíduo no nível fino (com halos)
    retorna rc: resíduo no nível grosso (com halos), interior metade
    Fórmula padrão 2D (1/16)*(4 centro + 2 ortogonais + 1 diagonais)
    """
    nyf = r.shape[0] - 2
    nxf = r.shape[1] - 2
    nyc = nyf // 2
    nxc = nxf // 2
    rc = np.zeros((nyc + 2, nxc + 2), dtype=r.dtype)
    # mapeamento: ponto grosso (I,J) corresponde ao fino (2I,2J)
    # laços simples (didático)
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
def prolong_bilinear(ec, nxf, nyf):
    """
    ec: correção no nível grosso (com halos)
    retorna ef: correção no nível fino (com halos), interior tamanho nxf x nyf.
    Interp. bilinear clássica (injeção + médias).
    """
    ef = np.zeros((nyf + 2, nxf + 2), dtype=ec.dtype)
    nyc = ec.shape[0] - 2
    nxc = ec.shape[1] - 2
    # preencher pontos finos a partir dos grossos e seus vizinhos
    for I in range(0, nyc+1):
        for J in range(0, nxc+1):
            # valores em ec usando halos para I,J e vizinhos
            eIJ   = ec[I,   J]
            eI1J  = ec[I+1, J]
            eIJ1  = ec[I,   J+1]
            eI1J1 = ec[I+1, J+1]
            # mapa para fino (2I,2J)
            i = 2 * I
            j = 2 * J
            # injeção
            ef[i, j] += eIJ
            # interpolação nas direções
            ef[i+1, j]   += 0.5*(eIJ + eI1J)
            ef[i,   j+1] += 0.5*(eIJ + eIJ1)
            # interpolação no centro do quadrante
            ef[i+1, j+1] += 0.25*(eIJ + eI1J + eIJ1 + eI1J1)
    # recorta ponto além do interior (se laço tocou a borda do halo)
    return ef

# --------------------------
# um ciclo-V recursivo
# --------------------------
def v_cycle(u, f, h, comm2d, nbrs, nu1=3, nu2=3, omega=2/3, level=0):
    """
    Executa 1 ciclo-V no nível atual (u,f), depois retorna u corrigido.
    """
    rank = comm2d.Get_rank()
    h2 = h*h
    h2inv = 1.0 / h2
    ny = u.shape[0] - 2
    nx = u.shape[1] - 2

    # critério de parada (nível muito pequeno): “resolve” com suavizações extras
    if nx < 4 or ny < 4:
        jacobi(u, f, h2, omega, iters=20, comm2d=comm2d, nbrs=nbrs)
        return

    # 1) pré-suavização
    jacobi(u, f, h2, omega, iters=nu1, comm2d=comm2d, nbrs=nbrs)

    # 2) resíduo e restrição
    exchange_halos(u, comm2d, nbrs)                 # garante halos atualizados
    r = residual(u, f, h2inv)                       # interior
    # construir array com halos para r (para restrição usar índices coerentes)
    r_full = np.zeros_like(u)
    r_full[1:-1,1:-1] = r
    rc = restrict_full_weighting(r_full)            # resíduo no nível grosso

    # 3) resolver no nível grosso: A ec = rc (aproximado)
    nyc = rc.shape[0] - 2
    nxc = rc.shape[1] - 2
    hc = 2.0*h

    # aloca u_correção no grosso (com halos); inicia com zero
    ec = np.zeros_like(rc)

    # halos de ec são 0 nas bordas globais (Dirichlet). trocaremos halos durante suavização.
    v_cycle(ec, rc[1:-1,1:-1], hc, comm2d, nbrs, nu1, nu2, omega, level+1)

    # 4) prolongar correção e somar
    ef = prolong_bilinear(ec, nx, ny)
    u[1:-1,1:-1] += ef[1:-1,1:-1]

    # 5) pós-suavização
    jacobi(u, f, h2, omega, iters=nu2, comm2d=comm2d, nbrs=nbrs)

# --------------------------
# norma global do resíduo
# --------------------------
def global_residual_norm(u, f, h, comm2d):
    h2inv = 1.0/(h*h)
    exchange_halos(u, comm2d, nbrs=None_or_dummy(comm2d), tagbase=300)  # usa vizinhos corretos
    rloc = residual(u, f, h2inv)
    loc = float(np.sum(rloc**2))
    tot = comm2d.allreduce(loc, op=MPI.SUM)
    return math.sqrt(tot)

def None_or_dummy(comm2d):
    # helper para reutilizar exchange_halos na checagem de resíduo
    # recupera novamente vizinhos a partir do comunicador
    rank = comm2d.Get_rank()
    srcN, dstS = comm2d.Shift(0, -1)
    srcS, dstN = comm2d.Shift(0, +1)
    srcW, dstE = comm2d.Shift(1, -1)
    srcE, dstW = comm2d.Shift(1, +1)
    return dict(N=srcN, S=srcS, W=srcW, E=srcE, sendN=dstN, sendS=dstS, sendW=dstW, sendE=dstE)

# --------------------------
# main
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Multigrid 2D (ciclo-V) com mpi4py — exemplo acadêmico")
    parser.add_argument("--Nx", type=int, default=128, help="número de pontos interiores em X (por todo o domínio)")
    parser.add_argument("--Ny", type=int, default=128, help="número de pontos interiores em Y (por todo o domínio)")
    parser.add_argument("--cycles", type=int, default=5, help="quantidade de ciclos-V")
    parser.add_argument("--nu1", type=int, default=3, help="pré-suavizações por nível")
    parser.add_argument("--nu2", type=int, default=3, help="pós-suavizações por nível")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # comunicador cartesiano e vizinhos
    comm2d, dims, coords, nbrs = make_cart_comm(comm)
    Py, Px = dims
    Ny, Nx = args.Ny, args.Nx

    # shapes locais
    nxi, nyi = local_shape(Nx, Ny, dims, coords)
    if nxi % 2 != 0 or nyi % 2 != 0:
        if rank == 0:
            print("Aviso: nxi/nyi deveriam ser pares para coarsening limpo. Ajuste Nx/Ny e número de processos.")
        # seguimos assim mesmo, mas níveis de coarsening podem parar cedo.

    # passo de malha global (espacamento uniforme em [0,1])
    hx = 1.0 / (Nx + 1)
    hy = 1.0 / (Ny + 1)
    assert abs(hx - hy) < 1e-12, "Exemplo assume hx==hy. Use Nx==Ny para simplificar."
    h = hx

    # aloca u e f (com halos)
    u = alloc_with_halos(nxi, nyi)  # chute inicial: zeros
    f = np.zeros((nyi+2, nxi+2), dtype=np.float64)

    # força fonte f=1 no interior (didático); solução analítica não é usada
    f[1:-1,1:-1] = 1.0

    # norma inicial do resíduo
    # (usa um helper que refaz info de vizinhos para evitar dependência global)
    r0 = global_residual_norm(u, f[1:-1,1:-1], h, comm2d)
    if rank == 0:
        print(f"[L0]  ||r||2 = {r0:.6e}  (inicial)  | Px x Py = {Px} x {Py} | n_local = {nxi}x{nyi}")

    # aplica alguns ciclos-V
    for k in range(1, args.cycles+1):
        v_cycle(u, f[1:-1,1:-1], h, comm2d, nbrs, nu1=args.nu1, nu2=args.nu2, omega=2/3, level=0)
        rk = global_residual_norm(u, f[1:-1,1:-1], h, comm2d)
        if rank == 0:
            print(f"[V-cycle {k}] ||r||2 = {rk:.6e}  (fator {rk/max(r0,1e-30):.3e} vs. inicial)")

    # imprime pequena amostra do centro do subdomínio do rank 0 (opcional)
    if rank == 0:
        nyc, nxc = u.shape[0]//2, u.shape[1]//2
        print(f"[rank 0] amostra u[centro-1:centro+2, centro-1:centro+2]:\n{u[nyc-1:nyc+2, nxc-1:nxc+2]}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

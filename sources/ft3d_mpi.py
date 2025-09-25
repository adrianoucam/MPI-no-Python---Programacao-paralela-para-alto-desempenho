# ft3d_mpi.py
# ------------------------------------------------------------
# FT acadêmico: FFT 3D distribuída (slab e pencil)
# - Transposições com MPI Alltoall
# - Checagens globais com Allreduce
#
# Execução:
#   # modo slab (P processos, Py=P, Px=1)
#   mpiexec -n 4 python ft3d_mpi.py --Nx 128 --Ny 128 --Nz 128 --mode slab
#
#   # modo pencil (2D): tenta fatorar P≈Py*Px automaticamente
#   mpiexec -n 8 python ft3d_mpi.py --Nx 128 --Ny 128 --Nz 128 --mode pencil
#   # ou escolhendo grade:
#   mpiexec -n 8 python ft3d_mpi.py --Nx 128 --Ny 128 --Nz 128 --mode pencil --py 4 --px 2
# ------------------------------------------------------------

from mpi4py import MPI
import numpy as np
import argparse
import math

def compute_dims(size, py=None, px=None):
    """Escolhe (Py, Px) para a grade 2D de processos."""
    if py and px:
        assert py * px == size, "py * px deve ser igual ao número total de processos"
        return py, px
    # tenta fatorar em algo próximo de um quadrado
    px = int(math.sqrt(size))
    while px > 1 and size % px != 0:
        px -= 1
    py = size // px
    return py, px

def init_local_data(Nz, Ny, Nx, z0, y0, dz, dy):
    """
    Dados determinísticos para teste (complex128):
    u[z,y,x] = exp( 2πi * (z/Nz + y/Ny + x/Nx) )
    """
    zz = (np.arange(dz) + z0)[:, None, None] / Nz
    yy = (np.arange(dy) + y0)[None, :, None] / Ny
    xx = np.arange(Nx)[None, None, :] / Nx
    phase = zz + yy + xx
    return np.exp(2j * np.pi * phase).astype(np.complex128)

def global_l2(u_local, comm):
    """||u||_2 global, via soma de quadrados e Allreduce."""
    loc = float(np.sum(np.abs(u_local)**2))
    tot = comm.allreduce(loc, op=MPI.SUM)
    return math.sqrt(tot)

# ====== TRANSFORMADAS: MODO PENCIL (geral, inclui SLAB como caso particular) ======

def fft3d_forward_pencil(u_local, Nz, Ny, Nx, Py, Px, comm2d, row_comm, col_comm):
    """
    Decomposição:
      - Py divide Z (linhas da grade de processos)
      - Px divide Y (colunas da grade de processos)
      - X é local inicialmente
    Pipeline:
      1) FFT em X (local)
      2) Alltoall em row_comm (entre colunas) para reunir Y completo e dividir X
      3) FFT em Y (local)
      4) Alltoall em col_comm (entre linhas) para reunir Z completo e dividir Y
      5) FFT em Z (local)
    Retorna o array no layout final: (Nz, Ny//Py, Nx//Px) por processo.
    """
    dz = u_local.shape[0]                  # Nz // Py
    dy = u_local.shape[1]                  # Ny // Px
    dx = u_local.shape[2]                  # Nx        (local antes da 1ª troca)
    assert dx % Px == 0, "Nx deve ser múltiplo de Px"
    dxc = dx // Px
    # 1) FFT em X
    u_local = np.fft.fft(u_local, axis=2)

    # 2) Alltoall em row_comm (entre colunas) — reparticiona X, junta Y
    # Prepara buffers [Px, dz*dy*dxc]
    send = u_local.reshape(dz, dy, Px, dxc).swapaxes(1, 2)            # (dz, Px, dy, dxc)
    sbuf = send.reshape(Px, -1).copy()
    rbuf = np.empty_like(sbuf)
    row_comm.Alltoall([sbuf, MPI.COMPLEX16], [rbuf, MPI.COMPLEX16])
    # Recebidos Px blocos: concatena no eixo Y → (dz, Ny, dxc)
    recv = rbuf.reshape(Px, dz, dy, dxc)
    u_y = np.concatenate([recv[i] for i in range(Px)], axis=1)        # (dz, Ny, dxc)

    # 3) FFT em Y
    u_y = np.fft.fft(u_y, axis=1)

    # 4) Alltoall em col_comm (entre linhas) — reparticiona Y, junta Z
    assert Ny % Py == 0, "Ny deve ser múltiplo de Py"
    ypc = Ny // Py
    send2 = u_y.reshape(dz, Py, ypc, dxc).swapaxes(0, 1)              # (Py, dz, ypc, dxc)
    sbuf2 = send2.reshape(Py, -1).copy()
    rbuf2 = np.empty_like(sbuf2)
    col_comm.Alltoall([sbuf2, MPI.COMPLEX16], [rbuf2, MPI.COMPLEX16])
    # Recebidos Py blocos: concatena no eixo Z → (Nz, ypc, dxc)
    recv2 = rbuf2.reshape(Py, dz, ypc, dxc)
    u_z = np.concatenate([recv2[i] for i in range(Py)], axis=0)       # (Nz, Ny//Py, Nx//Px)

    # 5) FFT em Z
    u_z = np.fft.fft(u_z, axis=0)
    return u_z  # layout final (Nz, Ny//Py, Nx//Px)

def fft3d_inverse_pencil(U_local, Nz, Ny, Nx, Py, Px, comm2d, row_comm, col_comm):
    """
    Inversa do pipeline acima (em ordem reversa).
    Entrada: layout (Nz, Ny//Py, Nx//Px)
    Saída:  layout original (Nz//Py, Ny//Px, Nx)
    """
    Nz_loc_full, ypc, dxc = U_local.shape
    assert Nz_loc_full == Nz
    # 1) IFFT em Z
    u = np.fft.ifft(U_local, axis=0)

    # 2) Alltoall inverso em col_comm: repartir Z e juntar Y
    dz = Nz // Py
    send = u.reshape(Py, dz, ypc, dxc)                                   # (Py, dz, ypc, dxc)
    sbuf = send.reshape(Py, -1).copy()
    rbuf = np.empty_like(sbuf)
    col_comm.Alltoall([sbuf, MPI.COMPLEX16], [rbuf, MPI.COMPLEX16])
    recv = rbuf.reshape(Py, dz, ypc, dxc)
    u_y = np.concatenate([recv[i] for i in range(Py)], axis=1)           # (dz, Ny, dxc)

    # 3) IFFT em Y
    u_y = np.fft.ifft(u_y, axis=1)

    # 4) Alltoall inverso em row_comm: repartir Y e juntar X completo
    dy = Ny // Px
    send2 = u_y.reshape(dz, Px, dy, dxc).swapaxes(1, 0)                  # (Px, dz, dy, dxc) após swap
    # cuidado: swapaxes(1,0) muda ordem; melhor construir explicitamente:
    send2 = u_y.reshape(dz, Ny, dxc)
    # fatia Y em Px blocos e monta lista para concat em X
    parts = [send2[:, i*dy:(i+1)*dy, :] for i in range(Px)]              # Px blocos (dz, dy, dxc)
    sbuf2 = np.stack(parts, axis=0).reshape(Px, -1).copy()               # (Px, dz*dy*dxc)
    rbuf2 = np.empty_like(sbuf2)
    row_comm.Alltoall([sbuf2, MPI.COMPLEX16], [rbuf2, MPI.COMPLEX16])
    recv2 = rbuf2.reshape(Px, dz, dy, dxc)
    u_x = np.concatenate([recv2[i] for i in range(Px)], axis=2)          # (dz, dy, Px*dxc) = (dz, dy, Nx)

    # 5) IFFT em X
    u_x = np.fft.ifft(u_x, axis=2)
    return u_x  # layout original (Nz//Py, Ny//Px, Nx)

def main():
    ap = argparse.ArgumentParser(description="FFT 3D distribuída (slab/pencil) com Alltoall/Allreduce — mpi4py")
    ap.add_argument("--Nx", type=int, default=128)
    ap.add_argument("--Ny", type=int, default=128)
    ap.add_argument("--Nz", type=int, default=128)
    ap.add_argument("--mode", choices=["slab","pencil"], default="slab")
    ap.add_argument("--py", type=int, default=None, help="process rows (Py) para modo pencil")
    ap.add_argument("--px", type=int, default=None, help="process cols (Px) para modo pencil")
    args = ap.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Define (Py, Px)
    if args.mode == "slab":
        Py, Px = size, 1              # slab em Z
    else:
        Py, Px = compute_dims(size, args.py, args.px)

    assert Py * Px == size

    # Comunicador cartesiano 2D (linhas=Py, colunas=Px)
    comm2d = comm.Create_cart(dims=[Py, Px], periods=[False, False], reorder=True)
    coords = comm2d.Get_coords(comm2d.Get_rank())  # (row, col) = (along Z, along Y)
    row_comm = comm2d.Sub((False, True))           # mesma linha (varia coluna)
    col_comm = comm2d.Sub((True, False))           # mesma coluna (varia linha)

    Nz, Ny, Nx = args.Nz, args.Ny, args.Nx
    # Checagens de divisibilidade (didáticas para usar Alltoall simples)
    assert Nz % Py == 0, "Nz deve ser múltiplo de Py"
    assert Ny % Px == 0, "Ny deve ser múltiplo de Px"
    assert Nx % Px == 0, "Nx deve ser múltiplo de Px (para a 1a transposição)"
    if args.mode == "slab":
        # nosso pipeline slab usa Ny%Py também (2a transposição)
        assert Ny % Py == 0, "No modo slab requeremos Ny múltiplo de P (=Py)"

    dz = Nz // Py
    dy = Ny // Px
    z0 = coords[0] * dz
    y0 = coords[1] * dy

    # Dados locais (layout inicial: (dz, dy, Nx))
    u0 = init_local_data(Nz, Ny, Nx, z0, y0, dz, dy)

    # Normas (Allreduce) — antes da FFT
    n0 = global_l2(u0, comm)

    comm.Barrier()
    t0 = MPI.Wtime()
    U = fft3d_forward_pencil(u0.copy(), Nz, Ny, Nx, Py, Px, comm2d, row_comm, col_comm)
    comm.Barrier()
    t1 = MPI.Wtime()

    # Inversa
    u_rec = fft3d_inverse_pencil(U, Nz, Ny, Nx, Py, Px, comm2d, row_comm, col_comm)
    comm.Barrier()
    t2 = MPI.Wtime()

    # Checagens globais
    n1 = global_l2(u_rec, comm)                  # deve ser ≈ n0 (até fator de normalização do FFT)
    # erro máximo local
    err_loc = float(np.max(np.abs(u_rec - u0)))
    err_glob = comm.allreduce(err_loc, op=MPI.MAX)

    if rank == 0:
        print(f"[FT3D] modo={args.mode}  P={size}  Py={Py} Px={Px}  N=({Nz},{Ny},{Nx})")
        print(f"  Tempo forward : {t1 - t0:0.6f} s")
        print(f"  Tempo inverse : {t2 - t1:0.6f} s")
        print(f"  ||u0||_2={n0:0.6e}  ||u_rec||_2={n1:0.6e}  (dif={abs(n1-n0):.3e})")
        print(f"  erro max |u_rec - u0| = {err_glob:.3e}")

    MPI.Finalize()

if __name__ == "__main__":
    main()

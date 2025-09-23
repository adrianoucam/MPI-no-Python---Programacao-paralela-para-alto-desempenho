# mpi_particulas_criancas.py
# Explicação para jovens:
# - Cada "partícula" é uma ficha com x, y, z, velocidade (floats) e n, tipo (ints).
# - O Líder (rank 0) cria 25 partículas e preenche os campos.
# - Com um broadcast (Bcast), todas as crianças recebem o mesmo conjunto de partículas.
# - Usamos um "tipo derivado" do MPI para descrever o layout da ficha na memória.

from mpi4py import MPI
import numpy as np

NELEM = 25  # quantidade de partículas (fichas)


# --- só o rank 0 faz gráfico; em ambiente sem tela, salvamos em PNG ---
def desenhar_grafico_por_rank(dados_por_rank, fname="particulas.png"):
    import matplotlib.pyplot as plt

    plt.figure()
    for r, arr in dados_por_rank.items():
        # scatter (x vs y) desse rank; sem especificar cores
        plt.scatter(arr["x"], arr["y"], label=f"Rank {r}", s=40)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Partículas após o deslocamento em cada processo")
    plt.legend()
    # tente mostrar; se falhar (ambiente headless), apenas salva
    try:
        plt.show()
    except Exception:
        plt.savefig(fname, dpi=140)

NELEM = 25

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    root = 0

    # 1) dtype NumPy equivalente ao struct do C 
    dt = np.dtype([
        ("x", "f4"),
        ("y", "f4"),
        ("z", "f4"),
        ("velocidade", "f4"),
        ("n", "i4"),
        ("tipo", "i4"),
    ], align=False)

    # 2) tipo derivado do MPI equivalente (2 blocos: 4 floats, 2 ints)
    _, extent_float = MPI.FLOAT.Get_extent()
    blocklengths  = [4, 2]
    displacements = [0, 4 * extent_float]
    oldtypes      = [MPI.FLOAT, MPI.INT]
    tipo_particula = MPI.Datatype.Create_struct(blocklengths, displacements, oldtypes)
    tipo_particula.Commit()

    # 3) buffers locais
    if rank == root:
        particulas = np.empty(NELEM, dtype=dt)
        for i in range(NELEM):
            particulas["x"][i] = float(i)
            particulas["y"][i] = float(-i)
            particulas["z"][i] = float(i)
            particulas["velocidade"][i] = 0.25
            particulas["n"][i] = i
            particulas["tipo"][i] = i % 2
        # broadcast a partir do root
        comm.Bcast([particulas, NELEM, tipo_particula], root=root)
        local = particulas
    else:
        p = np.empty(NELEM, dtype=dt)
        comm.Bcast([p, NELEM, tipo_particula], root=root)
        local = p

    # 4) “o que aconteceu”: cada processo desloca suas fichas
    #    (um deslocamento simples que depende do rank)
    #    exemplo: dx = 0.2*rank, dy = -0.15*rank, dz = 0.1*rank
    dx = 0.2 * rank
    dy = -0.15 * rank
    dz = 0.1 * rank
    local["x"] = local["x"] + dx
    local["y"] = local["y"] + dy
    local["z"] = local["z"] + dz

    # 5) juntar tudo no rank 0 para visualizar
    if rank == root:
        todos = np.empty(NELEM * size, dtype=dt)
        comm.Gather([local, NELEM, tipo_particula],
                    [todos, NELEM, tipo_particula], root=root)
    else:
        comm.Gather([local, NELEM, tipo_particula],
                    None, root=root)

    # 6) rank 0 organiza por rank e desenha
    if rank == root:
        # separe cada bloco de NELEM pertencente a cada rank
        dados_por_rank = {}
        for r in range(size):
            ini = r * NELEM
            fim = (r + 1) * NELEM
            dados_por_rank[r] = todos[ini:fim]
        # desenhar (x vs y) por rank
        desenhar_grafico_por_rank(dados_por_rank, fname="particulas.png")
        print("Gráfico gerado (x vs y). Se não abriu uma janela, procure por 'particulas.png'.")

    tipo_particula.Free()

if __name__ == "__main__":
    main()
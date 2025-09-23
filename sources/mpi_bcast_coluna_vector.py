# mpi_bcast_coluna_vector_fix.py
# Envia a 2ª coluna (índice 1) de uma matriz 4x4 usando um tipo derivado não contíguo.
# Root usa MPI.BOTTOM + datatype com endereço ABSOLUTO para a coluna.
# Demais ranks recebem em vetor contíguo.

from mpi4py import MPI
import numpy as np

TAM = 4
ROOT = 0

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # --- Tipo derivado: coluna (em bytes) + endereço absoluto ---
    # Cada "bloco" tem 1 float; stride = TAM * sizeof(float)
    float_extent = MPI.FLOAT.Get_extent()[1]  # bytes por float
    stride_bytes = TAM * float_extent

    # hvector descreve: TAM blocos, cada um com 1 float, pulando 'stride_bytes'
    tipo_col_rel = MPI.FLOAT.Create_hvector(TAM, 1, stride_bytes)

    if rank == ROOT:
        # Matriz do enunciado (contígua em memória, float32)
        matriz = np.array(
            [[ 1.0,  2.0,  3.0,  4.0],
             [ 5.0,  6.0,  7.0,  8.0],
             [ 9.0, 10.0, 11.0, 12.0],
             [13.0, 14.0, 15.0, 16.0]], dtype=np.float32)

        # Endereço ABSOLUTO do primeiro elemento da coluna 1 ([0,1])
        base_addr   = MPI.Get_address(matriz)                # addr do [0,0]
        col1_addr   = base_addr + 1 * float_extent          # desloca 1 float

        # “Coluna absoluta” = struct de 1 campo na posição col1_addr com o hvector relativo
        tipo_col_abs = MPI.Datatype.Create_struct([1], [col1_addr], [tipo_col_rel])
        tipo_col_abs.Commit()

        # Broadcast: root envia A PARTIR DE MPI.BOTTOM com o tipo derivado absoluto
        comm.Bcast([MPI.BOTTOM, 1, tipo_col_abs], root=ROOT)

        tipo_col_abs.Free()

    else:
        # Demais processos recebem a coluna em vetor contíguo
        vetor_local = np.empty(TAM, dtype=np.float32)
        comm.Bcast([vetor_local, TAM, MPI.FLOAT], root=ROOT)

        # Mostrar o que chegou
        print(f"Processo {rank} - " + " ".join(
            f"vetor[{i}] = {vetor_local[i]:.1f}" for i in range(TAM)
        ))

    tipo_col_rel.Free()
    MPI.Finalize()

if __name__ == "__main__":
    main()

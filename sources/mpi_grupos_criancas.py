# mpi_grupos_criancas.py
# - Cria dois grupos (listas de ranks), faz a união e cria um novo comunicador.
# - Cada processo imprime seu rank antigo (no mundo) e o novo rank (no grupo unido).
# mpi_grupos_criancas.py
# Dois grupos de crianças (ranks), união dos times e novo "pátio" (comunicador).

from mpi4py import MPI
import sys

NUM_PROCS = 10
RANKS1 = [0, 2, 3, 4, 5, 8]   # time A
RANKS2 = [9, 4, 0, 2, 8]      # time B

def main():
    comm_world = MPI.COMM_WORLD
    rank = comm_world.Get_rank()
    size = comm_world.Get_size()

    if size != NUM_PROCS:
        if rank == 0:
            print(f"Deve especificar o numero de processos igual a {NUM_PROCS}. Terminando.")
        MPI.Finalize()
        sys.exit(1)

    # Grupo do mundo (todas as crianças)
    g_world = comm_world.Get_group()

    # Grupos A e B
    g1 = g_world.Incl(RANKS1)
    g2 = g_world.Incl(RANKS2)

    # União correta em mpi4py (função de classe):
    g_new = MPI.Group.Union(g1, g2)

    # Novo comunicador só com quem pertence à união
    comm_new = comm_world.Create(g_new)  # quem não pertence recebe COMM_NULL

    if comm_new != MPI.COMM_NULL:
        new_rank = comm_new.Get_rank()   # novo número no novo pátio
        print(f"ranque antigo = {rank} | novo ranque = {new_rank}")
        comm_new.Free()

    # Liberar grupos
    g_new.Free()
    g1.Free()
    g2.Free()
    g_world.Free()

    MPI.Finalize()

if __name__ == "__main__":
    main()


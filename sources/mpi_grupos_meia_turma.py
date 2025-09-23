# mpi_grupos_meia_turma_flex.py
# Divide a turma em dois grupos (metade de baixo e metade de cima),
# cria comunicadores para cada grupo e faz um Allreduce (soma) dentro de cada grupo.
# Explicação para jovens:
# - Cada criança tem seu número de camiseta (rank).
# - Formamos dois times: "Baixo" e "Cima".
# - Cada time se reúne no seu próprio "pátio" (comunicador) e soma os números das camisetas.

from mpi4py import MPI
import sys

def main():
    comm_world = MPI.COMM_WORLD
    rank = comm_world.Get_rank()
    size = comm_world.Get_size()

    if size < 2:
        if rank == 0:
            print("Precisa de pelo menos 2 processos.")
        comm_world.Abort(1)

    # Grupo do mundo (todas as crianças)
    g_world = comm_world.Get_group()

    # Cortamos a turma ao meio (se for ímpar, o time de cima fica com 1 a mais)
    mid = size // 2
    ranks_low  = list(range(0, mid))        # time Baixo
    ranks_high = list(range(mid, size))     # time Cima

    # Cada processo escolhe em qual metade está
    if rank < mid:
        g_new = g_world.Incl(ranks_low)
        team  = "Baixo"
    else:
        g_new = g_world.Incl(ranks_high)
        team  = "Cima"

    # Cria o "pátio" do time (novo comunicador)
    comm_new = comm_world.Create(g_new)   # válido para quem pertence ao grupo

    # Novo número de camiseta dentro do pátio do time
    new_rank = g_new.Get_rank()  # aqui sempre definido, pois todos estão em um dos grupos

    # Soma coletiva dentro do time (soma dos ranks originais só para ilustrar)
    my_value = rank
    team_sum = comm_new.allreduce(my_value, op=MPI.SUM)

    print(f"[Time {team}] rank antigo = {rank:>2} | novo rank = {new_rank:>2} | soma do time = {team_sum}")

    # Limpeza
    comm_new.Free()
    g_new.Free()
    g_world.Free()
    MPI.Finalize()

if __name__ == "__main__":
    main()

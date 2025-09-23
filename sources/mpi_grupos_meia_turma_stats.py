# mpi_grupos_meia_turma_stats.py
# Divide a turma em dois grupos (Baixo e Cima), cria comunicadores,
# calcula estatísticas por time e imprime um resumo claro.

from mpi4py import MPI

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

    # Cortamos a turma ao meio.
    mid = size // 2
    ranks_low  = list(range(0, mid))      # Time Baixo
    ranks_high = list(range(mid, size))   # Time Cima

    # Cada processo escolhe seu time e grupo correspondente
    if rank < mid:
        team_name = "Baixo"
        g_new = g_world.Incl(ranks_low)
    else:
        team_name = "Cima"
        g_new = g_world.Incl(ranks_high)

    # Novo "pátio" (comunicador) para o time
    comm_new = comm_world.Create(g_new)

    # Novo número de camiseta dentro do time
    new_rank = g_new.Get_rank()  # sempre definido aqui

    # Estatísticas do time: soma e média dos RANKS ANTIGOS
    my_value = rank
    team_sum  = comm_new.allreduce(my_value, op=MPI.SUM)
    team_size = comm_new.Get_size()
    team_mean = team_sum / team_size

    # Quem está em cada time? (lista de ranks antigos)
    members = comm_new.gather(rank, root=0)  # só o líder recebe a lista

    # Cada processo mostra seu mapeamento (antigo -> novo)
    print(f"[Time {team_name}] rank antigo = {rank:>2} -> novo rank = {new_rank:>2}")

    # O líder do time imprime o resumo do time
    if new_rank == 0:
        members_sorted = sorted(members)
        print(f"\n=== Resumo do Time {team_name} ===")
        print(f"Membros (ranks antigos): {members_sorted}")
        print(f"Tamanho do time: {team_size}")
        print(f"Soma dos ranks antigos: {team_sum}")
        print(f"Média dos ranks antigos: {team_mean:.3f}")
        print(f"==============================\n")

    # Limpeza
    comm_new.Free()
    g_new.Free()
    g_world.Free()
    MPI.Finalize()

if __name__ == "__main__":
    main()

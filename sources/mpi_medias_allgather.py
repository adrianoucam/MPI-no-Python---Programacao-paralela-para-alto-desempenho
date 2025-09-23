# mpi_medias_allgather.py
# Ideia para crianças:
# - Cada criança (processo) tem 1024 bolinhas com números entre 0 e 1.
# - Cada uma calcula a sua MÉDIA LOCAL.
# - Com MPI_Allgather (allgather), TODO MUNDO troca as médias entre si.
# - Assim, cada criança consegue calcular a MÉDIA DA TURMA.

from mpi4py import MPI
import numpy as np

NELEM = 1024  # cada criança tem 1024 bolinhas

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()  # sou a criança número rank
    size = comm.Get_size()  # total de crianças na sala

    # Semente diferente para cada criança, para os números saírem diferentes
    seed = int(MPI.Wtime() * 1e6) + (rank + 1) * 12345
    rng = np.random.default_rng(seed)

    # Cria as "bolinhas" (números aleatórios entre 0 e 1)
    # dtype float32 para se parecer com 'float' do C
    bolinhas = rng.random(NELEM).astype(np.float32)

    # Cada criança soma suas bolinhas e calcula a MÉDIA LOCAL
    soma_local = float(np.sum(bolinhas, dtype=np.float64))
    media_local = soma_local / NELEM

    print(f"[Criança {rank}] Soma local = {soma_local:.6f} | Média local = {media_local:.6f}")

    # === Troca de informações: ALLGATHER ===
    # Todo mundo envia sua 'media_local' e recebe a 'media_local' de todo mundo.
    # Versão simples (objetos Python): retorna uma lista com 'size' médias.
    medias_de_todos = comm.allgather(media_local)

    # Como cada criança tem o MESMO número de bolinhas (NELEM),
    # a média da turma é a média das médias locais.
    media_turma = sum(medias_de_todos) / size

    print(f"[Criança {rank}] Média da turma (calculada aqui) = {media_turma:.6f}")

    # Observação: se cada criança tivesse QUANTIDADES DIFERENTES de bolinhas,
    # precisaríamos fazer uma MÉDIA PONDERADA (peso = quantidade de bolinhas de cada uma).

if __name__ == "__main__":
    main()

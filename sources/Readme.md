<b>Descricao de programas exemplo usando MPI no python</b>
<br>
<br>
Bolinhas distribuidas entre o rank0 e rank1<br>
<br>
mpiexec -n 4 python3 mpi_bolinhas.py (mpirun -n 4 python3 mpi_bolinhas.py no linux)<br>
[Rank 3] Estou s¾ observando a troca de bolinhas.<br>
[Rank 2] Estou s¾ observando a troca de bolinhas.<br>
[Rank 0] Enviei 10 bolinha(s) para o Rank 1.<br>
[Rank 1] Recebi 10 bolinha(s). De quem? Rank 0 | Etiqueta: 0<br>
[Rank 1] As bolinhas sÒo: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]<br>

Python + mpi4py do seu mpi_allgather.c, explicada “para crianças”. <br>
Pense que cada criança (processo) tem 1024 bolinhas com números entre 0 e 1. <br>
Cada criança calcula a sua média e depois todas as crianças trocam suas médias entre si <br>
usando o Allgather (tipo “todo mundo conta sua média para todo mundo”).<br>
No fim, cada uma consegue calcular a média da turma.<br>
<br>
<br>
mpiexec -n 4 python3 mpi_medias_allgather.py <br>
[Crianþa 1] Soma local = 525.791824 | MÚdia local = 0.513469<br>
[Crianþa 1] MÚdia da turma (calculada aqui) = 0.502864<br>
[Crianþa 3] Soma local = 507.466116 | MÚdia local = 0.495572<br>
[Crianþa 3] MÚdia da turma (calculada aqui) = 0.502864<br>
[Crianþa 2] Soma local = 514.933010 | MÚdia local = 0.502864<br>
[Crianþa 2] MÚdia da turma (calculada aqui) = 0.502864<br>
[Crianþa 0] Soma local = 511.540861 | MÚdia local = 0.499552<br>
[Crianþa 0] MÚdia da turma (calculada aqui) = 0.502864<br>

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

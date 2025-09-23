<b>Descricao de programas exemplo usando MPI no python</b>
<br>
<br>
Bolinhas distribuidas entre o rank0 e rank1<br>
<br>
mpiexec -n 4 python3 mpi_bolinhas.py (mpirun -n 4 python3 mpi_bolinhas.py no linux)<br>
[Rank 3] Estou só observando a troca de bolinhas.<br>
[Rank 2] Estou só observando a troca de bolinhas.<br>
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
[Crianca 1] Soma local = 525.791824 | Media local = 0.513469<br>
[Crianca 1] Media da turma (calculada aqui) = 0.502864<br>
[Crianca 3] Soma local = 507.466116 | Media local = 0.495572<br>
[Crianca 3] Media da turma (calculada aqui) = 0.502864<br>
[Crianca 2] Soma local = 514.933010 | Media local = 0.502864<br>
[Crianca 2] Media da turma (calculada aqui) = 0.502864<br>
[Crianca 0] Soma local = 511.540861 | Media local = 0.499552<br>
[Crianca 0] Media da turma (calculada aqui) = 0.502864<br>
<br>
<br>
versão em Python + mpi4py do seu allreduce, explicada “para em problemas simples” - uso academico. <br><br>
Pense que cada criança (processo) tem 1024 bolinhas com números entre 0 e 1. <br>
Cada uma calcula sua soma/média local. Depois, com Allreduce, todas somam tudo juntas (como se toda a turma colocasse as bolinhas numa mesa invisível e somasse de uma vez). <br>
Em seguida, cada uma calcula o quanto suas bolinhas estão longe da média da turma (diferença ao quadrado) e novamente usa Allreduce para achar o desvio padrão da turma.
<br>
<br>
mpiexec -n 6 python3 mpi_media_desvio_allreduce.py<br>
[Crianca 0] Soma local = 527.198582 | Media local = 0.514842<br>
[Crianca 0] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
[Crianca 1] Soma local = 514.481876 | Media local = 0.502424<br>
[Crianca 1] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
[Crianca 3] Soma local = 521.256441 | Media local = 0.509039<br>
[Crianca 3] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
[Crianca 2] Soma local = 522.115765 | Media local = 0.509879<br>
[Crianca 2] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
[Crianca 5] Soma local = 515.700250 | Media local = 0.503614<br>
[Crianca 5] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
[Crianca 4] Soma local = 503.313458 | Media local = 0.491517<br>
[Crianca 4] Media da turma = 0.505219 | Desvio padrao = 0.288570<br>
<br>
BARRIER<br>
Aqui vai a versão em Python + mpi4py do seu barrier, explicada de forma academica<br>
<br>
Pense que a barreira é um portão no parquinho: ninguém pode passar até todas as crianças chegarem. <br>
A criança 0 chega atrasada (espera o Enter), as outras ficam esperando no portão. <br>
Quando todo mundo chega, o portão abre e todas passam juntas.<br>
<br>
mpiexec -n 4 python mpi_barreira_criancas.py <br>
mpiexec -n 8 python3 mpi_barreira_criancas.py <br>
[Crianca 7] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 4] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 3] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 2] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 5] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 6] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 1] Cheguei na barreira e estou esperando a Crianca 0...<br>
[Crianca 0] Estou atrasada para a barreira! (segurando o portao)<br>
Pressione Enter para eu chegar (ou aguarde 3s)... <br>
[Crianca 0] Passei da barreira! Sou 0 de 8.<br>
[Crianca 4] Passei da barreira! Sou 4 de 8.<br>
[Crianca 2] Passei da barreira! Sou 2 de 8.<br>
[Crianca 6] Passei da barreira! Sou 6 de 8.<br>
[Crianca 1] Passei da barreira! Sou 1 de 8.<br>
[Crianca 5] Passei da barreira! Sou 5 de 8.<br>
[Crianca 3] Passei da barreira! Sou 3 de 8.<br>
[Crianca 7] Passei da barreira! Sou 7 de 8.<br>

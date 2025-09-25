
<b>Descricao de programas exemplo usando MPI no python</b>
<br>
Programa de aproximação de π (pi) usando Allreduce, com explicação para uso academico.<br>
<br>
Pense que queremos descobrir o tamanho da pizza (pi). Cada criança (processo) mede um pedacinho e no final somamos tudo. O Allreduce é como juntar todas as medidas em uma só resposta que todos recebem.<br>
mpiexec -n 4 python mpi_pi_criancas.py<br>
mpiexec -n 4 python3 mpi_pi_criancas.py<br>
[Rank 0] valor aproximado de pi: 3.1415926535897936<br>
[Rank 0] erro absoluto em relacao a math.pi: 4.441e-16<br>
[Rank 2] valor aproximado de pi: 3.1415926535897936<br>
[Rank 3] valor aproximado de pi: 3.1415926535897936<br>
[Rank 1] valor aproximado de pi: 3.1415926535897936<br>
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
<br>
<br>
mpi_scatter<br>
Ideia: o Líder (rank 0) tem uma fila de figurinhas (um vetor grandão). Com o Scatter, ele divide igualmente e entrega um pacotinho de TAM_VET figurinhas para cada criança (cada processo), inclusive para ele mesmo.<br>
<br>
mpiexec -n 4 python3 mpi_scatter_criancas.py<br>
Processo 1 recebeu: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]<br>
Processo 2 recebeu: [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]<br>
Processo 0 recebeu: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]<br>
Processo 3 recebeu: [30, 31, 32, 33, 34, 35, 36, 37, 38, 39]<br>
<br>
<br>
wtime para avaliar o tempo gasto nos processos<br>
mpiexec -n 8 python3 mpi_wtime_criancas.py --n 50000<br>
[Rank 2] Gastos 0.004514 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 1] Gastos 0.004384 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 5] Gastos 0.004365 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 3] Gastos 0.004053 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 7] Gastos 0.004564 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 0] Gastos 0.004747 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 4] Gastos 0.003916 s para calcular a = 49999 com precisao 6.984e-08 s<br>
[Rank 6] Gastos 0.003573 s para calcular a = 49999 com precisao 6.984e-08 s<br>
<br>
wtime + barrier para uma comparacao justa<br>
mpiexec -n 2 python3 mpi_wtime_criancas_barrier.py --n 500000<br>
[Rank 1] Tempo = 0.044915 s | a = 499999 | precisao = 6.984e-08 s<br>
[Rank 0] Tempo = 0.047111 s | a = 499999 | precisao = 6.984e-08 s<br>
<br>
<br>
MPI SEND + MPI GETCOUNT<br>
Ideia: a Criança 0 escolhe uma quantidade aleatória de bolinhas (números) e envia para a Criança 1. A Criança 1 recebe até um máximo de 100 e usa o status da mensagem para descobrir quantas realmente chegaram, além de quem enviou e qual foi a etiqueta (tag).<br>
<br>
mpiexec -n 8 python3 mpi_aleatorio_criancas.py<br>
[Rank 7] Sem papel nesta brincadeira.<br>
[Rank 2] Sem papel nesta brincadeira.<br>
[Rank 4] Sem papel nesta brincadeira.<br>
[Rank 3] Sem papel nesta brincadeira.<br>
[Rank 6] Sem papel nesta brincadeira.<br>
[Rank 5] Sem papel nesta brincadeira.<br>
[Rank 0] Enviei 58 numero(s) para o Rank 1 (tag=42).<br>
[Rank 1] Recebi 58 numero(s). Origem = 0, tag = 42.<br>
[Rank 1] Valores: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, '...']<br>
<br>
<br>
MPI SSEND
Ideia: cada criança tem um número. Em rodadas de “dobrar a distância” (1, depois 2, depois 4, …), ela troca números com uma parceira.<br>
Desta vez usamos envio síncrono (Ssend): é como falar cara a cara — quem fala só segue em frente quando tem certeza de que a outra já está ouvindo (o Recv já foi postado). Para não travar, metade das crianças envia primeiro e a outra metade recebe primeiro em cada rodada<br>
<br>
mpiexec -n 4 python3 mpi_sincrona_criancas.py<br>
Rank 2: meu_valor = 8, reducao = 12<br>
Rank 0: meu_valor = 0, reducao = 12<br>
Rank 1: meu_valor = 4, reducao = 12<br>
Rank 3: meu_valor = 12, reducao = 12<br>

<br>
<br>
MPI.Datatype.Create_struct com MPI_Botton, BCast
exemplo com tipo derivado vector e broadcast de uma coluna, explicada de forma academica.<br>
<br>
Ideia: pense numa tabela 4×4 de números. O Líder (rank 0) quer “gritar” para todos os outros a 2ª coluna da tabela. Como essa coluna está “espalhada” na memória (não é um bloco contínuo), usamos um tipo derivado “vetor” para dizer ao MPI: “pegue 1 número por linha, pulando de 4 em 4”.<br>
<br>
No C, você passa &matriz[0][1] (um ponteiro para o 1º elemento da coluna) e o datatype vector faz os “saltos”. Em mpi4py, para replicar isso direitinho, a forma robusta é:<br>
criar o datatype em bytes (Create_hvector),<br>
ancorá-lo no endereço absoluto do primeiro elemento da coluna com um Create_struct,<br>
e transmitir usando MPI.BOTTOM no root.<br>
<br>
mpiexec -n 4 python3 mpi_bcast_coluna_vector.py<br>
Processo 1 - vetor[0] = 2.0 vetor[1] = 6.0 vetor[2] = 10.0 vetor[3] = 14.0<br>
Processo 2 - vetor[0] = 2.0 vetor[1] = 6.0 vetor[2] = 10.0 vetor[3] = 14.0<br>
Processo 3 - vetor[0] = 2.0 vetor[1] = 6.0 vetor[2] = 10.0 vetor[3] = 14.0<br>


<br>
mpi_isend, explicada de forma academica.<br>
<br>
Ideia: cada criança tem um número. Em rodadas de “dobrar a distância” (1, depois 2, depois 4, …), ela troca seu número com uma parceira. Usamos mensageiros rápidos (envio/recebimento não bloqueante Isend/Irecv) — eles saem correndo enquanto a criança pode fazer outras coisas; no fim chamamos Wait para garantir que a entrega chegou. Depois de cada troca, a criança guarda o maior número. No final, todas ficam com o mesmo maior número.<br>
<br>
mpiexec -n 8 python3 mpi_isend_criancas.py<br>
Rank 4: meu_valor = 32, reducao = 56<br>
Rank 0: meu_valor = 0, reducao = 56<br>
Rank 6: meu_valor = 48, reducao = 56<br>
Rank 2: meu_valor = 16, reducao = 56<br>
Rank 7: meu_valor = 56, reducao = 56<br>
Rank 3: meu_valor = 24, reducao = 56<br>
Rank 5: meu_valor = 40, reducao = 56<br>
Rank 1: meu_valor = 8, reducao = 56<br>
<br>
<br>
mpi_maxloc, explicada de forma academica.<br>
<br>
Ideia: temos 10 “cartas” (posições 0..9). Cada criança (processo) tem um valor para cada carta. As crianças de número par colocam 50.0 na carta com o seu próprio número (se couber em 0..9). A turma quer saber, para cada carta, qual foi o maior valor e em qual criança ele apareceu — isso é o que o MAXLOC faz.<br>
<br>
Como em mpi4py o uso direto de MPI_MAXLOC com structs pode ser chato, vamos emular o comportamento com duas coletivas:<br>
<br>
Allreduce (MAX) para achar o maior valor de cada carta.<br>
<br>
Reduce (MIN) dos ranks candidatos (quem bateu o máximo naquela carta); quem não bateu manda “∞”. Assim, em caso de empate, fica o menor rank (igual ao MAXLOC).<br>
<br>
mpiexec -n 6 python3 mpi_maxloc_criancas.py<br>
Posicao  0: Resultado = 50.0  Processo = 0<br>
Posicao  1: Resultado =  1.0  Processo = 0<br>
Posicao  2: Resultado = 50.0  Processo = 2<br>
Posicao  3: Resultado =  3.0  Processo = 0<br>
Posicao  4: Resultado = 50.0  Processo = 4<br>
Posicao  5: Resultado =  5.0  Processo = 0<br>
Posicao  6: Resultado =  6.0  Processo = 0<br>
Posicao  7: Resultado =  7.0  Processo = 0<br>
Posicao  8: Resultado =  8.0  Processo = 0<br>
Posicao  9: Resultado =  9.0  Processo = 0<br>
<br>
Para cada posição (0..9), o Resultado é o maior valor alcançado naquela posição entre todos.<br>
<br>
Processo mostra quem (qual rank) bateu esse máximo; se deu empate, fica o menor rank <br>

<BR>
mpi_gather, explicada de forma academica:<br>
<br>
Pense que cada criança (processo) tem um bloquinho com 10 números. Cada criança preenche seu bloquinho com o seu número (o <br>rank). Depois, o Líder (rank 0) junta todos os bloquinhos com um Gather e mostra o resultado.<br>
mpiexec -n 8 python3 mpi_gather_criancas.py<br>
[Lider] Recebi 8 bloquinhos de tamanho 10.<br>
<br>
Do processo 0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]<br>
Do processo 1: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]<br>
Do processo 2: [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]<br>
Do processo 3: [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]<br>
Do processo 4: [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]<br>
Do processo 5: [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]<br>
Do processo 6: [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]<br>
Do processo 7: [7, 7, 7, 7, 7, 7, 7, 7, 7, 7]<br>
<br>
Vetor achatado (como no C):<br>
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]<br>
<br>


<br>
<br>
Python + mpi4py do seu mpi_allgather.c, explicada “para crianças”. <br>
Pense que cada criança (processo) tem 1024 bolinhas com números entre 0 e 1. <br>
Cada criança calcula a sua média e depois todas as crianças trocam suas médias entre si <br>
usando o Allgather (tipo “todo mundo conta sua média para todo mundo”).<br>
No fim, cada uma consegue calcular a média da turma.<br>
<br>
<br>
MPI Com funçoes, para identificar versões e validar tempo<br>
<br>
pense no programa como um “cartão de identidade do time MPI” — cada jogadora (processo) diz quem é (rank), quantas jogadoras existem (size), em qual “computador-quadra” está jogando e qual é a versão do uniforme (versão do MPI).<br>
<br>
Também medimos quanto tempo a checagem levou e qual é a precisão do relógio do juiz (Wtick).<br>
<br>
mpiexec -n 8 python3 mpi_funcoes_criancas.py<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 3  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000355 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 0  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000345 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 4  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000291 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 5  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000405 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 6  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000339 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 2  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000249 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 7  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000340 segundos com precisao de 6.984e-08 segundos<br>
Versao do MPI = 2 Subversao = 0<br>
Numero de tarefas = 8  Meu ranque = 1  Executando em DESKTOP-QB4IQQB<br>
Foram gastos 0.000252 segundos com precisao de 6.984e-08 segundos<br>
<br>
versão com GATHER para agrupar tudo <br>
mpiexec -n 8 python3 mpi_funcoes_criancas_gather.py<br>
Versao do MPI = 2  Subversao = 0<br>
<br>
Resumo dos processos (ordenado por rank):<br>
rank | size | maquina                      | tempo (s) | Wtick (s)<br>
-----+------+-------------------------------+-----------+----------<br>
   0 |    8 | DESKTOP-QB4IQQB               |  0.000341 | 6.984e-08<br>
   1 |    8 | DESKTOP-QB4IQQB               |  0.000183 | 6.984e-08<br>
   2 |    8 | DESKTOP-QB4IQQB               |  0.000340 | 6.984e-08<br>
   3 |    8 | DESKTOP-QB4IQQB               |  0.000192 | 6.984e-08<br>
   4 |    8 | DESKTOP-QB4IQQB               |  0.000214 | 6.984e-08<br>
   5 |    8 | DESKTOP-QB4IQQB               |  0.000377 | 6.984e-08<br>
   6 |    8 | DESKTOP-QB4IQQB               |  0.000234 | 6.984e-08<br>
   7 |    8 | DESKTOP-QB4IQQB               |  0.000335 | 6.984e-08<br>
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
<br>
BROADCAST<br>
Aqui vai a versão em Python + mpi4py do seu bcast, explicada de forma academica<br>
<br>
Pense que o broadcast é como o líder da turma gritando um número no pátio: <br>
o Líder (Criança 0) fala uma vez e todas as crianças escutam e passam a saber o mesmo número.<br>
<br>
mpiexec -n 8 python3 mpi_broadcast_criancas.py<br>
[Lider] Entre um valor inteiro:<br>
4<br>
[Crianca 0] Recebi o valor do Lider: 4<br>
[Crianca 1] Recebi o valor do Lider: 4<br>
[Crianca 2] Recebi o valor do Lider: 4<br>
[Crianca 4] Recebi o valor do Lider: 4<br>
[Crianca 5] Recebi o valor do Lider: 4<br>
[Crianca 3] Recebi o valor do Lider: 4<br>
[Crianca 6] Recebi o valor do Lider: 4<br>
[Crianca 7] Recebi o valor do Lider: 4<br>
<br>
BSEND

Versão usando bsend , explicada para uso academico.

Imagine que cada criança tem um cartão com 4 números iguais (ex.: [6,6,6,6]). <br>
Em cada rodada, ela troca cartões com um “vizinho” <br>
(que vai ficando cada vez mais distante: 1 passo, depois 2, depois 4…). <br>
Após cada troca, cada criança fica com o maior número em cada posição. <br>
No fim, todas sabem o maior de cada posição entre todas as crianças.<br>
Aqui usamos Bsend (envio bufferizado): é como colocar a carta numa caixinha de correio (buffer) antes de enviar.<br>
<br>
mpiexec -n 4 python mpi_bsend_criancas.py<br>
<br>
mpiexec -n 4 python3 mpi_bsend_criancas.py<br>
[Rank 3] Valor inicial = 12 | Cartao final (maximos) = [12, 12, 12, 12]<br>
[Rank 1] Valor inicial = 4 | Cartao final (maximos) = [12, 12, 12, 12]<br>
[Rank 2] Valor inicial = 8 | Cartao final (maximos) = [12, 12, 12, 12]<br>
[INFO] Buffer de Bsend anexado com 55 bytes.<br>
[Rank 0] Valor inicial = 0 | Cartao final (maximos) = [12, 12, 12, 12]<br>
<br>
<br>
Usando tipo dtype NumPy equivalente ao struct do C , com MPI BroadCast e Gather para juntar os valores
Ideia<br>
<br>
Imagine que cada “partícula” é uma fichinha com 6 campos:<br>
<br>
4 números de ponto flutuante: x, y, z, velocidade<br>
<br>
2 números inteiros: n, tipo<br>
<br>
O Líder (rank 0) preenche um pacote com 25 fichinhas e, com um broadcast, manda o mesmo pacote para todas as crianças (processos).<br>
Usamos um tipo MPI derivado para dizer ao MPI exatamente como essa fichinha é organizada na memória.<br>
o rank 0 cria as fichas e faz broadcast.<br>
cada rank aplica um deslocamento simples nas suas fichas.<br>
fazemos um gather de volta no rank 0, que desenha um gráfico (x vs y) com um grupo por processo.<br>
se você estiver num ambiente sem janela gráfica, será salvo um arquivo particulas.png na pasta atual <br>
<br>
MPI group include<BR>
Dois grupos (metade/metade), novo comunicador para cada grupo e Allreduce (soma) dentro do grupo.<BR>
Ideia: temos 8 crianças (processos) numeradas de 0 a 7.<br>
Formamos dois times:<br>
Time A = [0, 1, 2, 3]<br>
Time B = [4, 5, 6, 7]<br>
Cada criança entra no seu time (grupo) e ganha um novo número de camiseta (o novo rank) dentro do novo pátio (comunicador) do time.<br>
Dentro de cada pátio, fazemos uma soma coletiva dos números das camisetas (Allreduce com soma).<br>
Cada criança mostra: rank antigo, novo rank e o resultado da soma do seu time.<br>
mpiexec -n 4 python3 mpi_grupos_meia_turma.py<br>
[Time Cima] rank antigo =  2 | novo rank =  0 | soma do time = 5<br>
[Time Cima] rank antigo =  3 | novo rank =  1 | soma do time = 5<br>
[Time Baixo] rank antigo =  0 | novo rank =  0 | soma do time = 1<br>
[Time Baixo] rank antigo =  1 | novo rank =  1 | soma do time = 1<br>
<br>
<br>
mpiexec -n 10 python3 mpi_grupos_meia_turma_stats.py<br>
[Time Baixo] rank antigo =  2 -> novo rank =  2<br>
[Time Cima] rank antigo =  7 -> novo rank =  2<br>
[Time Baixo] rank antigo =  1 -> novo rank =  1<br>
[Time Cima] rank antigo =  9 -> novo rank =  4<br>
[Time Baixo] rank antigo =  0 -> novo rank =  0<br>
<br>
=== Resumo do Time Baixo === <br>
Membros (ranks antigos): [0, 1, 2, 3, 4] <br>
Tamanho do time: 5<br>
Soma dos ranks antigos: 10<br>
MÚdia dos ranks antigos: 2.000<br>
============================== <br>
<br>
[Time Baixo] rank antigo =  3 -> novo rank =  3<br>
[Time Cima] rank antigo =  8 -> novo rank =  3<br>
[Time Cima] rank antigo =  5 -> novo rank =  0<br>
 <br>
=== Resumo do Time Cima ===<br>
Membros (ranks antigos): [5, 6, 7, 8, 9]<br>
Tamanho do time: 5<br>
Soma dos ranks antigos: 35<br>
MÚdia dos ranks antigos: 7.000<br>
==============================<br>
<br>
[Time Baixo] rank antigo =  4 -> novo rank =  4<br>
[Time Cima] rank antigo =  6 -> novo rank =  1<br>
<br>
<BR>
MPI_GROUP e MPI COMM (comunicadores)
grupos e comunicadores — explicada de forma academica .<BR>
<BR>
Ideia: imagine 10 crianças numeradas de 0 a 9.<BR>
<BR>
Montamos dois times com algumas crianças:<BR>
<BR>
Time A = [0, 2, 3, 4, 5, 8]<BR>
<BR>
Time B = [9, 4, 0, 2, 8]<BR>
<BR>
Depois fazemos a união dos times (sem repetir crianças) e criamos um novo pátio (comunicador) só para quem está na união.<BR>
<BR>
Dentro desse novo pátio, cada criança ganha um novo número de camiseta (o novo rank).<BR>
<BR>
Quem não está no novo time não entra no pátio novo.<BR>
<BR>
mpiexec -n 10 python3 mpi_grupos_criancas.py<BR>
ranque antigo = 4 | novo ranque = 3<BR>
ranque antigo = 3 | novo ranque = 2<BR>
ranque antigo = 2 | novo ranque = 1<BR>
ranque antigo = 5 | novo ranque = 4<BR>
ranque antigo = 8 | novo ranque = 5<BR>
ranque antigo = 9 | novo ranque = 6<BR>
ranque antigo = 0 | novo ranque = 0<BR>
<BR>
(os ranks 1, 6 e 7 não aparecem porque não entraram na união dos grupos)<BR>
<BR>
Dica didática: o novo rank é como o novo número de camiseta dentro do novo time (comunicador). Fora desse time, o número “antigo” (rank do mundo) continua o mesmo.<BR>
<BR>
<BR>
<BR>
mpi_trapezio, com a mesma lógica (envios/recebimentos explícitos) e uma explicação academica.<BR>
usando send e receive para distribuir os calculos
<BR>
Pense assim: queremos medir a área sob a curva da função exp(x) entre a=0 e b=1. Dividimos em muitos “trapezinhos”. Cada criança (processo) soma alguns trapezinhos, e o rank 0 junta tudo no final.<BR>
<BR>
mpiexec -n 4 python3 mpi_trapezio_criancas.py<BR>
Foram gastos 11.3 segundos<BR>
Com n = 100000000 trapezoides, a estimativa<BR>
da integral de 0.000000 ate 1.000000 = 1.718281855372<BR>
<BR>
mpiexec -n 8 python3 mpi_trapezio_criancas.py<BR>
Foram gastos 7.2 segundos<BR>
Com n = 100000000 trapezoides, a estimativa<BR>
da integral de 0.000000 ate 1.000000 = 1.718281855573<BR>
<BR>
<BR>
versão curta usando coletiva (Reduce).<BR>
Se quiser que todos os processos recebam o resultado, troque reduce por allreduce.<BR>
versão de trapezio com reduce , ficou mais lenta nos meus testes <BR>
<BR>
mpiexec -n 4 python3 mpi_trapezio_coletiva.py<BR>
Foram gastos 18.2 segundos<BR>
Com n = 100000000 trapezoides, a estimativa<BR>
da integral de 0.000000 atÚ 1.000000 = 1.718281828459<BR>
<BR>
mpiexec -n 8 python3 mpi_trapezio_coletiva.py<BR>
Foram gastos 10.9 segundos<BR>
Com n = 100000000 trapezoides, a estimativa<BR>
da integral de 0.000000 atÚ 1.000000 = 1.718281828459<BR>

<br>
 mpi_alltoall_sensores.py<br>
 Objetivo acadêmico:<br>
 - Cada processo gera 1 leitura para cada "sensor" (0..size-1) => vetor de tamanho "size".<br>
 - Usando MPI_Alltoall, o elemento j vai para o processo j.<br>
 - Assim, o processo j recebe todas as leituras do "sensor j" (uma de cada processo) e calcula a média.<br>
mpi_comm.Alltoall<br>
<br>
mpiexec -n 4  python3 all_to_all.py<br>
[Entrada]  rank 0: [0, 1, 2, 3]<br>
[Saida]    rank 0: [0, 100, 200, 300]<br>
[Sensor 0] min=0  max=300  media=150.00<br>
[Entrada]  rank 1: [100, 101, 102, 103]<br>
[Saida]    rank 1: [1, 101, 201, 301]<br>
[Sensor 1] min=1  max=301  media=151.00<br>
[Entrada]  rank 3: [300, 301, 302, 303]<br>
[Saida]    rank 3: [3, 103, 203, 303]<br>
[Sensor 3] min=3  max=303  media=153.00<br>
[Entrada]  rank 2: [200, 201, 202, 203]<br>
[Saida]    rank 2: [2, 102, 202, 302]<br>
[Sensor 2] min=2  max=302  media=152.00<br>
<br>
<br>
Exemplo Acadêmico: Multigrid (Ciclo-V) 2D para Poisson<br>
<br>
Este exemplo resolve a equação de Poisson -∇² u = f em [0,1] × [0,1] com condição de Dirichlet zero (bordas u = 0).
A implementação usa mpi4py com comunicador cartesiano e faz troca de halos (ghost cells) entre vizinhos a cada etapa de suavização.<br>
<br>
O código está bem comentado e inclui um bloco de documentação no topo — pronto para entrar na sua doc.<br>

Resumo didático<br>
<br>
Domínio e malha: o domínio [0,1] × [0,1] é discretizado em uma malha uniforme Nx × Ny.<br>
<br>
Particionamento paralelo: a malha é particionada em um grid 2D de processos (cartesiano); cada processo resolve seu subdomínio com células de halo.<br>
<br>
Ciclo-V (V-cycle):<br>
<br>
Pré-suavização (relaxação, p.ex. Jacobi/GS)<br>
<br>
Restrição do resíduo para a malha mais grossa<br>
<br>
Solução aproximada no nível grosseiro<br>
<br>
Prolongamento da correção para a malha fina<br>
<br>
Pós-suavização<br>
<br>
Comunicação MPI:<br>
<br>
Troca de fronteiras (vizinho-a-vizinho) com MPI_Sendrecv (ou MPI_Isend/Irecv + MPI_Wait*)<br>
<br>
Reduções globais (norma do resíduo, produtos internos) com MPI_Allreduce<br>
<br>
Objetivo pedagógico: mostrar como o Multigrid reduz erro em vários comprimentos de onda e onde o MPI entra (halos entre vizinhos e reduções globais).<br>
<br>
mpiexec -n 4 python3 mpi_multigrid_vcycle.py --Nx 128 --Ny 128 --cycles 5
<br>
<br>



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

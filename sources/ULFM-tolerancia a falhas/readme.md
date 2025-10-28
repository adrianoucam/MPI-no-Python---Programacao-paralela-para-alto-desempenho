







### ULFM (User-Level Failure Mitigation) estende a API do MPI com erros e rotinas para:

## detectar falhas (erro MPI_ERR_PROC_FAILED),


revogar comunicadores comprometidos,


encolher o comunicador para excluir ranks mortos (MPI_Comm_shrink),


e reconstruir a malha de processos, permitindo o app prosseguir.


Veja: docs do Open MPI 5.x para ULFM e estudos de avaliação/implementação.


### EXEMPLO COM CHECKPOINT

## Desta forma, preserva os dados, se alguns dos ranks falharem

mpiexec -n 4 python3 mpi_checkpoint_demo.py --n 20000000 --iters 20 --ckpt-every 5

[2025-10-28 10:05:09.263] [rank 0] [host DESKTOP-QB4IQQB] Retomando do passo -1 (manifesto=-1). Blocagem: n=20000000 | SIZE=4 | local=[0,5000000) nloc=5000000

[2025-10-28 10:05:09.266] [rank 0] [host DESKTOP-QB4IQQB] step=0  acc_global=199,999,990,000,000.000

[2025-10-28 10:05:09.326] [rank 0] [host DESKTOP-QB4IQQB] [checkpoint] passo 0 salvo.

[2025-10-28 10:05:09.326] [rank 0] [host DESKTOP-QB4IQQB] step=1  acc_global=299,999,985,000,000.000

[2025-10-28 10:05:09.327] [rank 0] [host DESKTOP-QB4IQQB] step=2  acc_global=366,666,648,333,333.375

[2025-10-28 10:05:09.327] [rank 0] [host DESKTOP-QB4IQQB] step=3  acc_global=416,666,645,833,333.375

[2025-10-28 10:05:09.327] [rank 0] [host DESKTOP-QB4IQQB] step=4  acc_global=456,666,643,833,333.375

[2025-10-28 10:05:09.327] [rank 0] [host DESKTOP-QB4IQQB] step=5  acc_global=489,999,975,500,000.000

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] [checkpoint] passo 5 salvo.

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] step=6  acc_global=518,571,402,642,857.125

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] step=7  acc_global=543,571,401,392,857.125

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] step=8  acc_global=565,793,622,503,968.250

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] step=9  acc_global=585,793,621,503,968.250

[2025-10-28 10:05:09.341] [rank 0] [host DESKTOP-QB4IQQB] step=10  acc_global=603,975,438,776,695.500

[2025-10-28 10:05:09.353] [rank 0] [host DESKTOP-QB4IQQB] [checkpoint] passo 10 salvo.

[2025-10-28 10:05:09.354] [rank 0] [host DESKTOP-QB4IQQB] step=11  acc_global=620,642,104,610,028.875

[2025-10-28 10:05:09.354] [rank 0] [host DESKTOP-QB4IQQB] step=12  acc_global=636,026,719,225,413.500

[2025-10-28 10:05:09.354] [rank 0] [host DESKTOP-QB4IQQB] step=13  acc_global=650,312,432,796,842.000

[2025-10-28 10:05:09.354] [rank 0] [host DESKTOP-QB4IQQB] step=14  acc_global=663,645,765,463,508.750

[2025-10-28 10:05:09.354] [rank 0] [host DESKTOP-QB4IQQB] step=15  acc_global=676,145,764,838,508.750

[2025-10-28 10:05:09.367] [rank 0] [host DESKTOP-QB4IQQB] [checkpoint] passo 15 salvo.

[2025-10-28 10:05:09.367] [rank 0] [host DESKTOP-QB4IQQB] step=16  acc_global=687,910,470,132,626.250

[2025-10-28 10:05:09.367] [rank 0] [host DESKTOP-QB4IQQB] step=17  acc_global=699,021,580,688,181.875

[2025-10-28 10:05:09.367] [rank 0] [host DESKTOP-QB4IQQB] step=18  acc_global=709,547,895,951,339.875

[2025-10-28 10:05:09.367] [rank 0] [host DESKTOP-QB4IQQB] step=19  acc_global=719,547,895,451,339.875

[2025-10-28 10:05:09.382] [rank 0] [host DESKTOP-QB4IQQB] [checkpoint] passo 19 salvo.

[2025-10-28 10:05:09.382] [rank 0] [host DESKTOP-QB4IQQB] Finalizado com sucesso.



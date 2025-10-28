
ULFM (User-Level Failure Mitigation) estende a API do MPI com erros e rotinas para:

detectar falhas (erro MPI_ERR_PROC_FAILED),


revogar comunicadores comprometidos,


encolher o comunicador para excluir ranks mortos (MPI_Comm_shrink),


e reconstruir a malha de processos, permitindo o app prosseguir.


Veja: docs do Open MPI 5.x para ULFM e estudos de avaliação/implementação.

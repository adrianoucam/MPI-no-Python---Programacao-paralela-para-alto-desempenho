
# Exemplo para calcular Pi com 4 processos
mpiexec -n 4 python3 ep_pi.py --total-samples 20000000

# Exemplo para calcular a área de f(x)=x^2
mpiexec -n 4 python3 mc_area_f_x2.py --total-samples 20000000

# Exemplo para a simulação econômica
mpiexec -n 4 python3 mc_economia_risco.py --total-sims 5000000

# Exemplo para a simulação de física
mpiexec -n 4 python3 mc_fisica_rocket.py --total-samples 10000000

# Exemplo para a demo de adição de vetores
mpiexec -n 4 python3 demo_vector_add.py

"""Ponto de entrada do dashboard.

Execução: ``poetry run streamlit run src/f1/dashboard/app.py``.

A interface fica em ``f1.dashboard.ui``. O Streamlit executa este arquivo como
script solto (fora do pacote ``f1``); mantê-lo mínimo faz com que todo o
código da UI seja importado como módulo do pacote e testado normalmente.
"""

from f1.dashboard.ui import main

main()

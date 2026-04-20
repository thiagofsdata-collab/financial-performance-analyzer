select
    date,
    company,
    receita_bruta,
    ebitda
from {{ ref('fct_dre') }}
where receita_bruta <= ebitda
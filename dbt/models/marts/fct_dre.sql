with base as (
    select * from {{ ref('int_transactions_enriched') }}
),

pivoted as (
    select
        date,
        company,
        sum(case when dre_line = 'Receita Bruta' then amount else 0 end) as receita_bruta,
        sum(case when dre_line = 'Deducoes da Receita' then amount else 0 end) as deducoes_receita,
        sum(case when dre_line = 'COGS' then amount else 0 end) as cogs,
        sum(case when dre_line = 'Opex' then amount else 0 end) as opex,
        sum(case when dre_line = 'Resultado Financeiro' then amount else 0 end) as resultado_financeiro,
        sum(case when dre_line = 'Impostos' then amount else 0 end) as impostos
    from base
    group by date, company
),

with_subtotals as (
    select
        date,
        company,
        receita_bruta,
        deducoes_receita,
        cogs,
        opex,
        resultado_financeiro,
        impostos,
        receita_bruta + deducoes_receita as receita_liquida,
        receita_bruta + deducoes_receita + cogs as lucro_bruto,
        receita_bruta + deducoes_receita + cogs + opex as ebitda,
        receita_bruta + deducoes_receita + cogs + opex
            + resultado_financeiro + impostos as lucro_liquido,
        round(
            (receita_bruta + deducoes_receita + cogs)
            / nullif(receita_bruta, 0), 4
        ) as gross_margin,
        round(
            (receita_bruta + deducoes_receita + cogs + opex)
            / nullif(receita_bruta, 0), 4
        ) as ebitda_margin,
        round(
            (receita_bruta + deducoes_receita + cogs + opex
                + resultado_financeiro + impostos)
            / nullif(receita_bruta, 0), 4
        ) as net_margin
    from pivoted
)

select * from with_subtotals
order by company, date
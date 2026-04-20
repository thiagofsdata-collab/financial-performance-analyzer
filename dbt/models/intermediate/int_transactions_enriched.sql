with transactions as (
    select * from {{ ref('stg_transactions') }}
),

account_mapping as (
    select * from {{ ref('stg_account_mapping') }}
),

joined as (
    select
        t.date,
        t.company,
        t.business_unit,
        t.cost_center,
        t.dre_line,
        a.dre_order,
        t.amount
    from transactions t
    left join account_mapping a
        on t.account_code = a.account_code
),

aggregated as (
    select
        date,
        company,
        business_unit,
        cost_center,
        dre_line,
        dre_order,
        sum(amount) as amount
    from joined
    group by
        date, company, business_unit, cost_center, dre_line, dre_order
)

select * from aggregated
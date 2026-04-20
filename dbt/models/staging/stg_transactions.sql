with source as (
    select * from {{ source('financial_db', 'transactions') }}
),

renamed as (
    select
        id as transaction_id,
        date::date as date,
        company,
        business_unit,
        cost_center,
        account_code,
        account_name,
        dre_line,
        amount::numeric as amount
    from source
)

select * from renamed
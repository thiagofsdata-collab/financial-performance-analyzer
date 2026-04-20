with source as (
    select * from {{ source('financial_db', 'account_mapping') }}
),

renamed as (
    select
        account_code,
        account_name,
        dre_line,
        dre_order,
        amount_sign
    from source
)

select * from renamed
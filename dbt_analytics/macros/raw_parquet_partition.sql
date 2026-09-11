{% macro raw_parquet_partition(filename) %}
(
    {% for market in var('active_market_codes') %}
        select
            '{{ market }}' as folder_market_code,
            cast(market_code as varchar) as market_code,
            '{{ filename }}' as filename
        from read_parquet('{{ var("raw_path") }}/{{ market }}/{{ filename }}')
        {% if not loop.last %}
            union all
        {% endif %}
    {% endfor %}
)
{% endmacro %}

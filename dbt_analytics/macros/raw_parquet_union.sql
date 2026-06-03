{% macro raw_parquet_union(filename) %}
(
    {% for market in var('active_market_codes') %}
        select * from read_parquet('{{ var("raw_path") }}/{{ market }}/{{ filename }}')
        {% if not loop.last %}
            union all by name
        {% endif %}
    {% endfor %}
)
{% endmacro %}

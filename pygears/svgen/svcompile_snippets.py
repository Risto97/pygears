import jinja2


@jinja2.contextfilter
def call_macro_by_name(context, macro_name, *args, **kwargs):
    return context.vars[macro_name](*args, **kwargs)


qrange_mux_impl = '''
{% macro qrange(iter_name, iter_reg, flag_name, rng) %}

if {{flag_name}}:
    {{iter_name}} = {{iter_reg}}
else:
    {{iter_name}} = {{rng[0]}}

{{iter_reg}} = {{iter_name}} + {{rng[2]}}

{{flag_name}} = True

{% endmacro %}
'''

jenv = jinja2.Environment()
jenv.filters['macro'] = call_macro_by_name

qrange = jenv.from_string(qrange_mux_impl).module.qrange

enumerate_str = '''
{% macro enumerate_macro(idx_name, iter_name, var_name, rng) %}

if {{idx_name}} == 0:
    {{iter_name}} = {{var_name}}0
{% for i in rng %}
elif {{idx_name}} == {{i}}:
    {{iter_name}} = {{var_name}}{{i}}
{% endfor %}

{% endmacro %}
'''

enumerate_impl = jenv.from_string(enumerate_str).module.enumerate_macro

from pygears.conf import registry
from pygears.typing.base import Any, GenericMeta, type_repr, typeof


class TypeMatchError(Exception):
    pass


def _type_match_rec(t, pat, matches):

    # Ignore type template arguments, i.e.: 'T2' in Tuple[1, 2, 3, 'T2']
    if isinstance(t, str):
        return t

    if (t == Any) or (pat == Any):
        return t

    if t == pat:
        return t

    # Did we reach the parameter name?
    if isinstance(pat, str):
        if pat in matches:
            # If the parameter name is already bound, check if two deductions
            # are same
            if repr(t) != repr(
                    matches[pat]) and t != Any and matches[pat] != Any:
                raise TypeMatchError(
                    f'Ambiguous match for parameter "{pat}": {type_repr(t)} '
                    f"and {type_repr(matches[pat])}")
        else:
            try:
                res = eval(pat, registry('gear/type_arith'), matches)
                if repr(t) != repr(res):
                    raise TypeMatchError(
                        f"{type_repr(t)} cannot be matched to {type_repr(res)}"
                    )
            except Exception as e:
                matches[pat] = t

        return t

    if (isinstance(t, GenericMeta) and isinstance(pat, GenericMeta)
            and (typeof(t.base, pat.base))):

        if pat.args:
            args = []
            for ta, pa in zip(t.args, pat.args):
                try:
                    res = _type_match_rec(ta, pa, matches)
                    args.append(res)
                except TypeMatchError as e:
                    raise TypeMatchError(
                        f'{str(e)}\n - when matching {repr(t)} to {repr(pat)}')

            # if hasattr(pat, '__parameters__'):
            args = {name: a for name, a in zip(pat.fields, args)}
        else:
            args = t.args

        # TODO: Revisit this Don't create a new type class when class has no
        # specified templates, so that we don't end up with multiple different
        # base class objects, that cannot be correctly tested with "issubclass"
        if not args and not t.args:
            return t
        else:
            return t.__class__(t.__name__,
                               t.__bases__,
                               dict(t.__dict__),
                               args=args)

    raise TypeMatchError("{} cannot be matched to {}".format(
        type_repr(t), type_repr(pat)))


def type_match(t, pat, matches=None):
    if matches is None:
        matches = {}
    else:
        matches = dict(matches)

    res = _type_match_rec(t, pat, matches)
    return matches, res

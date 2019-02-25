from pygears.hls.hdl_utils import add_to_list
from pygears.typing.visitor import TypingVisitorBase


class VGenTypeVisitor(TypingVisitorBase):
    def __init__(self, name, basic_type='wire', hier=True):
        self.context = name
        self.basic_type = basic_type
        self.hier = hier

    def visit_int(self, type_, field, **kwds):
        return [
            f'{self.basic_type} signed [{int(type_)-1}:0] {self.context}; // {type_}'
        ]

    def visit_bool(self, type_, field, **kwds):
        return [f'{self.basic_type} [0:0] {self.context}; // {type_}']

    def visit_uint(self, type_, field, **kwds):
        if int(type_) != 0:
            return [
                f'{self.basic_type} [{int(type_)-1}:0] {self.context}; // {type_}'
            ]

        return None

    def visit_unit(self, type_, field, **kwds):
        return None

    def visit_union(self, type_, field, **kwds):
        assert False, f'Unions not supported in Verilog'

    def visit_queue(self, type_, field, **kwds):
        res = []
        parent_context = self.context

        # top
        res.append(
            f'{self.basic_type} [{int(type_)-1}:0] {parent_context}; // {type_}'
        )

        if self.hier:
            # eot
            res.append(
                f'{self.basic_type} [{type_.args[1]-1}:0] {parent_context}_eot; // u{type_.args[1]}'
            )
            eot_low = int(type_) - int(type_.args[1])
            eot_high = int(type_) - 1
            res.append(
                f'assign {parent_context}_eot = {parent_context}[{eot_high}:{eot_low}];'
            )

            # data
            self.context = f'{parent_context}_data'

            sub = self.visit(type_.args[0], type_.fields[0])
            if sub:
                add_to_list(res, sub)
                res.append(
                    f'assign {self.context} = {parent_context}[{eot_low-1}:0];'
                )

        self.context = parent_context
        return res

    def visit_tuple(self, type_, field, **kwds):
        res = []
        parent_context = self.context
        high = 0
        low = 0
        if self.hier:
            for sub_t, sub_f in zip(type_.args, type_.fields):
                high += int(sub_t)

                self.context = f'{parent_context}_{sub_f}'
                sub = self.visit(sub_t, sub_f)
                if sub:
                    add_to_list(res, sub)
                    res.append(
                        f'assign {self.context} = {parent_context}[{high - 1}:{low}];'
                    )

                low += int(sub_t)

            self.context = parent_context
        if res or (not self.hier):
            res.append(
                f'{self.basic_type} [{int(type_)-1}:0] {self.context}; // {type_}'
            )

        return res

    def visit_array(self, type_, field, **kwds):
        assert False, f'Arrays not supported in Verilog'
        # TODO : below is systemverilog syntax, not pure verilog..
        # sub = self.visit(type_.args[0], type_.fields[0])
        # if sub:
        #     assert len(sub) == 1
        #     split_type = sub[0].split(' ', 1)
        #     split_type.insert(1, f'[{type_.args[1]-1}:0]')
        #     type_declaration = ' '.join(split_type)
        #     res = type_declaration.split('//')[0]
        #     return [f'{res} // {type_}']

        # return None


def vgen_intf(dtype, name, hier=True):
    valid = f'reg {name}_valid;\n'
    ready = f'reg {name}_ready;'

    if isinstance(dtype, str):
        data = f'{dtype} {name}_data;\n'
        return data + valid + ready

    if int(dtype) == 0:
        data = f'wire [0:0] {name}_data;\n'
        return data + valid + ready

    vis = VGenTypeVisitor(name, 'wire', hier)
    data = '\n'.join(vis.visit(type_=dtype, field=name)) + '\n'
    return data + valid + ready


def vgen_reg(dtype, name, hier=True):
    if isinstance(dtype, str):
        return f'{dtype} {name};'

    if int(dtype) == 0:
        return f'reg [0:0] {name};'

    vis = VGenTypeVisitor(name, 'reg', hier)
    return '\n'.join(vis.visit(type_=dtype, field=name))


def vgen_wire(dtype, name, hier=True):
    if isinstance(dtype, str):
        return f'{dtype} {name};'

    if int(dtype) == 0:
        return f'wire [0:0] {name};'

    vis = VGenTypeVisitor(name, 'wire', hier)
    return '\n'.join(vis.visit(type_=dtype, field=name))
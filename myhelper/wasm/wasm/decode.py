"""Provides functions for decoding WASM modules and bytecode."""
from __future__ import print_function, absolute_import, division, unicode_literals

from collections import namedtuple
from .modtypes import ModuleHeader, Section, SEC_UNK, SEC_NAME, NameSubSection
from .opcodes import OPCODE_MAP
from .compat import byte2int


from .modtypes import (TypeSection,
                           ImportSection,
                           FunctionSection,
                           TableSection,
                           MemorySection,
                           GlobalSection,
                           ExportSection,
                           StartSection,
                           ElementSection,
                           CodeSection,
                           DataSection)


Instruction = namedtuple('Instruction', 'op imm len')
ModuleFragment = namedtuple('ModuleFragment', 'type data')


def decode_bytecode(bytecode):
    """Decodes raw bytecode, yielding `Instruction`s."""
    bytecode_wnd = memoryview(bytecode)
    while bytecode_wnd:
        opcode_id = byte2int(bytecode_wnd[0])
        opcode = OPCODE_MAP[opcode_id]

        if opcode.imm_struct is not None:
            offs, imm, _ = opcode.imm_struct.from_raw(None, bytecode_wnd[1:])
        else:
            imm = None
            offs = 0

        insn_len = 1 + offs
        yield Instruction(opcode, imm, insn_len)
        bytecode_wnd = bytecode_wnd[insn_len:]


def decode_module(module, decode_name_subsections=False):
    """Decodes raw WASM modules, yielding `ModuleFragment`s."""
    module_wnd = memoryview(module)

    # Read & yield module header.
    hdr = ModuleHeader()
    hdr_len, hdr_data, _ = hdr.from_raw(None, module_wnd)
    yield ModuleFragment(hdr, hdr_data)
    module_wnd = module_wnd[hdr_len:]

    # Read & yield sections.
    while module_wnd:
        sec = Section()
        sec_len, sec_data, _ = sec.from_raw(None, module_wnd)

        # an ugly hack way to get the real offset
        if isinstance(sec_data.get_decoder_meta()['types']['payload'], DataSection):
            # deal with code
            data_bytes = module_wnd.tobytes()
            # print(data_bytes)

            for idx, entry in enumerate(sec_data.payload.entries):
                const_idx = data_bytes[const_idx:].index(entry.data.tobytes()) + const_idx
                # print(const_idx)
                sec_data_tmp = data_bytes[:const_idx]
                const_start_idx = 0
                while b'\x41' in sec_data_tmp:
                    const_start_idx = sec_data_tmp.index(b'\x41')
                    sec_data_tmp = sec_data_tmp[(const_start_idx + 1):]
                const_end_idx = sec_data_tmp.index(b'\x0b')
                sec_data_tmp = bytearray(b'\x41') + sec_data_tmp[:(const_end_idx + 1)]

                #             for insn in decode_bytecode(sec_data):
                #                 print([
                #     getattr(insn.op.imm_struct, x.name).to_string(
                #         getattr(insn.imm, x.name)
                #     )
                #     for x in insn.op.imm_struct._meta.fields
                # ])
                # mod_iter = iter(decode_bytecode(sec_data))
                # instrs = next(mod_iter)
                # for instr in mod_iter:
                #      print(format_instruction(instr))

                # print(sec_data_tmp)
                sec_data.payload.entries[idx].offset = sec_data_tmp
                entry.offset = sec_data_tmp


        # If requested, decode name subsections when encountered.
        if (
            decode_name_subsections and
            sec_data.id == SEC_UNK and
            sec_data.name == SEC_NAME
        ):
            sec_wnd = sec_data.payload
            while sec_wnd:
                subsec = NameSubSection()
                subsec_len, subsec_data, _ = subsec.from_raw(None, sec_wnd)
                yield ModuleFragment(subsec, subsec_data)
                sec_wnd = sec_wnd[subsec_len:]
        else:
            yield ModuleFragment(sec, sec_data)

        module_wnd = module_wnd[sec_len:]

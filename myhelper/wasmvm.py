from struct import *
import logging

from .graph import *
from .tools import *

import collections

class StackItem:
    def __init__(self, _value = 0):
         self.value = _value
    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, StackItem):
            return self.value == other.value
        else:
            return self.value == other
    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)
    def __str__(self):
        return str(self.value)
    def __int__(self):
        return self.value

class Stack(collections.MutableSequence):

    def __init__(self, *args):
        self.list = list()
        self.extend(list(args))

    def __len__(self): return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __delitem__(self, i): del self.list[i]

    def __setitem__(self, i, v):
        print("setitem")
        self.list[i].value = v

    def insert(self, i, v):
        if isinstance(v, StackItem):
            self.list.insert(i, v)
        else:
            item = StackItem()
            item.value = v
            self.list.insert(i, item)

    def __str__(self):
        strStack = list(i.value for i in self.list)
        return str(strStack)

class WasmVM(object):

    def __init__(self, cfg, func_map):
        self.mem_tb = {}
        self.globals = {}
        self.size_stack = 0
        self.stack = Stack()
        self.cfg = cfg
        self.func_map = func_map

        self.indirect_targets = []
        self.send_inline_hit = False
        self.dubiousCmp = False
        self.dubiousFunc = -1

        self.globals['$G0'] = 8192

        self.memAddr = 0

    def trace_func(self, path_blocks, args = list(), focus_funcs=list()):

        locals = {}  # keep local variables
        for i in range(0, len(args)):
            locals["$L" + str(i)] = args[i]

        self.trace_blocks(path_blocks, locals, focus_funcs)


    def trace_blocks(self, blocks, locals = dict(), focus_funcs = list(), recursion = False):
        logging.debug(list(b.name for b in blocks))
        logging.debug(self.mem_tb)

        path_instrs = []
        for b in blocks:
            path_instrs.extend(b.instructions)

        for i in path_instrs:
            logging.debug(str(self.size_stack)  + str(self.stack) + str(i) )
            # print(self.mem_tb)
            # record the size_stack
            if i.name != "call":
                self.size_stack -= i.pops
                self.size_stack += i.pushes

            if i.name in ["unreachable", "nop", "block", "loop", "else", "end", "br"]:
                pass
            elif i.name == "if":
                self.stack.pop()
            elif i.name == "br_if":
                self.stack.pop()
            elif i.name == "br_table":
                self.stack.pop()
            elif i.name == "return":
                self.stack.pop()

            elif i.name == "drop":
                self.stack.pop()
            elif i.name == "select":
                c = self.stack.pop()
                val2 = self.stack.pop()
                val1 = self.stack.pop()
                if int(c) != 0:
                    self.stack.append(val1)
                else:
                    self.stack.append(val2)
            elif i.name == "get_local":
                if "$L" + str(i.operand_interpretation.split(" ")[-1]) in locals:
                    obj = locals["$L" + str(i.operand_interpretation.split(" ")[-1])]
                    item = StackItem()
                    if isinstance(obj, StackItem):
                        item = obj
                    else:
                        item.value = int(obj)
                elif i.operand_interpretation == "get_local 2":
                    item = StackItem()
                    item.value = 0
                    item.type = "TO"
                else:
                    item = StackItem()
                    item.value = 0
                    item.type = "UNKNOWN"
                # item.type = "LOCAL"
                item.allies = "$L" + str(i.operand_interpretation.split(" ")[-1])
                self.stack.append(item)
            elif i.name == "set_local":
                locals["$L" + str(i.operand_interpretation.split(" ")[-1])] = self.stack.pop()
            elif i.name == "tee_local":
                locals["$L" + str(i.operand_interpretation.split(" ")[-1])] = self.stack[-1]

            elif i.name == "get_global":
                self.stack.append(self.globals["$G" + str(i.operand_interpretation.split(" ")[-1])])
            elif i.name == "set_global":
                self.globals["$G"+ str(i.operand_interpretation.split(" ")[-1])] = self.stack.pop()
            elif i.name == "i32.load":
                addr_operand = self.stack.pop()
                if (int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)) in self.mem_tb:
                    val = self.mem_tb[int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)]
                    val = unpack('i', val)[0]
                    self.stack.append(val)
                else:
                    self.stack.append(0)
            elif i.name == "i32.load8_u":
                addr_operand = self.stack.pop()
                if (int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)) in self.mem_tb:
                    val = self.mem_tb[int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)]
                    val = unpack('i', val)[0]
                    self.stack.append(val)
                else:
                    self.stack.append(0)
            elif i.name == "i64.load":

                addr_operand = self.stack.pop()
                ef_addr1 = int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)
                ef_addr2 = (4 + int(i.operand_interpretation.split(" ")[-1])) + int(addr_operand)

                item = StackItem()
                item.memAddr = ef_addr1
                if hasattr(addr_operand, "allies") and addr_operand.allies == "$L0" \
                        and i.operand_interpretation == "i64.load 3, 0":
                    item.type = "SELF"
                else:
                    item.type = "MEM_V"

                item.op = i.operand_interpretation
                if ef_addr1 in self.mem_tb:
                    val = self.mem_tb[ef_addr1]

                    if ef_addr2 in self.mem_tb:
                        val = val + self.mem_tb[ef_addr2]

                    else:
                        val = val + pack('i', 0)

                    val = unpack('q', val)[0]
                    item.value = val
                    self.stack.append(item)
                else:
                    item.value = 0
                    self.stack.append(item)
            elif i.name == "i32.store":
                val = self.stack.pop()
                val = pack('i', int(val))
                addr_operand = self.stack.pop()
                self.mem_tb[int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)] = val
            elif i.name == "i64.store":  # TODO: 64bit
                val = self.stack.pop()
                val = pack('q', int(val))
                addr_operand = self.stack.pop()
                self.mem_tb[int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand)] = val[:4]
                self.mem_tb[int(i.operand_interpretation.split(" ")[-1]) + int(addr_operand) + 4] = val[4:]

            elif i.name in ["i32.const", "i64.const"]:
                self.stack.append(int(i.operand_interpretation.split(" ")[-1]))
            elif i.name in ["i32.eqz", "i64.eqz"]:
                op = int(self.stack.pop())
                if op == "unknown":
                    self.stack.append(0)
                    continue

                if op in locals:
                    op = locals[op]

                if int(op) == 0:
                    self.stack.append(1)
                else:
                    self.stack.append(0)
            elif i.name in ["i32.eq", "i64.eq", "i32.ne", "i64.ne"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                # print(hex(i.offset), i.name, op1, op2)
                # if hasattr(op1, 'type'):
                #     print("op1", op1.type)
                #     if op1.type == 'MEM_V':
                #         print("memAddr", op1.memAddr)
                # if hasattr(op2, 'type'):
                #     print("op2", op2.type)
                #     if op2.type == 'MEM_V':
                #         print("memAddr", op2.memAddr)
                if hasattr(op1, 'type') and op1.type == 'SELF' and hasattr(op2, 'type') and ((op2.type == 'MEM_V' and op2.memAddr == int(self.dubiousFunc) + 8) or (op2.type == "TO")) \
                or hasattr(op2, 'type') and op2.type == 'SELF' and hasattr(op1, 'type') and ((op1.type == 'MEM_V' and op1.memAddr == int(self.dubiousFunc) + 8) or (op1.type == "TO")):
                    self.dubiousCmp = True
                # if(op1 == op2)
                self.stack.append(0)
            # elif i.name in ["i32.ne", "i64.ne"]:
            #     op2 = self.stack.pop()
            #     op1 = self.stack.pop()
            #     # print(i.name, op1, op2)
            #     # if hasattr(op1, 'type'):
            #     #     print("op1", op1.type)
            #     #     if op1.type == 'MEM_V':
            #     #         print("memAddr", op1.memAddr)
            #     # if hasattr(op2, 'type'):
            #     #     print("op2", op2.type)
            #     #     if op2.type == 'MEM_V':
            #     #         print("memAddr", op2.memAddr)
            #     if op1 == op2:
            #         self.stack.append(0)
            #     else:
            #         self.stack.append(1)
            elif i.name in ["i32.lt_u", "i64.lt_u"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                if int(op1) < int(op2):
                    self.stack.append(1)
                else:
                    self.stack.append(0)
            elif i.name in ["i32.gt_u", "i64.gt_u"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                if int(op1) > int(op2):
                    self.stack.append(1)
                else:
                    self.stack.append(0)
            elif i.name in ["i32.le_s", "i64.le_s"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                if int(op1) < int(op2):
                    self.stack.append(1)
                else:
                    self.stack.append(0)
            elif i.name in ["i32.mul", "i64.mul"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                self.stack.append(int(op1) * int(op2))
            elif i.name in ["i32.ge_u","i64.ge_u","i32.shl", "i64.shl","i32.shr_s","i64.shr_s"]:
                self.stack.pop()
            elif i.name in ["i32.add", "i64.add"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                if int(op2) in locals:
                    op2 = locals[int(op2)]
                if int(op1) in locals:
                    op1 = locals[int(op1)]
                if op1 == "unknown" or op2 == "unknown":
                    self.stack.append(0)#TODO
                else:
                    self.stack.append(int(op1) + int(op2))


            elif i.name in ["i32.sub", "i64.sub"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                self.stack.append(int(op1) - int(op2))

            elif i.name in ["i32.and", "i64.and"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                if int(op2) in locals:
                    op2 = locals[int(op2)]
                if int(op1) in locals:
                    op1 = locals[int(op1)]
                self.stack.append(int(op1) & int(op2))
            elif i.name in ["i32.or", "i64.or"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                self.stack.append(int(op1) | int(op2))
            elif i.name in ["i32.xor", "i64.xor"]:
                op2 = self.stack.pop()
                op1 = self.stack.pop()
                self.stack.append(int(op1) ^ int(op2))


            elif i.name == "call":
                f_idx = int(i.operand_interpretation.split(" ")[-1])

                if self.func_map[f_idx][3] != "import":
                    pops_n = len(list(filter(None, self.func_map[f_idx][1].split(" "))))
                    pushs_n = len(list(filter(None, self.func_map[f_idx][2].split(" "))))

                    args_next = []
                    if self.func_map[focus_funcs[0]][0] == "eosio_assert":
                        print("assert block when", i.operand_interpretation)#这个log出来的才是对dubious func的call的指令
                        if pops_n == 1 and pushs_n == 0:
                            #record the input// if input is a addr of mem
                            print("dubious func: ", self.stack[-1]) #这个log出来的其实应该是from的地址
                            self.dubiousFunc = self.stack[-1]

                    for n in range(0, pops_n):
                        #print("pops_n", pops_n)
                        args_next.append(self.stack.pop())
                        self.size_stack -= self.size_stack

                    if f_idx in focus_funcs and pops_n > 0:
                        #print("//=============== enter the ", self.func_map[f_idx][0], "\n")

                        #next_blocks = self.cfg.func_paths_map[func_map[f_idx][0]][-1][0]
                        #trace_func_path(cfg, next_blocks, args_next, focus_funcs)
                        # print("//=============== leave the ", func_map[f_idx][0], "\n")
                        if recursion:
                            f_next_name = self.func_map[f_idx][0]
                            logging.debug("//===================enter the " + f_next_name + "\n")
                            next_paths = get_func_paths(self.cfg, f_next_name)
                            for p in next_paths[:1]:
                                self.trace_func(p, args_next, focus_funcs)
                                logging.debug("//===================leave the " + f_next_name + "\n")

                        else:
                            #print("idx in focus func", f_idx)
                            try:

                                indirect_target = unpack("i", self.mem_tb[int(args_next[0])])[0]
                               # print("indirect target",indirect_target)
                                f_pts = self.cfg.analyzer.elements[0].get('elems')
                              #  print(self.cfg.analyzer.elements[0].get('offset'))
                                start_idx = 1
                                for f in self.cfg.functions:
                                    if f.name == self.func_map[f_pts[0]][0]:
                                        #print(list(i.name for i in f.instructions))
                                        if len(f.instructions) == 2 and f.instructions[0].name == "unreachable" and f.instructions[1].name == "end":
                                            start_idx = 0
                                            break
                                if not f_pts[indirect_target - start_idx] in self.indirect_targets:
                                    self.indirect_targets.append(f_pts[indirect_target - start_idx])
                            except:
                                #print("try fail", f_idx)
                                pass

                            # for paths in func_paths_map[func_map[f_idx][0]]:
                            #     for path in paths:
                            #
                            #         #next_blocks = func_paths_map[func_map[f_idx][0]][-1][0]
                            #         print(args_next)
                            #         print(colored(unpack("i", _mem_tb[int(args_next[0])])[0],"red"))
                            #         stack_tmp = stack.copy()
                            #         size_stack_tmp = size_stack
                            #         _mem_tb_tmp = _mem_tb.copy()
                            #         trace_func_path(cfg, path, args_next, focus_funcs)
                            #         stack = stack_tmp.copy()
                            #         size_stack = size_stack_tmp
                            #         _mem_tb = _mem_tb_tmp.copy()
                            #         print("//=============== leave the ", func_map[f_idx][0], "\n")


                    #else:
                    self.size_stack += pushs_n
                    for n in range(0, pushs_n):
                        self.stack.append(0)

                else:
                    if f_idx in focus_funcs:
                        self.send_inline_hit = True
                        logging.debug(self.stack)
                        logging.debug(self.mem_tb)
                    pops_n = len(list(filter(None, self.func_map[f_idx][1].split(" "))))
                    self.size_stack -= pops_n
                    for n in range(0, pops_n):
                        self.stack.pop()
                    pushs_n = len(list(filter(None, self.func_map[f_idx][2].split(" "))))
                    self.size_stack += pushs_n
                    for n in range(0, pushs_n):
                        self.stack.append(0)


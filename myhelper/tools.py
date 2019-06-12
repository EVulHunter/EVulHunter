from octopus.core.edge \
    import (EDGE_UNCONDITIONAL,
            EDGE_CONDITIONAL_TRUE, EDGE_CONDITIONAL_FALSE,
            EDGE_FALLTHROUGH, EDGE_CALL)
from .graph import *

def get_common_edges(a = list(), b = list()):
    common = list()
    if len(a) and len(b):
        for ai in a:
            for bi in b:
                if ai == bi:
                    common.append(ai)
    return common


def enum_func_call_edges(functions, len_imports):
    # return a list of tuple with
    #   (index_func_node_from, index_func_node_to)

    call_edges = list()
    N_FUNCS = len_imports + len(functions)
    # iterate over functions
    for index, func in enumerate(functions):
        node_from = len_imports + index
        # iterates over instruction
        for inst in func.instructions:
            # detect if inst is a call instructions
            if inst.name == "call":  # is_call:
                # print(inst.operand_interpretation)
                # if inst.name == "call":
                # only get the import_id

                import_id = inst.operand_interpretation.split(' ')[1]
                if import_id.startswith('0x'):
                    import_id = int(import_id, 16)
                else:
                    import_id = int(import_id)
                node_to = int(import_id)
                call_edges.append((node_from, node_to))
            # The `call_indirect` operator takes a list of function arguments and as the last operand the index into the table.
            elif inst.name == "call_indirect":
                # the last operand is the index on the table
                # print(inst.operand_interpretation)
                # print(type(inst.insn_byte[1]))
                # print(func.name)
                node_to = int(inst.operand_interpretation.split(',')[-1].split(' ')[
                                  -1])  # node_to is the table of functions to index into.(http://fitzgeraldnick.com/2018/04/26/how-does-dynamic-dispatch-work-in-wasm.html)
                call_edges.append((node_from, N_FUNCS))

    return call_edges

def gen_f_param(cfg, f_name):
    f_blocks = list(b for f in cfg.functions for b in f.basicblocks if f.name == f_name)  # entire block
    f_edges = list(e for e in cfg.edges if e.node_from in list(b.name for b in f_blocks))  # entire
    return f_blocks, f_edges

def gen_g_param(f_blocks, f_edges):
    g_nodes = list(b.name for b in f_blocks)
    g_edges = []
    for e in f_edges:
        g_edges.append((e.node_from, e.node_to))
    return g_nodes, g_edges

def gen_func_graph_params(cfg, f_name):
    f_blocks, f_edges = gen_f_param(cfg, f_name)
    g_nodes, g_edges = gen_g_param(f_blocks, f_edges)
    return f_blocks, f_edges, g_nodes, g_edges


def get_conditional_edges(func_edges, func_blocks): #return edges name
    edges_eosio_token_false = func_edges.copy()  # $local_1: code != eosio.token
    edges_eosio_token_true = func_edges.copy()
    edges_transfer_true = func_edges.copy()  # $local_2: action == transfer
    edges_transfer_false = func_edges.copy()

    for e in func_edges:
        block_from = list(b for b in func_blocks if b.name == e.node_from)[0]
        # block_to = list(b for b in t_blocks if b.name == e.node_to)[0]
        last_instr = block_from.end_instr
        instrs = block_from.instructions

        if last_instr.is_branch_conditional:
            if last_instr.name == "br_if":
                if instrs[-2].name == "i64.eq":
                    # $local_1: code
                    if "get_local 1" in (str(instrs[-3]), str(instrs[-4])):
                        # code = "eosio.token"
                        if "i64.const 6138663591592764928" in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_eosio_token_true and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_eosio_token_true.remove(e)
                            if e in edges_eosio_token_false and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_eosio_token_false.remove(e)
                        # code = "something else" and "something else" != receiver
                        elif "i64.const" in (instrs[-3].name, instrs[-4].name) or "get_local" in (instrs[-3].name, instrs[-4].name)\
                                and "get_local 0" not in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_eosio_token_true and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_eosio_token_true.remove(e)
                            if e in edges_eosio_token_false and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_eosio_token_false.remove(e)
                    # $local_2: action
                    elif "get_local 2" in (str(instrs[-3]), str(instrs[-4])):
                        # action = "transfer"
                        if "i64.const -3617168760277827584" in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_transfer_false and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_transfer_false.remove(e)
                            if e in edges_transfer_true and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_transfer_true.remove(e)
                        # action = "something else"
                        elif "i64.const" in (instrs[-3].name, instrs[-4].name):
                            if e in edges_transfer_true and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_transfer_true.remove(e)
                elif instrs[-2].name == "i64.ne":
                    # $local_1 : code
                    if "get_local 1" in (str(instrs[-3]), str(instrs[-4])):
                        # code != "eosio.token"
                        if "i64.const 6138663591592764928" in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_eosio_token_true and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_eosio_token_true.remove(e)
                            if e in edges_eosio_token_false and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_eosio_token_false.remove(e)
                        # code != "something else" and "something else" != receiver
                        elif "i64.const" in (instrs[-3].name, instrs[-4].name) or "get_local" in (instrs[-3].name, instrs[-4].name) \
                                and "get_local 0" not in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_eosio_token_true and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_eosio_token_true.remove(e)
                            if e in edges_eosio_token_false and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_eosio_token_false.remove(e)
                    # $local_2 : action
                    elif "get_local 2" in (str(instrs[-3]), str(instrs[-4])):
                        # action != "transfer"
                        if "i64.const -3617168760277827584" in (str(instrs[-3]), str(instrs[-4])):
                            if e in edges_transfer_true and e.type == EDGE_CONDITIONAL_TRUE:
                                edges_transfer_true.remove(e)
                            if e in edges_transfer_false and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_transfer_false.remove(e)
                        # action != "something else"
                        elif "i64.const" in (instrs[-3].name, instrs[-4].name):
                            if e in edges_transfer_true and e.type == EDGE_CONDITIONAL_FALSE:
                                edges_transfer_true.remove(e)


            elif last_instr.name == "if":
                # TODO
                pass
            elif last_instr.name == "br_table":
                # TODO
                pass


    return edges_eosio_token_false, edges_eosio_token_true, edges_transfer_true,edges_transfer_false

def get_paths_to_target(paths, func_blocks, focus_funcs):
    # return the paths_foucs in paths which will lead to indirectly call func in focus funcs
    paths_focus = []
    block_focus = []
    for p in paths:
        for b_name in p:
            block = list(b for b in func_blocks if b.name == b_name)[0]
            for i in block.instructions:
                if i.name == "call" and int(i.operand_interpretation.split(" ")[-1]) in focus_funcs:
                    paths_focus.append(p)
                    block_focus.append(block)
                    break
    return paths_focus, block_focus


def get_indirect_targets(wasmvm, paths_focus, func_blocks, func_args, focus_funcs):
    # TODO: refine the paths
    for p_C1_paths_focus in paths_focus:
        path_blocks = []
        for b_name in p_C1_paths_focus:
            block = list(b for b in func_blocks if b.name == b_name)[0]
            path_blocks.append(block)
        wasmvm.trace_func(path_blocks, func_args, focus_funcs)
        # print(wasmvm.indirect_targets)

def blocks_name_to_blocks(blocks_name = list(), func_blocks = list()):
    blocks = []
    for b_name in blocks_name:
        block = list(b for b in func_blocks if b.name == b_name)[0]
        blocks.append(block)
    return blocks


def get_func_paths(cfg, f_name):
    func_blocks, func_edges, graph_nodes, graph_edges = gen_func_graph_params(cfg, f_name)
    graph = Graph(graph_nodes, graph_edges)

    # get all possible paths in the above graph
    # TODO:get all the possible end node
    paths = graph.depth_first_search_path(graph_nodes[0], graph_nodes[-1])
    paths_blocks = []
    for p in paths:
        p_blocks = blocks_name_to_blocks(p, func_blocks)
        paths_blocks.append(p_blocks)
    return paths_blocks

def gen_funcs_call_graph(cfg, N_FUNCS):
    call_edges = enum_func_call_edges(cfg.functions, len(cfg.analyzer.imports_func))
    funcs_idx = list(range(0, N_FUNCS + 1))  # N_FUNCS is the indirect call target
    funcs_edges = []
    for e in call_edges:
        funcs_edges.append((e[0], e[1]))
    return Graph(funcs_idx, funcs_edges)


def isGetSelf(instr, func_name, cfg):
    localVarId = instr.operand_interpretation.split(" ")[-1]
    # print(localVarId)
    func_instrs = list(f.instructions for f in cfg.functions if f.name == func_name)[0]
    for i in range(0, len(func_instrs)):
        if "get_local " + localVarId == func_instrs[i].operand_interpretation \
                or "tee_local " + localVarId == func_instrs[i].operand_interpretation:
            # print(func_instrs[i].operand_interpretation, func_instrs[i - 2].operand_interpretation, func_instrs[i - 1].operand_interpretation)
            if func_instrs[i - 2].operand_interpretation == "get_local 0" and \
                    func_instrs[i - 1].operand_interpretation == "i64.load 3, 0":
                return True
        if func_instrs[i] is instr:  # why not "==" ?
            # print(hex(instr.offset), hex(func_instrs[i].offset), func_instrs[i] == instr)
            break
    return False
import logging, sys, getopt

from octopus.platforms.EOS.cfg import EosCFG
from octopus.core.edge \
    import (EDGE_UNCONDITIONAL,
            EDGE_CONDITIONAL_TRUE, EDGE_CONDITIONAL_FALSE,
            EDGE_FALLTHROUGH, EDGE_CALL)

from myhelper.graph import Graph
from myhelper.tools import *
from myhelper.wasmvm import *


# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def usage():
    print(
        '''
        usage: python3 EOSVulDetector.py -i|--input <FILEPATH> -t|--type <VUL TYPE>
        VUL TYPE:
        1   FALSE EOS TRANSFER
        2   FALSE RECEIPT TRANSFER
        '''
    )


def main(argv):
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:t:h', ['input', 'type', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ['-h', '--help']:
            usage()
        elif opt in ['-i', '--input']:
            file_name = arg
        elif opt in ['-t', '--type']:
            vul_type = arg
        else:
            print("Error: invalid parameters")
            usage()
            sys.exit()

    print("Detector start!")
    print(file_name, vul_type)
    EOSVuldetect(file_name, vul_type)
    print("")


def EOSVuldetect(file_name, vul_type):
    with open(file_name, 'rb') as f:
        raw = f.read()
    cfg = EosCFG(raw)

    # a list to map the func idx and the func name eg: func_map[14]="apply"
    func_proto = cfg.analyzer.get_func_prototypes_ordered()
    func_map = list()
    for f_idx in func_proto:
        func_map.append(f_idx)

    N_FUNCS = len(func_map)

    send_inline_idx = None
    send_deferred_idx = None
    for f in func_map:
        if f[0] == "send_inline":
            send_inline_idx = func_map.index(f)
        if f[0] == "send_deferred":
            send_deferred_idx = func_map.index(f)
        if f[0] == "eosio_assert":
            assert_idx = func_map.index(f)
    print("the index of send_inline is ", send_inline_idx)
    print("the index of send_deferred is ", send_deferred_idx)
    print("the index of eosio_assert is ", assert_idx)

    apply_args = [0, 6138663591592764928, -3617168760277827584]

    # get blocks graph of apply func

    # get all possible paths in the above graph

    # get only the relevant paths

    # get the graph of all the functions

    # get all paths in the above graph, where the start is apply and the terminal is indirect call

    # get the focused f(s)

    # trace the blocks, get the indirect_call func idx (my-f)

    # get blocks graph of my-f

    # get all possible paths in my-f

    # trace all possible paths

    # if send_inline exists, get the para

    # ======================================================#
    # get blocks graph in apply func

    # apply_paths = get_func_paths(cfg, "apply")

    # get only the relevant paths
    # for p in paths:
    #     logging.debug("path")
    #     for b in p:
    #         logging.debug(b)
    func_apply_blocks, func_apply_edges = gen_f_param(cfg, "apply")

    edges_eosio_token_false, edges_eosio_token_true, edges_transfer_true, edges_transfer_false \
        = get_conditional_edges(func_apply_edges, func_apply_blocks)

    # print(len(func_apply_edges))
    # =======================================================#
    #   C1  ||  code != eosio.token && action == transfer   #
    #   C2  ||  code == eosio.token && action == transfer   #
    # =======================================================#
    C1_edges = get_common_edges(edges_eosio_token_false, edges_transfer_true)
    C2_edges = get_common_edges(edges_eosio_token_true, edges_transfer_true)

    print("eosio token false: ", len(edges_eosio_token_false))
    print("eosio token true: ", len(edges_eosio_token_true))
    print("action true: ", len(edges_transfer_true))
    print("action false: ", len(edges_transfer_false))
    # print("eosio token common: ", len(get_common_edges(edges_eosio_token_true, edges_eosio_token_false)))
    # print("C1, C2 edges gotton!")
    graph_apply_nodes, graph_C1_edges = gen_g_param(func_apply_blocks, C1_edges)
    graph_C1 = Graph(graph_apply_nodes, graph_C1_edges)
    # print(len(graph_apply_nodes), len(graph_C1_edges))
    # print("C1 graph created!")
    C1_paths = graph_C1.depth_first_search_path(graph_apply_nodes[0], graph_apply_nodes[-1])
    print("C1 paths searched!", len(C1_paths))

    graph_apply_nodes, graph_C2_edges = gen_g_param(func_apply_blocks, C2_edges)
    graph_C2 = Graph(graph_apply_nodes, graph_C2_edges)
    # print(len(graph_apply_nodes), len(graph_C2_edges))

    # print("C2 graph created!")

    print("common c1 and c2 edges:", len(get_common_edges(graph_C1_edges, graph_C2_edges)))
    C2_paths = graph_C2.depth_first_search_path(graph_apply_nodes[0], graph_apply_nodes[-1])
    print("C2 paths searched!", len(C2_paths))

    # get all possible paths in the above graph

    # for p in paths_eosio_token_false:
    #     logging.debug("eosio token false path")
    #     for b in p:
    #         logging.debug(b)
    #
    # for p in paths_transfer_true:
    #     logging.debug("transfer true path")
    #     for b in p:
    #         logging.debug(b)
    #
    # for p in C1_paths:
    #     logging.info("C1 relevant path")
    #     for b in p:
    #         logging.info(b)
    #
    # for p in C2_paths:
    #     logging.info("C2 relevant path")
    #     for b in p:
    #         logging.info(b)

    # get the graph of functions being called
    graph_funcs = gen_funcs_call_graph(cfg, N_FUNCS)

    # get all paths in the above graph, where the start is apply and the terminal is indirect call target
    apply_idx = list(f[0] for f in func_map).index("apply")
    paths_indirect_call = graph_funcs.depth_first_search_path(apply_idx, N_FUNCS)
    print("indirect call: ", paths_indirect_call)  # blocks name

    # get the focused f(s)
    focus_funcs = []
    for p in paths_indirect_call:
        focus_funcs.append(p[1])
    focus_funcs = list(set(focus_funcs))
    print("focused f : " + str(focus_funcs))

    # focus_funcs_recursion = paths_indirect_call[-1]

    for f in cfg.functions:
        for i in f.instructions:
            if i.name == "call":
                if int(i.operand_interpretation.split(" ")[-1]) == send_inline_idx:
                    pass
                    # print("inline", f.name)
                if int(i.operand_interpretation.split(" ")[-1]) == send_deferred_idx:
                    pass
                    # print("defer", f.name)

    # ======================Anaylze C1 Begins=======================#
    if vul_type == "1":
        Vul1 = False

        # trace the blocks, get the indirect_call func idx (my-f)
        wasmvm = WasmVM(cfg, func_map)

        C1_paths_focus, C1_blocks_focus = get_paths_to_target(C1_paths, func_apply_blocks, focus_funcs)
        print("in C1, ", len(C1_paths_focus), "paths will lead to indirect call")

        for b in C1_blocks_focus:
            wasmvm.trace_blocks([b], {}, focus_funcs)
        # get_indirect_targets(wasmvm, C1_paths_focus, func_apply_blocks, apply_args, focus_funcs)
        # get_indirect_targets(wasmvm, C1_paths_focus, func_apply_blocks, apply_args, focus_funcs_recursion)
        print("in C1, ", wasmvm.indirect_targets, "is the target func to be called: ")
        if len(wasmvm.indirect_targets):
            Vul1 = True
        # get blocks graph of my-f
        # for f_idx in wasmvm.indirect_targets:
        #     target_f_paths = get_func_paths(cfg, func_map[f_idx][0])
        #
        #     #trace all possible paths
        #     #if send_inline exists, get the para
        #     wasmvm = WasmVM(cfg, func_map)
        #     args = [111,222,333,444,555]
        #     for p in target_f_paths:
        #         wasmvm.trace_func(p, args, [send_inline_idx])
        #         if wasmvm.send_inline_hit:
        #             Vul1 = True
        #             print("when code != eosio.token & action == transfer, send inline is invoked.")
        #             break
        # ======================Anaylze C1 Ends=========================#
        print("######result########")

        if Vul1:
            print("Vul1! false eos transfer!")
            f = open("log/list_results.txt", "a")
            f.write(file_name + "        " + "Vul1! false eos transfer!\n")
        else:
            print("No Vul1.")
            f = open("log/list_results.txt", "a")
            f.write(file_name + "        " + "No Vul1.\n")

        f.close()
        print("######result########")

    # ======================Anaylze C2 Begins=======================#
    elif vul_type == "2":
        Vul2 = True
        wasmvm = WasmVM(cfg, func_map)

        C2_paths_focus, C2_blocks_focus = get_paths_to_target(C2_paths, func_apply_blocks, focus_funcs)
        print("\nin C2, ", len(C2_paths_focus), "paths will lead to indirect call")
        # get_indirect_targets(wasmvm, C2_paths_focus, func_apply_blocks, apply_args, focus_funcs)
        for b in C2_blocks_focus:
            wasmvm.trace_blocks([b], {}, focus_funcs)

        print("in C2, ", wasmvm.indirect_targets, "is the target func to be called: ")

        if len(wasmvm.indirect_targets) == 0:
            Vul2 = False

        for idx in wasmvm.indirect_targets:
            # when self != to, what can be done? so we foucs the edges which are relevant with self != to
            f_name = func_map[idx][0]
            print(f_name)
            t_blocks, t_edges = gen_f_param(cfg, f_name)
            t_g_b, t_g_e = gen_g_param(t_blocks, t_edges)
            t_graph = Graph(t_g_b, t_g_e)
            edges_focus = t_edges.copy()

            # print("target edges len: ", len(t_edges))
            # print("target blocks len: ", len(t_blocks))

            Vul2 = True

            for e in t_edges:
                block_from = list(b for b in t_blocks if b.name == e.node_from)[0]
                # block_to = list(b for b in t_blocks if b.name == e.node_to)[0]
                instr = block_from.end_instr
                instrs = block_from.instructions
                str_instrs = list(str(i) for i in instrs)
                # 先判断是不是有eosio_assert,如果assert失败，就可以把接下来的所有边删了
                # 通过run block分析，只接受一个参数不反回的，记录它的函数参数，假定为action data，如果参数+8是比较的除了self的参数，则认为是在做这个比较
                # JUDGE CASE 1: action_data
                for i in range(len(str_instrs)):
                    if str_instrs[i] == "call " + str(assert_idx):
                        if instrs[i - 1].name in ["i32.const", "i64.const"]:
                            if 'i64.load 3, 0' in str_instrs[0:i]:
                                id_tmp = str_instrs.index('i64.load 3, 0')
                                if str_instrs[id_tmp - 1] == 'get_local 0':
                                    block_wasmvm = WasmVM(cfg, func_map)
                                    # block_wasmvm.mem_tb[10240] = b'\xff\xff\xff\xff'
                                    print("start", block_from.name)
                                    block_wasmvm.trace_blocks([block_from], {"$L0": 0}, [assert_idx])
                                    if block_wasmvm.dubiousCmp == True:
                                        Vul2 = False
                                        break

                if Vul2:
                    # JUDGE CASE 2: params
                    if instr.is_branch_conditional and len(instrs) >= 4:
                        if instr.name == "br_if":
                            # if instrs[-2].name == "i64.eq":

                            # self: get_local self
                            # to:   get_local 2
                            if "get_local 2" == str(instrs[-3]) and instrs[-4].name == "get_local" and isGetSelf(
                                    instrs[-4], f_name, cfg) \
                                    or "get_local 2" == str(instrs[-4]) and instrs[
                                -3].name == "get_local" and isGetSelf(
                                instrs[-3], f_name, cfg):
                                Vul2 = False
                            # self: get_local 0, i64.load 3, 0
                            # to:   get_local 2
                            if len(instrs) >= 5 and "get_local 2" in (str(instrs[-3]), str(instrs[-5])):
                                # print(str(instrs[-3]), str(insotrs[-4]), str(instrs[-5]))
                                if ('get_local 0', 'i64.load 3, 0') == (str_instrs[-4], str_instrs[-3]) \
                                        or ('get_local 0', 'i64.load 3, 0') == (str_instrs[-5], str_instrs[-4]):
                                    if e in edges_focus and e.type == EDGE_CONDITIONAL_TRUE:
                                        Vul2 = False
                                        edges_focus.remove(e)
                            # self: get_local self
                            # to:   i64.load 3, x + 8
                            if instrs[-3].name == "get_local" and isGetSelf(instrs[-3],
                                                                            f_name, cfg) and instrs[
                                -4].name == "i64.load" \
                                    or instrs[-4].name == "get_local" and isGetSelf(instrs[-4],
                                                                                    f_name, cfg) and instrs[
                                -3].name == "i64.load":
                                # wasm 跑从第一个到当下的块
                                # 是否有dubious cmp
                                paths = t_graph.depth_first_search_path(t_g_b[0], block_from.name)
                                for p in paths:
                                    p_wasmvm = WasmVM(cfg, func_map)
                                    # # block_wasmvm.mem_tb[10240] = b'\xff\xff\xff\xff'
                                    # print("start", block_from.name)
                                    print(p)
                                    path_blocks = blocks_name_to_blocks(p, t_blocks)
                                    p_wasmvm.trace_blocks((path_blocks), {"$L0": 0}, [assert_idx])
                                    if p_wasmvm.dubiousCmp == True:
                                        Vul2 = False
                                    #     break
                            # elif instrs[-2].name == "i64.ne":
                            #     if "get_local 2" == str(instrs[-3]) and instrs[-4].name == "get_local" and isGetSelf(instrs[-4], f_name, cfg) \
                            #     or "get_local 2" == str(instrs[-4]) and instrs[-3].name == "get_local" and isGetSelf(instrs[-3], f_name, cfg):
                            #         Vul2 = False
                            #     if  len(instrs) >= 5 and "get_local 2" in (str(instrs[-3]), str(instrs[-5])):
                            #         if ('get_local 0', 'i64.load 3, 0') == (str_instrs[-4], str_instrs[-3]) \
                            #             or ('get_local 0', 'i64.load 3, 0') == (str_instrs[-5], str_instrs[-4]):
                            #             if e in edges_focus and e.type == EDGE_CONDITIONAL_FALSE:
                            #                 Vul2 = False
                            #                 edges_focus.remove(e)
                        elif instr.name == "if":
                            pass
                        elif instr.name == "br_table":
                            pass

            g_nodes, g_edges = gen_g_param(t_blocks, edges_focus)
            t_graph = Graph(g_nodes, g_edges)
            to_ne_self_blocks = t_graph.depth_first_search(g_nodes[0])
            # to_ne_self_paths = t_graph.depth_first_search_path(g_nodes[0], g_nodes[-1])
            # print("the target func has ", len(to_ne_self_blocks), "different blocks if to!=self")

            # wasmvm = WasmVM(cfg, func_map)
            # args = [111, 222, 333, 444, 555]
            # for p in to_ne_self_paths:
            #     to_ne_self_blocks = blocks_name_to_blocks(p, t_blocks)
            #     wasmvm.trace_func(to_ne_self_blocks, args, [send_inline_idx])
            #     if wasmvm.send_inline_hit:
            #         print("when to != self, send inline is invoked.")
            #         break

        print("######result########")
        if Vul2:
            print("Vul2! transfer false receipiet!")
            f = open("log/list_results.txt", "a")
            f.write(file_name + "        " + "Vul2! transfer false receipiet!\n")
        else:
            print("No Vul2.")
            f = open("log/list_results.txt", "a")
            f.write(file_name + "        " + "No Vul2.\n")
        f.close()
        print("######result########")

    # ======================Anaylze C2 Ends=========================#


if __name__ == '__main__':
    main(sys.argv)
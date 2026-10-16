from enum import Enum
class TypeEnum(Enum):
    ROOT = 1
    NORMAL = 2
class Node:
    def __init__(self, id, parents, states, cpt, type: TypeEnum):
        # self.optional_value = {} # {1: 0.5, 2: 0.3, 3: 0.2}
        self.cpt = cpt # key: 父节点状态元组；value: {节点状态: 概率}
        self.id = id
        self.parents = parents
        self.parent_count = len(parents)
        self.states = states
        self.type = type
class Edge:
    def __init__(self, source, target):
        self.source = source
        self.target = target
class Condition:
    def __init__(self, node_id, value):
        self.node_id = node_id
        self.value = value
    def __eq__(self, other):
        return self.node_id == other.node_id and self.value == other.value
def combinations(pools, depth, current=None, cb=[], allow_similar=True):
    if current is None:
        current = []
    if depth == len(pools):
        cb.append([c for c in current])
        return
    for x in pools[depth]:
        if not allow_similar and x in current:
            continue
        else:
            current.append(x)
        combinations(pools, depth + 1, current, cb, allow_similar)
        current.pop()
class Bayesian:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node: Node, edges: list[Edge]):
        if node.id in self.nodes:
            raise Exception("node already exists")
        self.nodes[node.id] = node
        self.edges[node.id] = []
        for edge in edges:
            if edge.source == node.id:
                targets = list(self.edges[node.id])
                targets.append(edge.target)
                self.edges[node.id] = set(targets)
            elif edge.target == node.id:
                if edge.source in self.edges:
                    targets = self.edges[edge.source]
                    targets.append(edge.target)
                    self.edges[edge.source] = set(targets)

    def get_cpt_values(self, event: Condition, conditions: list[Condition], unmatched_nodes):
        node_id = event.node_id
        cpt_values = {}
        parent_conditions = []
        parent_unmatched_nodes = []
        for condition in conditions:
            if condition.node_id in self.nodes[node_id].parents:
                parent_conditions.append(condition)
        for unmatched_node in unmatched_nodes:
            if unmatched_node in self.nodes[node_id].parents:
                parent_unmatched_nodes.append(unmatched_node)
        # 直接从CPT里取出来
        event_node = self.nodes[node_id]
        cpt_key = []
        #parent_unmatched_nodes 对所有情况进行组合
        parent_unmatched_node_states_key = {}
        for parent_unmatched_node in parent_unmatched_nodes:
            parent_unmatched_node_states_key[parent_unmatched_node] = []
            parent_unmatched_node_node = self.nodes[parent_unmatched_node]
            for state in parent_unmatched_node_node.states:
                parent_unmatched_node_states_key[parent_unmatched_node].append(f"{parent_unmatched_node_node.id}={state}")
        parent_unmatched_node_states_key_combination = []

        for parent_condition in parent_conditions:
            parent_unmatched_node_states_key[parent_condition.node_id] = []
            parent_unmatched_node_states_key[parent_condition.node_id].append(f"{parent_condition.node_id}={parent_condition.value}")
        parent_unmatched_node_states_key_list = list(parent_unmatched_node_states_key.values())

        combinations(parent_unmatched_node_states_key_list, 0, None, parent_unmatched_node_states_key_combination)


        # for parent_unmatched_node in parent_unmatched_nodes:
            # parent_unmatched_node_name = self.nodes[parent_unmatched_node].id
            # for state in self.nodes[parent_unmatched_node].states:
        for parent_unmatched_node_states_key_combination_item in parent_unmatched_node_states_key_combination:
            # for parent_condition in parent_conditions:
                # parent_condition_name = parent_condition.node_id
            cpt_key = parent_unmatched_node_states_key_combination_item
            for key in event_node.cpt:
                if sorted(list(key)) == sorted(cpt_key):
                    cpt_value = event_node.cpt[key][event.value]
                    cpt_values[key] = cpt_value
        return cpt_values
    
    def calculate_event_conditions_probability(self, event: Condition, conditions: list[Condition], unmatched_nodes):
        # event限制的是要取哪个cpt的值（target），conditions限制的是哪些随机变量是已知的不用累加的，unmatched_nodes则是需要累加的
        eventNode = self.nodes[event.node_id]
        if eventNode.type == TypeEnum.ROOT:
            return eventNode.cpt[(eventNode.id,)][event.value]
        cpt_event_map = self.get_cpt_values(event, conditions, unmatched_nodes)
        value_sum = 0
        for cpt_key in cpt_event_map:
            nodes_value = {condition_pair.split("=")[0]: int(condition_pair.split("=")[1]) for condition_pair in cpt_key if condition_pair.split("=")[0] in self.nodes}
            nodes = [condition_pair.split("=")[0] for condition_pair in cpt_key if condition_pair.split("=")[0] in self.nodes]
            value = cpt_event_map[cpt_key]
            
            temp_conditions = [con for con in conditions]
            for n,v in nodes_value.items():
                temp_conditions.append(Condition(n, v))
            def f(nodes):
                if len(nodes) == 0:
                    return 1
                node = nodes.pop()
                # TODO
                node_event = Condition(node, nodes_value[node])
                node_value = self.calculate_posterior_probability([node_event], [])
                # node_value = 算出node=state的概率
                return node_value * f(nodes)
            value = value * f(nodes=nodes)
            value_sum += value
        return value_sum     

    def calculate_events_conditions_probability(self, events: list[Condition], conditions: list[Condition], unmatched_nodes):
            # event限制的是要取哪个cpt的值（target），conditions限制的是哪些随机变量是已知的不用累加的，unmatched_nodes则是需要累加的
            # eventNode = self.nodes[event.node_id]
            # if eventNode.type == TypeEnum.ROOT:
            #     return eventNode.cpt[(eventNode.id,)][event.value]

            # unmatched_nodes 组合并遍历
            unmatched_nodes_array = []
            unmatched_nodes_names = []
            for unmatched_node in unmatched_nodes:
                unmatched_node_node = self.nodes[unmatched_node]
                unmatched_nodes_array.append(unmatched_node_node.states)
                unmatched_nodes_names.append(unmatched_node)
            for condition in conditions:
                condition_node = self.nodes[condition.node_id]
                unmatched_nodes_array.append([condition.value])
                unmatched_nodes_names.append(condition.node_id)
            cpt_event_map_map = {}
            cpt_event_map_type_map = {}
            for event in events:
                eventNode = self.nodes[event.node_id]
                cpt_event_map_type_map[event.node_id] = eventNode.type
                if eventNode.type == TypeEnum.ROOT:
                    cpt_event_map_map[event.node_id] = eventNode.cpt[(eventNode.id,)][event.value]
                else:
                    cpt_event_map = self.get_cpt_values(event, conditions, unmatched_nodes)
                    cpt_event_map_map[event.node_id] = cpt_event_map

            unmatched_nodes_array_combinations = []
            combinations(unmatched_nodes_array, 0, None, unmatched_nodes_array_combinations)

            value_sum = 0
            # 外层不同combination累加
            for unmatched_nodes_array_combination in unmatched_nodes_array_combinations:
                prefix = []
                # 内层同一combination累乘
                for index, unmatched_node_value in enumerate(unmatched_nodes_array_combination):
                    unmatched_node_name = unmatched_nodes_names[index]
                    prefix.append(f"{unmatched_node_name}={unmatched_node_value}")
                event_value = 1
                for event_node_name in cpt_event_map_map:
                    event_type = cpt_event_map_type_map[event_node_name]
                    if event_type == TypeEnum.ROOT:
                        event_value = event_value * cpt_event_map_map[event_node_name]
                    else:
                        cpt_event_map = cpt_event_map_map[event_node_name]
                        event_prefix = [p for p in prefix if p.split("=")[0] in self.nodes[event_node_name].parents]
                        cpt_key = tuple(sorted(event_prefix)) 

                        if cpt_key in cpt_event_map:
                            event_value = event_value * cpt_event_map[cpt_key]

                conditions_unmonted_key = tuple(sorted(prefix)) 
                nodes_value = {condition_pair.split("=")[0]: int(condition_pair.split("=")[1]) for condition_pair in conditions_unmonted_key if condition_pair.split("=")[0] in self.nodes}
                nodes = [condition_pair.split("=")[0] for condition_pair in conditions_unmonted_key if condition_pair.split("=")[0] in self.nodes]

                # def f(nodes):
                #     if len(nodes) == 0:
                #         return 1
                #     node = nodes.pop()
                #     # TODO
                #     node_event = Condition(node, nodes_value[node])
                #     node_value = self.calculate_posterior_probability([node_event], [])
                #     # node_value = 算出node=state的概率
                #     return node_value * f(nodes)

                nodes_events = []
                conditions_nodes = [c.node_id for c in conditions]
                for node in nodes:
                    # if node not in conditions_nodes:
                    node_event = Condition(node, nodes_value[node])
                    nodes_events.append(node_event)
                # 子父级传递conditions，判断conditions是否需要保留，若为events的有效限制，则需要保留
                # p_conditions = [c for c in conditions if c.node_id not in nodes]
                events_pools = [nodes, [c.node_id for c in conditions]]
                events_conditions_cb = []
                p_cs = []
                combinations(events_pools, 0, None, events_conditions_cb, False)
                cb_pair = []
                for ec_cb in events_conditions_cb:
                    if sorted(ec_cb) in cb_pair:
                        continue
                    cb_pair.append(sorted(ec_cb))
                    e = ec_cb[0]
                    c = ec_cb[1]

                    def if_dependency(a, b):
                        if_found = False
                        visited = []
                        targets = self.edges[b]
                        targets = [t for t in targets if t not in visited]
                        queue = []
                        if targets:
                            queue.extend(targets)
                            visited.extend(targets)
                        while len(queue) > 0:
                            target = queue.pop()
                            visited.append(target)
                            if target == a:
                                if_found = True
                                break
                            targets = self.edges[target]
                            targets = [t for t in targets if t not in visited]
                            queue.extend(targets)
                        # 交换，同时events之间非父子关系（A与B B与A均无父子关系）则A和B都不用交换，且不能作为条件，有父子关系则交换父作为条件
                        return if_found
    
                    if if_dependency(e, c) or if_dependency(c, e):
                        p_cs.append(c)
                event_value = event_value * self.calculate_posterior_probability(nodes_events, conditions=[c for c in conditions if c.node_id in p_cs])
                value_sum += event_value
                # for cpt_key in cpt_event_map:
                #     nodes_value = {condition_pair.split("=")[0]: int(condition_pair.split("=")[1]) for condition_pair in cpt_key if condition_pair.split("=")[0] in self.nodes}
                #     nodes = [condition_pair.split("=")[0] for condition_pair in cpt_key if condition_pair.split("=")[0] in self.nodes]
                #     value = cpt_event_map[cpt_key]
                    
                #     temp_conditions = [con for con in conditions]
                #     for n,v in nodes_value.items():
                #         temp_conditions.append(Condition(n, v))
                # def f(nodes):
                #     if len(nodes) == 0:
                #         return 1
                #     node = nodes.pop()
                #     # TODO
                #     node_event = Condition(node, nodes_value[node])
                #     node_value = self.calculate_posterior_probability([node_event], [])
                #     # node_value = 算出node=state的概率
                #     return node_value * f(nodes)
                #     value = value * f(nodes=nodes)
                #     value_sum += value
            return value_sum         

    def calculate_edge_P(vairables: list[Condition]):
        pass

    def get_exchange_unmatched_nodes(self, events_nodes, condition_nodes):
        event_change = {}
        queue = []
        unmatched_nodes = []
        all_nodes = []
        all_nodes.extend([e for e in events_nodes])
        all_nodes.extend([c for c in condition_nodes])
        # unmatched_nodes_candidates = []
        for event_node in events_nodes:
            for condition_node in condition_nodes:
                if event_node == condition_node:
                    continue
                if_found = False
                visited = []
                targets = self.edges[condition_node]
                targets = [t for t in targets if t not in visited]
                if targets:
                    queue.extend(targets)
                    visited.extend(targets)
                while len(targets) > 0:
                    target = targets.pop()
                    if target == event_node:
                        if_found = True
                        break
                    targets = self.edges[target]
                    targets = [t for t in targets if t not in visited]
                    queue.extend(targets)
                # 交换，同时events之间非父子关系（A与B B与A均无父子关系）则A和B都不用交换，有父子关系则交换父
                if not if_found:
                    if event_node not in event_change:
                        event_change[event_node] = []
                    event_change[event_node].append(condition_node)
                unmatched_nodes.extend([n for n in visited if n not in all_nodes])

        # for k,vs in event_change.items():
        #     events_pools = [[k], vs]
        #     events_cb = []
        #     events_allows = []
        #     combinations(events_pools, 0, None, events_cb, False)
        #     cb_pair = []
        #     for event_cb in events_cb:
        #         if sorted(event_cb) in cb_pair:
        #             continue
        #         cb_pair.append(sorted(event_cb))
        #         a = event_cb[0]
        #         b = event_cb[1]

        #         def if_dependency(a, b):
        #             if_found = False
        #             visited = []
        #             targets = self.edges[b]
        #             targets = [t for t in targets if t not in visited]
        #             if targets:
        #                 queue.extend(targets)
        #                 visited.extend(targets)
        #             while len(queue) > 0:
        #                 target = queue.pop()
        #                 if target == a:
        #                     if_found = True
        #                     break
        #                 targets = self.edges[target]
        #                 targets = [t for t in targets if t not in visited]
        #                 queue.extend(targets)
        #             # 交换，同时events之间非父子关系（A与B B与A均无父子关系）则A和B都不用交换，且不能作为条件，有父子关系则交换父作为条件
        #             return if_found

        #         if if_dependency(a, b):
        #             events_allows.append(b)
        #         if if_dependency(b, a):
        #             events_allows.append(a)

        # unmatched_nodes = list(set(unmatched_nodes))
        # event_change_allow = {}
        # for k,vs in event_change.items():
        #     if k in events_allows:
        #         event_change_allow[k] = vs
            # else:
            #     if k in condition_nodes and k in events_nodes:
            #         condition_nodes.remove(k)
        return event_change, unmatched_nodes, condition_nodes

    def calculate_splits(self, events: list[Condition], conditions: list[Condition], unmatched_nodes):
        # TODO events需要拆的情况
        events_nodes = [e.node_id for e in events]
        events_map = {e.node_id: e for e in events}
        events_pools = [events_nodes, events_nodes]
        events_cb = []
        events_splits = {}
        combinations(events_pools, 0, None, events_cb, False)
        cb_pair = []
        for event_cb in events_cb:
            if sorted(event_cb) in cb_pair:
                continue
            cb_pair.append(sorted(event_cb))
            a = event_cb[0]
            b = event_cb[1]
            queue = []
            def if_dependency(a, b):
                if_found = False
                visited = []
                targets = self.edges[b]
                targets = [t for t in targets if t not in visited]
                if targets:
                    queue.extend(targets)
                    visited.extend(targets)
                while len(queue) > 0:
                    target = queue.pop()
                    visited.append(target)
                    if target == a:
                        if_found = True
                        break
                    targets = self.edges[target]
                    targets = [t for t in targets if t not in visited]
                    queue.extend(targets)
                # 交换，同时events之间非父子关系（A与B B与A均无父子关系）则A和B都不用交换，且不能作为条件，有父子关系则交换父作为条件
                return if_found

            if if_dependency(a, b):
                if a not in events_splits:
                    events_splits[a] = []
                events_splits[a].append(b)
            if if_dependency(b, a):
                if b not in events_splits:
                    events_splits[b] = []
                events_splits[b].append(a)

        current_value = 1
        if len(list(events_splits.keys())) > 0:
            # 拆
            for child, parents in events_splits.items():
                temp_conditions = conditions + [events_map[p] for p in parents]
                temp_events = [events_map[child]]
                current_value *= self.calculate_posterior_probability(temp_events, temp_conditions)
                # current_value *= self.calculate_posterior_probability(temp_conditions, conditions)
        else:
            current_value *= self.calculate_events_conditions_probability(events, conditions, unmatched_nodes)
        return current_value


    def calculate_pre_posterior_probability(self, events: list[Condition], conditions: list[Condition]):
            # 1. 递归找到events: list[Condition], conditions: list[Condition]和unmatched_nodes，如果events之间有直接关联，则把events父级合并到condition，没有关联则视为独立并分别计算之后相乘
            unmatched_nodes = []
            events_nodes = []
            condition_nodes = []
            all_nodes = []
            variable_values = {}
            for event in events:
                all_nodes.append(event.node_id)
                # matched_nodes.append(event.node_id)
                events_nodes.append(event.node_id)
                variable_values[event.node_id] = event.value
            # for event_node in events_nodes:
            #     for target in self.edges[event_node]:
            #         if target in events_nodes:
            #             condition_nodes.append(event_node)
            # events_nodes = [event_node for event_node in events_nodes if event_node not in condition_nodes]
            for condition in conditions:
                all_nodes.append(condition.node_id)
                # matched_nodes.append(condition.node_id)
                condition_nodes.append(condition.node_id)
                variable_values[condition.node_id] = condition.value
    
            for event_node in events_nodes:
                for edge_source in self.edges:
                    if edge_source in condition_nodes:
                        continue
                    if event_node in self.edges[edge_source] and edge_source not in unmatched_nodes and edge_source not in all_nodes:
                        unmatched_nodes.append(edge_source) 
                        all_nodes.append(edge_source)
            for condition_node in condition_nodes:
                for edge_source in self.edges:
                    if condition_node in self.edges[edge_source] and edge_source not in unmatched_nodes and edge_source not in all_nodes:
                        unmatched_nodes.append(edge_source) 
                        all_nodes.append(edge_source)
            all_nodes = set(all_nodes)
    
        
            # for all_node in all_nodes:
            #     for edge_source in self.edges:
            #         if all_node in self.edges[edge_source] and edge_source not in all_nodes:
            #             all_nodes.append(edge_source)
            # 隐藏变量
            # unmatched_nodes = [node for node in all_nodes if node not in matched_nodes]
            # 1. 判断条件和事件之间是什么关系，能不能直接通过cpt获取，还是需要通过贝叶斯公式转化
            # matched_ec_nodes = {}
            # unmatched_ec_nodes = []
            # for c_node in condition_nodes:
            #     if_found = False
            #     for e_node in events_nodes:
            #         if e_node in self.edges[c_node]:
            #             if_found = True
            #             if e_node not in matched_ec_nodes:
            #                 matched_ec_nodes[e_node] = []
            #             matched_ec_nodes[e_node].append(c_node)
            #     if not if_found:
            #         unmatched_ec_nodes.append(c_node)
    
            # 公式转换： event不能是condition或者unmatched_nodes的source
            # TODO 不止是直接依赖交换，上下游多跳都要交换，并且把缺失的设置为unmatched
            event_change = {}
            for event_node in events_nodes:
                for condition in condition_nodes:
                    if condition in self.edges[event_node]:
                        # event是source，说明要和condition交换
                        if event_node not in event_change:
                            event_change[event_node] = []
                        event_change[event_node].append(condition)
    
            event_change, _, condition_nodes = self.get_exchange_unmatched_nodes(events_nodes, condition_nodes)
            if len(event_change) > 0:
                return self.calculate_posterior_probability(events, conditions)
            else:
                if conditions == events:
                    return 1
                if len(conditions) > 0:
                    return self.calculate_posterior_probability(events, conditions) / self.calculate_posterior_probability(conditions, [])

    # TODO 现在有交换是条件概率，不交换是联合概率
    def calculate_posterior_probability(self, events: list[Condition], conditions: list[Condition]):
        # 1. 递归找到events: list[Condition], conditions: list[Condition]和unmatched_nodes，如果events之间有直接关联，则把events父级合并到condition，没有关联则视为独立并分别计算之后相乘
        unmatched_nodes = []
        events_nodes = []
        condition_nodes = []
        all_nodes = []
        variable_values = {}
        for event in events:
            all_nodes.append(event.node_id)
            # matched_nodes.append(event.node_id)
            events_nodes.append(event.node_id)
            variable_values[event.node_id] = event.value
        # for event_node in events_nodes:
        #     for target in self.edges[event_node]:
        #         if target in events_nodes:
        #             condition_nodes.append(event_node)
        # events_nodes = [event_node for event_node in events_nodes if event_node not in condition_nodes]
        for condition in conditions:
            all_nodes.append(condition.node_id)
            # matched_nodes.append(condition.node_id)
            condition_nodes.append(condition.node_id)
            variable_values[condition.node_id] = condition.value

        for event_node in events_nodes:
            for edge_source in self.edges:
                if edge_source in condition_nodes:
                    continue
                if event_node in self.edges[edge_source] and edge_source not in unmatched_nodes and edge_source not in all_nodes:
                    unmatched_nodes.append(edge_source) 
                    all_nodes.append(edge_source)
        for condition_node in condition_nodes:
            for edge_source in self.edges:
                if condition_node in self.edges[edge_source] and edge_source not in unmatched_nodes and edge_source not in all_nodes:
                    unmatched_nodes.append(edge_source) 
                    all_nodes.append(edge_source)
        all_nodes = set(all_nodes)

    
        # for all_node in all_nodes:
        #     for edge_source in self.edges:
        #         if all_node in self.edges[edge_source] and edge_source not in all_nodes:
        #             all_nodes.append(edge_source)
        # 隐藏变量
        # unmatched_nodes = [node for node in all_nodes if node not in matched_nodes]
        # 1. 判断条件和事件之间是什么关系，能不能直接通过cpt获取，还是需要通过贝叶斯公式转化
        # matched_ec_nodes = {}
        # unmatched_ec_nodes = []
        # for c_node in condition_nodes:
        #     if_found = False
        #     for e_node in events_nodes:
        #         if e_node in self.edges[c_node]:
        #             if_found = True
        #             if e_node not in matched_ec_nodes:
        #                 matched_ec_nodes[e_node] = []
        #             matched_ec_nodes[e_node].append(c_node)
        #     if not if_found:
        #         unmatched_ec_nodes.append(c_node)

        # 公式转换： event不能是condition或者unmatched_nodes的source
        # TODO 不止是直接依赖交换，上下游多跳都要交换，并且把缺失的设置为unmatched
        event_change = {}
        for event_node in events_nodes:
            for condition in condition_nodes:
                if condition in self.edges[event_node]:
                    # event是source，说明要和condition交换
                    if event_node not in event_change:
                        event_change[event_node] = []
                    event_change[event_node].append(condition)

        event_change, _, condition_nodes = self.get_exchange_unmatched_nodes(events_nodes, condition_nodes)
        # events_nodes = [e for e in events_nodes if e not in condition_nodes and e not in unmatched_nodes]
        
        # 有交换的，那么就需要把分子转换成
        molecular_unmatched_nodes = [n for n in unmatched_nodes]
        molecular_conditions = [c for c in condition_nodes]
        molecular_events = [e for e in events_nodes]
        for event in event_change:
            molecular_conditions.append(event)
            molecular_events.remove(event)
            for origin_condition in event_change[event]:
                molecular_conditions.remove(origin_condition)
                molecular_events.append(origin_condition)
        # 分母：
        denominator_unmatched_nodes = [n for n in unmatched_nodes]
        denominator_conditions = [c for c in condition_nodes]
        denominator_events = []
        if len(event_change) > 0:
            for event in event_change:
                denominator_unmatched_nodes.append(event)
                for origin_condition in event_change[event]:
                    denominator_conditions.remove(origin_condition)
                    denominator_events.append(origin_condition)
        # else:
        #     denominator_events = []
        #     denominator_conditions = []
        #     denominator_unmatched_nodes = []
        #     if len(conditions) > 0:
        #         denominator_events = molecular_conditions
        #         denominator_conditions = molecular_conditions
        #         denominator_unmatched_nodes = molecular_unmatched_nodes


        # TODO 待验证完整流程及单个CPT取值是否正确
        # 2. 根据有向图拆成CPT，当events有多个的时候，原则是：1. 当events之间没有依赖，则可以直接分拆并相乘，2.当events之间有依赖，则需要把source保留到target event的condition中
                #2.1 for循环调用event 进calculate_nodes_probability，并累乘
                #2.2 先处理condition，再进calculate_nodes_probability，并累乘
        # 先处理分子
        # for event_node in molecular_events:
        #     for target in self.edges[event_node]:
        #         if target in molecular_events:
        #             molecular_conditions.append(event_node)
        #             molecular_conditions = list(set(molecular_conditions))
        molecular_events = [me for me in molecular_events if me not in molecular_conditions and me not in molecular_unmatched_nodes]
        # 处理当层CPT
        molecular_value = 1
        if len(molecular_events) > 0:
            molecular_value = self.calculate_splits([Condition(c, variable_values[c]) for c in molecular_events],[Condition(c, variable_values[c]) for c in molecular_conditions], molecular_unmatched_nodes)
        # for event_node in molecular_events:
        #     molecular_value *= self.calculate_event_conditions_probability(Condition(event_node, variable_values[event_node]), [Condition(c, variable_values[c]) for c in molecular_conditions], molecular_unmatched_nodes)
        # 递归处理父级
        # father_molecular_events = molecular_conditions
        # if len(father_molecular_events) > 0:
        #     molecular_value *= self.calculate_posterior_probability(
        #         [Condition(e, variable_values[e]) for e in father_molecular_events], []
        #     )
        
        # 再处理分母
        # for event_node in denominator_events:
        #     for target in self.edges[event_node]:
        #         if target in denominator_events:
        #             denominator_conditions.append(event_node)
        #             denominator_conditions = list(set(denominator_conditions))

        # 处理当层CPT
        denominator_value = 1
        denominator_events = [de for de in denominator_events if de not in denominator_conditions and de not in denominator_unmatched_nodes]
        if len(denominator_events) > 0:
            # for event_node in denominator_events:
            #     denominator_value *= self.calculate_event_conditions_probability(Condition(event_node, variable_values[event_node]), [Condition(c, variable_values[c]) for c in denominator_conditions], denominator_unmatched_nodes)
            denominator_value = self.calculate_splits([Condition(c, variable_values[c]) for c in denominator_events],[Condition(c, variable_values[c]) for c in denominator_conditions], denominator_unmatched_nodes)

        # 递归处理父级
        # father_denominator_events = denominator_conditions
        # if len(father_denominator_events) > 0:
        #     denominator_value *= self.calculate_posterior_probability(
        #         [Condition(e, variable_values[e]) for e in father_denominator_events], []
        #     )

        return molecular_value / denominator_value

if __name__ == "__main__":
    bayesian = Bayesian()
    # 示例假设：C、D 的状态 1 都会提高 A、B 取状态 1 的概率。
    cpt_a = {
        ("C=0", "D=0"): {0: 0.95, 1: 0.05},
        ("C=0", "D=1"): {0: 0.70, 1: 0.30},
        ("C=1", "D=0"): {0: 0.45, 1: 0.55},
        ("C=1", "D=1"): {0: 0.10, 1: 0.90},
    }
    cpt_b = {
        ("C=0", "D=0"): {0: 0.90, 1: 0.10},
        ("C=0", "D=1"): {0: 0.55, 1: 0.45},
        ("C=1", "D=0"): {0: 0.75, 1: 0.25},
        ("C=1", "D=1"): {0: 0.25, 1: 0.75},
    }
    nodeA = Node("A", ["C", "D"], [0, 1], cpt_a, TypeEnum.NORMAL)
    nodeB = Node("B", ["C", "D"], [0, 1], cpt_b, TypeEnum.NORMAL)
    nodeC = Node("C", [], [0, 1], {("C",): {0: 0.80, 1: 0.20}}, TypeEnum.ROOT)
    nodeD = Node("D", [], [0, 1], {("D",): {0: 0.70, 1: 0.30}}, TypeEnum.ROOT)
    edgeCA = Edge(nodeC.id, nodeA.id)
    edgeCB = Edge(nodeC.id, nodeB.id)
    edgeDA = Edge(nodeD.id, nodeA.id)
    edgeDB = Edge(nodeD.id, nodeB.id)
    bayesian.add_node(nodeA, [])
    bayesian.add_node(nodeB, [])
    bayesian.add_node(nodeC, [edgeCA, edgeCB])
    bayesian.add_node(nodeD, [edgeDA, edgeDB])
    eventC = Condition(nodeC.id, 0)
    conditionA = Condition(nodeA.id, 1)
    conditionB = Condition(nodeB.id, 0)
    print(bayesian.calculate_posterior_probability([eventC], [conditionA, conditionB]))

    # # 下面的节点按“子节点在前、父节点在后”的顺序加入网络。
    # # 每组都给出根据 CPT 独立计算的预期值，便于定位尚未支持的推理结构。
    def run_case(name, nodes, edge_pairs, events, conditions, expected):
        network = Bayesian()
        for node in nodes:
            outgoing = [Edge(source, target) for source, target in edge_pairs if source == node.id]
            network.add_node(node, outgoing)
        try:
            actual = network.calculate_pre_posterior_probability(
                [Condition(node_id, value) for node_id, value in events],
                [Condition(node_id, value) for node_id, value in conditions],
            )
            result = "通过" if abs(actual - expected) < 1e-9 else "未通过"
            print(f"{name}: {result}，实际={actual:.12f}，预期={expected:.12f}")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            print(f"{name}: 报错 {type(exc).__name__}: {exc}，预期={expected:.12f}")

    # # 2 节点链：X -> Y；反向推理 P(X=1 | Y=1)。
    # # 预期：(0.3 * 0.8) / (0.3 * 0.8 + 0.7 * 0.2) = 12/19。
    run_case(
        "2 节点链",
        [
            Node("Y", ["X"], [0, 1], {
                ("X=0",): {0: 0.8, 1: 0.2},
                ("X=1",): {0: 0.2, 1: 0.8},
            }, TypeEnum.NORMAL),
            Node("X", [], [0, 1], {("X",): {0: 0.7, 1: 0.3}}, TypeEnum.ROOT),
        ],
        [("X", "Y")], [("X", 1)], [("Y", 1)], 12 / 19,
    )

    # # # 3 节点分叉：R -> S、R -> T；两项观测共同指向根节点。
    # # # 预期：(0.4 * 0.8 * 0.3) / (0.4 * 0.8 * 0.3 + 0.6 * 0.1 * 0.9) = 0.64。
    run_case(
        "3 节点分叉",
        [
            Node("S", ["R"], [0, 1], {
                ("R=0",): {0: 0.9, 1: 0.1},
                ("R=1",): {0: 0.2, 1: 0.8},
            }, TypeEnum.NORMAL),
            Node("T", ["R"], [0, 1], {
                ("R=0",): {0: 0.9, 1: 0.1},
                ("R=1",): {0: 0.3, 1: 0.7},
            }, TypeEnum.NORMAL),
            Node("R", [], [0, 1], {("R",): {0: 0.6, 1: 0.4}}, TypeEnum.ROOT),
        ],
        [("R", "S"), ("R", "T")], [("R", 1)], [("S", 1), ("T", 0)], 0.64,
    )

    # # 3 节点链：R -> M -> L；中间节点 M 未观测，需要边缘化。
    # # 预期：0.35*(0.7*0.9+0.3*0.1) / [前项+0.65*(0.2*0.9+0.8*0.1)] = 0.5775。
    run_case(
        "3 节点链（隐藏中间节点）",
        [
            Node("L", ["M"], [0, 1], {
                ("M=0",): {0: 0.9, 1: 0.1},
                ("M=1",): {0: 0.1, 1: 0.9},
            }, TypeEnum.NORMAL),
            Node("M", ["R"], [0, 1], {
                ("R=0",): {0: 0.8, 1: 0.2},
                ("R=1",): {0: 0.3, 1: 0.7},
            }, TypeEnum.NORMAL),
            Node("R", [], [0, 1], {("R",): {0: 0.65, 1: 0.35}}, TypeEnum.ROOT),
        ],
        [("R", "M"), ("M", "L")], [("R", 1)], [("L", 1)], 0.5775,
    )

    # # 4 节点汇聚再延伸：U -> M <- V，M -> Q；正向推理 P(Q=1 | U=1)。
    # # 预期：0.7*(0.5*0.9+0.5*0.2) + 0.3*(0.9*0.9+0.1*0.2) = 0.634。
    run_case(
        "4 节点汇聚与延伸",
        [
            Node("Q", ["M"], [0, 1], {
                ("M=0",): {0: 0.8, 1: 0.2},
                ("M=1",): {0: 0.1, 1: 0.9},
            }, TypeEnum.NORMAL),
            Node("M", ["U", "V"], [0, 1], {
                ("U=0", "V=0"): {0: 0.95, 1: 0.05},
                ("U=0", "V=1"): {0: 0.6, 1: 0.4},
                ("U=1", "V=0"): {0: 0.5, 1: 0.5},
                ("U=1", "V=1"): {0: 0.1, 1: 0.9},
            }, TypeEnum.NORMAL),
            Node("U", [], [0, 1], {("U",): {0: 0.8, 1: 0.2}}, TypeEnum.ROOT),
            Node("V", [], [0, 1], {("V",): {0: 0.7, 1: 0.3}}, TypeEnum.ROOT),
        ],
        [("U", "M"), ("V", "M"), ("M", "Q")],
        [("Q", 1)], [("U", 1)], 0.634,
    )

    # 自条件恒等式：只含一个根节点时，P(X=x | X=x) 必须等于 1。
    # 这能单独检查“同一节点同时出现在事件和条件中”的处理。
    for node_id, state in [("C", 0), ("U", 1)]:
        run_case(
            f"自条件 {node_id}={state}",
            [Node(node_id, [], [0, 1], {
                (node_id,): {0: 0.8, 1: 0.2},
            }, TypeEnum.ROOT)],
            [], [(node_id, state)], [(node_id, state)], 1.0,
        )

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
def combinations(pools, depth, current=None, cb=[]):
    if current is None:
        current = []
    if depth == len(pools):
        cb.append([c for c in current])
        return
    for x in pools[depth]:
        current.append(x)
        combinations(pools, depth + 1, current, cb)
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
                for node in nodes:
                    node_event = Condition(node, nodes_value[node])
                    nodes_events.append(node_event)
                event_value = event_value * self.calculate_posterior_probability(nodes_events, [])
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

    def calculate_posterior_probability(self, events: list[Condition], conditions: list[Condition]):
        # 1. 递归找到events: list[Condition], conditions: list[Condition]和unmatched_nodes，如果events之间有直接关联，则把events父级合并到condition，没有关联则视为独立并分别计算之后相乘
        matched_nodes = []
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
        event_change = {}
        for event_node in events_nodes:
            for condition in condition_nodes:
                if condition in self.edges[event_node]:
                    # event是source，说明要和condition交换
                    if event_node not in event_change:
                        event_change[event_node] = []
                    event_change[event_node].append(condition)
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
        for event in event_change:
            denominator_unmatched_nodes.append(event)
            for origin_condition in event_change[event]:
                denominator_conditions.remove(origin_condition)
                denominator_events.append(origin_condition)

        # TODO 待验证完整流程及单个CPT取值是否正确
        # 2. 根据有向图拆成CPT，当events有多个的时候，原则是：1. 当events之间没有依赖，则可以直接分拆并相乘，2.当events之间有依赖，则需要把source保留到target event的condition中
                #2.1 for循环调用event 进calculate_nodes_probability，并累乘
                #2.2 先处理condition，再进calculate_nodes_probability，并累乘
        # 先处理分子
        for event_node in molecular_events:
            for target in self.edges[event_node]:
                if target in molecular_events:
                    molecular_conditions.append(event_node)
        # 处理当层CPT
        molecular_value = 1
        if len(molecular_events) > 0:
            molecular_value = self.calculate_events_conditions_probability([Condition(c, variable_values[c]) for c in molecular_events],[Condition(c, variable_values[c]) for c in molecular_conditions], molecular_unmatched_nodes)
        # for event_node in molecular_events:
        #     molecular_value *= self.calculate_event_conditions_probability(Condition(event_node, variable_values[event_node]), [Condition(c, variable_values[c]) for c in molecular_conditions], molecular_unmatched_nodes)
        # 递归处理父级
        # father_molecular_events = molecular_conditions
        # if len(father_molecular_events) > 0:
        #     molecular_value *= self.calculate_posterior_probability(
        #         [Condition(e, variable_values[e]) for e in father_molecular_events], []
        #     )
        
        # 再处理分母
        for event_node in denominator_events:
            for target in self.edges[event_node]:
                if target in denominator_events:
                    denominator_conditions.append(event_node)

        # 处理当层CPT
        denominator_value = 1
        if len(denominator_events) > 0:
            # for event_node in denominator_events:
            #     denominator_value *= self.calculate_event_conditions_probability(Condition(event_node, variable_values[event_node]), [Condition(c, variable_values[c]) for c in denominator_conditions], denominator_unmatched_nodes)
            denominator_value = self.calculate_events_conditions_probability([Condition(c, variable_values[c]) for c in denominator_events],[Condition(c, variable_values[c]) for c in denominator_conditions], denominator_unmatched_nodes)

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

#!/usr/bin/env python
# -*- coding: utf8 -*-

import itertools
from collections import defaultdict

import numpy as np


class BipartiteGraph(object):
    """bipartite graph를 표현하기 위한 클래스"""
    def __init__(self):
        self._lns = defaultdict(dict)
        self._rns = defaultdict(dict)

    def add_edge(self, source, target, weight=1.0):
        self._lns[source][target] = weight
        self._rns[target][source] = weight

    def get_lns(self):
        return self._lns.keys()

    def get_rns(self):
        return self._rns.keys()

    def get_lns_count(self):
        return len(self._lns)

    def get_weight(self, ln, rn):
        return self._lns[ln][rn]

    def get_lns_index(self):
        return dict([(node, i) for i, node in enumerate(self._lns)])

    def get_rns_index(self):
        return dict([(node, i) for i, node in enumerate(self._rns)])

    def get_ln_neighbors(self, ln):
        if ln not in self._lns:
            raise KeyError("%s is not in this graph's left side." % ln)

        return self._lns[ln]

    def get_rn_neighbors(self, rn):
        if rn not in self._rns:
            raise KeyError("%s is not in this graph's right side." % rn)

        return self._rns[rn]

    def get_neighbors(self, node, is_lns=True):
        if is_lns:
            return self.get_ln_neighbors(node)
        else:
            return self.get_rn_neighbors(node)

    def split_subgraphs(self):
        """Bipartitle graph가 연결이 끊어진 여러 그래프로 나뉠 수 있다면, 해당 그래프들을 분리해서 list에 담아 반환한다."""
        # not yes processed edges
        wating_edges = set()
        for ln in self.get_lns():
            for ne in self.get_ln_neighbors(ln):
                wating_edges.add((ln, ne))

        result_list = []
        while len(wating_edges) > 0:
            # 아직 처리되지 않은 edge 하나를 뽑아서 starting point ln을 정한다.
            _ln, _rn = wating_edges.pop()
            wating_lns = [_ln]

            # ln 정보만 얻고 다시 대기열에 넣어두어야 이후에 정상 처리됨.
            wating_edges.add((_ln, _rn))

            g = BipartiteGraph()
            while len(wating_lns) > 0:
                ln = wating_lns.pop(0)

                # 아직 처리 안된 edge에 대해서만 처리
                for rn in filter(lambda candidate_rn: (ln, candidate_rn) in wating_edges, self.get_ln_neighbors(ln)):
                    g.add_edge(ln, rn, self.get_weight(ln, rn))

                    # 처리한 edge를 대기열에서 삭제하고,
                    # 이번에 처리한 rn의 neighbors(candidate ln)를 처리 대상으로 추가한다.
                    wating_edges.remove((ln, rn))
                    wating_lns.extend(filter(lambda candidate_ln: (candidate_ln, rn) in wating_edges, self.get_rn_neighbors(rn)))

            # 하나의 subgraph 완성
            result_list.append(g)

        return result_list


def simrank_bipartite(G, r=0.8, max_iter=100, eps=1e-4):
    """ A bipartite version in the paper.
    """

    lns = G.get_lns()
    rns = G.get_rns()

    lns_count = len(lns)
    rns_count = len(rns)

    lns_index = G.get_lns_index()
    rns_index = G.get_rns_index()

    lns_sim_prev = np.identity(lns_count)
    lns_sim = np.identity(lns_count)

    rns_sim_prev = np.identity(rns_count)
    rns_sim = np.identity(rns_count)

    def _update_left_partite():
        for u, v in itertools.product(lns, lns):
            if u is v: continue

            u_index, v_index = lns_index[u], lns_index[v]
            u_ns, v_ns = G.get_ln_neighbors(u), G.get_ln_neighbors(v)

            if len(u_ns) == 0 or len(v_ns) == 0:
                lns_sim[u_index][v_index] = lns_sim[v_index][u_index] = 0.0

            else:
                # left의 neighbor들은 right
                s_uv = sum([rns_sim_prev[rns_index[u_n]][rns_index[v_n]] for u_n, v_n in itertools.product(u_ns, v_ns)])
                lns_sim[u_index][v_index] = lns_sim[v_index][u_index] = (r * s_uv) / (len(u_ns) * len(v_ns))

    def _update_right_partite():
        for u, v in itertools.product(rns, rns):
            if u is v: continue

            u_index, v_index = rns_index[u], rns_index[v]
            u_ns, v_ns = G.get_rn_neighbors(u), G.get_rn_neighbors(v)

            if len(u_ns) == 0 or len(v_ns) == 0:
                rns_sim[u_index][v_index] = rns_sim[v_index][u_index] = 0.0

            else:
                # right의 neighbor들은 left
                s_uv = sum([lns_sim_prev[lns_index[u_n]][lns_index[v_n]] for u_n, v_n in itertools.product(u_ns, v_ns)])
                rns_sim[u_index][v_index] = rns_sim[v_index][u_index] = (r * s_uv) / (len(u_ns) * len(v_ns))

    for i in range(max_iter):
        if np.allclose(lns_sim, lns_sim_prev, atol=eps) and np.allclose(rns_sim, rns_sim_prev, atol=eps):
            break

        lns_sim_prev = np.copy(lns_sim)
        rns_sim_prev = np.copy(rns_sim)

        _update_left_partite()
        _update_right_partite()

    print("Converge after %d iterations (eps=%f)." % (i, eps))

    return (lns_sim, rns_sim)


def simrank_double_plus_bipartite(G, r=0.8, max_iter=100, eps=1e-4):
    """ A simrank++ bipartite version in the paper.
    """

    lns = G.get_lns()
    rns = G.get_rns()

    lns_count = len(lns)
    rns_count = len(rns)

    lns_index = G.get_lns_index()
    rns_index = G.get_rns_index()

    lns_sim_prev = np.identity(lns_count)
    lns_sim = np.identity(lns_count)

    rns_sim_prev = np.identity(rns_count)
    rns_sim = np.identity(rns_count)

    # evidence
    lns_evidence = np.identity(lns_count)
    rns_evidence = np.identity(rns_count)

    # spread
    lns_spread = np.zeros(lns_count)
    rns_spread = np.zeros(rns_count)

    # normalized weight
    # row: node_from, column: node_to
    norm_weight_l_to_r = np.zeros((lns_count, rns_count))
    norm_weight_r_to_l = np.zeros((rns_count, lns_count))

    # transition_prob
    # row: node_from, column: node_to
    transition_prob_l_to_r = np.zeros((lns_count, rns_count))
    transition_prob_r_to_l = np.zeros((rns_count, lns_count))
    self_transition_prob_l = np.zeros(lns_count)
    self_transition_prob_r = np.zeros(rns_count)

    def _calculate_evidence(ns, ns_index, ns_evidence, is_lns=True):
        """ns의 evidence 계산하기

        ns의 evidence를 계산해서 ns_evidence에 저장한다.

        :param ns: evidence를 계산할 node list
        :param ns_index: ns의 배열에서의 index를 얻을 사전. key: node, value: index
        :param ns_evidence: 계산한 evidence를 저장할 matrix
        :param is_lns: ns가 left nodes인지 여부. True이면 left, False이면 right.
        """
        ## sum_i=1..n (1/2^n). 11개 이상은 1.0으로 봐도 됨.
        ## 공통 원소가 0개인 경우는 무조건 0이므로, 앞에 0 추가.
        calculated_evidence = [0.0,
                               0.50000, 0.75000, 0.87500, 0.93750, 0.96875,
                               0.98438, 0.99219, 0.99609, 0.99805, 0.99902]

        calculated = np.full((len(ns), len(ns)), False)

        for u, v in itertools.product(ns, ns):
            # 동일한 노드이거나 이미 계산한 노드인 경우는 skip
            if u is v: continue
            if calculated[ns_index[u]][ns_index[v]]: continue

            u_ns = set(G.get_neighbors(u, is_lns))
            v_ns = set(G.get_neighbors(v, is_lns))

            evidence_uv = 0.0

            if (len(u_ns) == 0) or (len(v_ns) == 0):
                evidence_uv = 0.0
            else:
                intersection = len(u_ns & v_ns)
                evidence_uv = calculated_evidence[intersection] if intersection <= 10 else 1.0

            ns_evidence[ns_index[u]][ns_index[v]] = evidence_uv
            ns_evidence[ns_index[v]][ns_index[u]] = evidence_uv
            calculated[ns_index[u]][ns_index[v]] = True
            calculated[ns_index[v]][ns_index[u]] = True


    def _calculate_spread(ns, is_lns=True):
        """ns의 spread 계산"""
        for n in ns:
            nbr = G.get_neighbors(n, is_lns)
            weights = nbr.values()

            if is_lns:
                lns_spread[lns_index[n]] = np.exp(-np.var(weights))
            else:  # is_rns
                rns_spread[rns_index[n]] = np.exp(-np.var(weights))


    def _calculate_normalized_weight(ns, is_lns=True):
        for n in ns:
            nbrs = G.get_neighbors(n, is_lns)
            denom_factor = np.sum(nbrs.values())

            for nbr in nbrs:
                if is_lns:
                    norm_weight_l_to_r[lns_index[n]][rns_index[nbr]] = nbrs[nbr] / denom_factor
                else: # is_rns
                    norm_weight_r_to_l[rns_index[n]][lns_index[nbr]] = nbrs[nbr] / denom_factor


    def _calculate_transition_prob():
        _calculate_spread(lns)
        _calculate_spread(rns, False)

        _calculate_normalized_weight(lns)
        _calculate_normalized_weight(rns, False)

        # lns to rns
        for n in lns:
            n_index = lns_index[n]

            sum_prob = 0.0
            for nbr in G.get_neighbors(n, True):
                nbr_index = rns_index[nbr]
                transition_prob_l_to_r[n_index][nbr_index] = rns_spread[nbr_index] * norm_weight_l_to_r[n_index][nbr_index]
                sum_prob += transition_prob_l_to_r[n_index][nbr_index]

            self_transition_prob_l[n_index] = 1.0 - sum_prob

        # rns to lns
        for n in rns:
            n_index = rns_index[n]

            sum_prob = 0.0
            for nbr in G.get_neighbors(n, False):
                nbr_index = lns_index[nbr]
                transition_prob_r_to_l[n_index][nbr_index] = lns_spread[nbr_index] * norm_weight_r_to_l[n_index][nbr_index]
                sum_prob += transition_prob_r_to_l[n_index][nbr_index]

            self_transition_prob_r[n_index] = 1.0 - sum_prob


    def _update_left_partite():
        for u, v in itertools.product(lns, lns):
            if u is v: continue

            u_index, v_index = lns_index[u], lns_index[v]
            u_ns, v_ns = G.get_ln_neighbors(u), G.get_ln_neighbors(v)

            if len(u_ns) == 0 or len(v_ns) == 0:
                lns_sim[u_index][v_index] = lns_sim[v_index][u_index] = 0.0

            else:
                sim = 0.0

                for u_n, v_n in itertools.product(u_ns, v_ns):
                    # left의 neighbor들은 right
                    u_n_index = rns_index[u_n]
                    v_n_index = rns_index[v_n]

                    sim += transition_prob_l_to_r[u_index][u_n_index] * transition_prob_l_to_r[v_index][v_n_index] * rns_sim_prev[u_n_index][v_n_index]

                lns_sim[u_index][v_index] = lns_sim[v_index][u_index] = r * sim


    def _update_right_partite():
        for u, v in itertools.product(rns, rns):
            if u is v: continue

            u_index, v_index = rns_index[u], rns_index[v]
            u_ns, v_ns = G.get_rn_neighbors(u), G.get_rn_neighbors(v)

            if len(u_ns) == 0 or len(v_ns) == 0:
                rns_sim[u_index][v_index] = rns_sim[v_index][u_index] = 0.0

            else:
                sim = 0.0

                for u_n, v_n in itertools.product(u_ns, v_ns):
                    # right의 neighbor들은 left
                    u_n_index = lns_index[u_n]
                    v_n_index = lns_index[v_n]

                    sim += transition_prob_r_to_l[u_index][u_n_index] * transition_prob_r_to_l[v_index][v_n_index] * lns_sim_prev[u_n_index][v_n_index]

                rns_sim[u_index][v_index] = rns_sim[v_index][u_index] = r * sim


    ## evidance 계산
    _calculate_evidence(lns, lns_index, lns_evidence)
    _calculate_evidence(rns, rns_index, rns_evidence, False)

    ## transition probabiliyt
    _calculate_transition_prob()

    print "evidence"
    print lns_evidence
    print rns_evidence

    print "spread"
    print lns_spread
    print rns_spread

    print "norm weights"
    print norm_weight_l_to_r
    print norm_weight_r_to_l

    print "transition prob."
    print transition_prob_l_to_r
    print transition_prob_r_to_l

    for i in range(max_iter):
        _update_left_partite()
        _update_right_partite()

        #print "%d-~iteration" % (i+1)
        #print lns_sim
        #print rns_sim

        if np.allclose(lns_sim, lns_sim_prev, atol=eps) and np.allclose(rns_sim, rns_sim_prev, atol=eps):
            break

        lns_sim_prev = np.copy(lns_sim)
        rns_sim_prev = np.copy(rns_sim)


    print("Converge after %d iterations (eps=%f)." % ((i+1), eps))

    return (np.multiply(lns_sim, lns_evidence),
            np.multiply(rns_sim, rns_evidence))



if __name__ == "__main__":
    print "example 1"
    print "camera --> hp.com, bestbuy.com"
    print "digital_camera --> hp.com, bestbuy.com"
    G = BipartiteGraph()

    G.add_edge("camera", "hp.com", 1.0)
    G.add_edge("camera", "bestbuy.com", 1.0)
    G.add_edge("digital_camera", "hp.com", 1.0)
    G.add_edge("digital_camera", "bestbuy.com", 1.0)

    lns_sim, rns_sim = simrank_double_plus_bipartite(G)

    print "sim"
    for node, index in G.get_lns_index().iteritems():
        print "%d | %s" % (index, node)
    print lns_sim

    for node, index in G.get_rns_index().iteritems():
        print "%d | %s" % (index, node)
    print rns_sim

    print "example2"
    print "pc --> hp.com"
    print "camera --> hp.com"
    G2 = BipartiteGraph()

    G2.add_edge("pc", "hp.com", 1.0)
    G2.add_edge("camera", "hp.com", 1.0)

    lns_sim, rns_sim = simrank_double_plus_bipartite(G2)

    print "sim"
    for node, index in G2.get_lns_index().iteritems():
        print "%d | %s" % (index, node)
    print lns_sim

    for node, index in G2.get_rns_index().iteritems():
        print "%d | %s" % (index, node)
    print rns_sim

    print "example3"
    print "split into subgraphs"
    print "A -> 1, 2 | B -> 1, 3 | C -> 3 | D -> 4, 5 | E -> 5"
    print "two subgraphs: (A, B, C) and (D, E)"

    G3 = BipartiteGraph()

    G3.add_edge("A", 1)
    G3.add_edge("A", 2)
    G3.add_edge("B", 1)
    G3.add_edge("B", 3)
    G3.add_edge("C", 3)
    G3.add_edge("D", 4)
    G3.add_edge("D", 5)
    G3.add_edge("E", 5)

    for c, subgraph in enumerate(G3.split_subgraphs(), start=1):
        print "%d-subgraph has %d-lns." % (c, subgraph.get_lns_count())
        print subgraph.get_lns()


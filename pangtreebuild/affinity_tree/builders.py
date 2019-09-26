"""Affinity Tree builders"""

from collections import deque
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

from pangtreebuild.tools import logprocess
from pangtreebuild.affinity_tree import parameters
from pangtreebuild.affinity_tree import poa
from pangtreebuild.affinity_tree import structure

from pangtreebuild.datamodel.Poagraph import Poagraph
from pangtreebuild.datamodel.Sequence import SequenceID, SeqPath


global_logger = logprocess.get_global_logger()
tresholds_logger = logprocess.get_logger('tresholdsCSV')
detailed_logger = logprocess.get_logger('details')


class AffinityTreeBuildException(Exception):
    """Any exception connected with Affinity Tree build process."""

    pass


def build_poa_affinity_tree(poagraph: Poagraph,
                            blosum: parameters.Blosum,
                            output_dir: Path,
                            hbmin: parameters.Hbmin,
                            verbose: bool) -> structure.AffinityTree:
    """Builds Affinity Tree coherent with poa software.

    This method builds a simple version of Affinity Tree as it uses a single call to poa software.
    Poa provides division of sequences in Poagraph into consistent groups with a consensus path assigned to every group.
    These groups are converted in this method to Affinity Tree nodes and connected with a dummy root node so the result
    is coherent with pangtree definition of Affinity Tree.

    Args:
        poagraph: Poagraph containing sequences to be divided into groups (Affinity Tree nodes).
        blosum: BLOSUM matrix.
        output_dir: Path to a directory that can be used by poa software.
        hbmin: Parameter required by poa software. The minimum value of sequence compatibility to generated consensus.
        verbose: Switch to control logging intensity.

    Raises:
        AffinityTreeGenerationException: if consensuses cannot be found.
    """
    def _convert_consensus_paths_to_affinity_tree_nodes():
        at_nodes = []
        assigned_sequences = []
        for c_id, c_info in consensus_paths.items():
            assigned_sequences += c_info.assigned_sequences_ids
            compatibilities = poagraph.get_compatibilities(poagraph.get_sequences_ids(), c_info.path)
            if len(c_info.assigned_sequences_ids):
                mincomp = min([c for seq_id, c in compatibilities.items() if seq_id in c_info.assigned_sequences_ids])
            else:
                mincomp = 0
            at_nodes.append(structure.AffinityNode(id_=structure.AffinityNodeID(c_id + 1),
                                         parent=structure.AffinityNodeID(0),
                                         sequences=c_info.assigned_sequences_ids,
                                         mincomp=mincomp,
                                         compatibilities=compatibilities,
                                         consensus=c_info.path,
                                         children=[]))

        node_for_unassigned_sequences = structure.AffinityNode(parent=structure.AffinityNodeID(0),
                                                     sequences=[seq_id
                                                                for seq_id in poagraph.get_sequences_ids()
                                                                if seq_id not in assigned_sequences],
                                                     id_=structure.AffinityNodeID(len(at_nodes) + 1),
                                                     mincomp=structure.Compatibility(0),
                                                     children=[])
        at_nodes.append(node_for_unassigned_sequences)
        return at_nodes

    global_logger.info("POA defined affinity tree generation started.")
    _raise_error_if_invalid_poagraph(poagraph)
    try:
        consensus_paths = poa.get_consensuses(poagraph,
                                              poagraph.get_sequences_ids(),
                                              output_dir,
                                              "poa_tree",
                                              blosum.filepath,
                                              hbmin)
    except poa.NoConsensusError:
        raise AffinityTreeBuildException("Cannot find consensus in given Affinity Tree.")

    consensus_nodes = _convert_consensus_paths_to_affinity_tree_nodes()
    root_node = structure.AffinityNode(id_=structure.AffinityNodeID(0),
                             children=[consensus_node.id_ for consensus_node in consensus_nodes])
    affinity_tree = structure.AffinityTree([root_node] + consensus_nodes)
    global_logger.info("POA defined affinity tree generation started.")
    return affinity_tree


def build_affinity_tree(poagraph: Poagraph,
                        blosum: parameters.Blosum,
                        output_dir: Path,
                        stop: parameters.Stop,
                        p: parameters.P,
                        verbose: bool) -> structure.AffinityTree:
    """Builds Affinity Tree as defined in paper 'Getting insight into the pan-genome structure with Pangtree'.

    This method builds an Affinity Tree by iterative calls to poa software. Full algorithm and idea are described in
    the above-mentioned paper.

    Args:
        poagraph: Poagraph containing sequences to be divided into groups (Affinity Tree nodes).
        blosum: BLOSUM matrix.
        output_dir: Path to a directory that can be used by poa software.
        stop: Value of mincomp above which the affinity tree node is no more split.
        p: Value changing the linear meaning of compatibility when searching for cutoff.
        verbose: Switch to control logging intensity.

    Raises:
        AffinityTreeGenerationException: if consensuses cannot be found.

    Returns:
        Affinity Tree generated with Pangtree algorithm.
    """

    global_logger.info("Affinity Tree generation started.")
    if verbose:
        logprocess.add_file_handler_to_logger(output_dir, "tresholdsCSV", "tresholds.csv", "%(message)s", False)
    _raise_error_if_invalid_poagraph(poagraph)

    root_node = _get_root_node(poagraph, blosum.filepath, output_dir, p)
    affinity_tree = structure.AffinityTree([root_node])

    nodes_to_process = deque([affinity_tree.get_node(structure.AffinityNodeID(0))])
    while nodes_to_process:
        node = nodes_to_process.pop()

        children_nodes = _get_children_nodes_looping(node,
                                            poagraph,
                                            output_dir,
                                            blosum.filepath,
                                            p,
                                            affinity_tree.get_max_node_id())
        if len(children_nodes) == 1:
            continue

        for child in children_nodes:
            child.compatibilities = poagraph.get_compatibilities(sequences_ids=[*poagraph.sequences.keys()],
                                                                 consensus_path=child.consensus,
                                                                 p=p)
            node.children.append(child.id_)
            affinity_tree.nodes.append(child)
            if not _node_is_ready(child, stop):
                nodes_to_process.append(child)
    global_logger.info("Affinity Tree generation finished.\n")
    return affinity_tree


def _raise_error_if_invalid_poagraph(poagraph: Poagraph) -> None:
    """Checks if any sequence is present in the input poagraph.

    Args:
        poagraph: Poagraph which is input to the Affinity Tree generation algorithm.
    Raises:
        AffinityTreeGenerationException: If no sequence is present in the poagraph.
    """

    if len(poagraph.sequences) == 0:
        raise AffinityTreeBuildException("Invalid poagraph."
                                              "No paths in poagraph."
                                              "Affinity Tree generation is impossible.")


def _get_root_node(poagraph: Poagraph,
                   blosum_path: Path,
                   output_dir: Path,
                   p: parameters.P) -> structure.AffinityNode:
    """Creates root node of the Affinity Tree with assigned consensus path and all sequences."""

    detailed_logger.info("Getting the root affinity node...")
    all_poagraph_sequences_ids = poagraph.get_sequences_ids()
    try:
        consensus_paths = poa.get_consensuses(poagraph,
                                              all_poagraph_sequences_ids,
                                              output_dir,
                                              "root",
                                              blosum_path,
                                              hbmin=parameters.Hbmin(0),
                                              specific_consensuses_id=[0])
    except poa.NoConsensusError:
        raise AffinityTreeBuildException("Cannot find root consensus.")
    compatibilities = poagraph.get_compatibilities(all_poagraph_sequences_ids,
                                                   consensus_paths[0].path,
                                                   p=p)
    affinity_node = structure.AffinityNode(id_=structure.AffinityNodeID(0),
                                 sequences=[*poagraph.sequences.keys()],
                                 mincomp=_get_min_comp(all_poagraph_sequences_ids, compatibilities),
                                 compatibilities=compatibilities,
                                 consensus=consensus_paths[0].path)
    detailed_logger.info(f"New affinity node created: {str(affinity_node)}")
    return affinity_node


def _get_children_nodes_looping(node: structure.AffinityNode,
                                poagraph: Poagraph,
                                output_dir: Path,
                                blosum_path: Path,
                                p: parameters.P,
                                current_max_affinity_node_id: int) -> List[structure.AffinityNode]:
    """Generates children of given Affinity Tree node."""

    children_nodes: List[structure.AffinityNode] = []
    not_assigned_sequences_ids: List[SequenceID] = node.sequences
    detailed_logger.info(f"Getting children nodes for affinity node {node.id_}...")

    affinity_node_id = 0
    so_far_cutoffs: List[structure.Compatibility] = []
    while not_assigned_sequences_ids:
        detailed_logger.info(f"### Getting child {len(so_far_cutoffs)}...")
        child_ready = False
        attempt = 0
        current_candidates = not_assigned_sequences_ids
        while not child_ready:
            consensus_candidate = poa.get_consensuses(poagraph,
                                                      current_candidates,
                                                      output_dir,
                                                      f"parent_{node.id_}_child_{len(so_far_cutoffs)}_attempt_{attempt}",
                                                      blosum_path,
                                                      parameters.Hbmin(0),
                                                      specific_consensuses_id=[0])[0].path
            compatibilities_to_consensus_candidate = poagraph.get_compatibilities(sequences_ids=not_assigned_sequences_ids,
                                                                                  consensus_path=consensus_candidate,
                                                                                  p=p)
            compatibilities_to_consensus_candidate[SequenceID("parent")] = node.mincomp
            qualified_sequences_ids_candidates, cutoff = _get_qualified_sequences_ids_and_cutoff(
                compatibilities_to_max_c=compatibilities_to_consensus_candidate,
                so_far_cutoffs=so_far_cutoffs,
                splitted_node_id=node.id_)

            if qualified_sequences_ids_candidates == current_candidates or attempt == 10:
                if attempt == 10:
                    detailed_logger.info("Attempt treshold 10 exceeded!")
                affinity_node_id += 1

                affinity_node = structure.AffinityNode(
                    id_=structure.AffinityNodeID(current_max_affinity_node_id + affinity_node_id),
                    parent=node.id_,
                    sequences=qualified_sequences_ids_candidates,
                    mincomp=_get_min_comp(node_sequences_ids=qualified_sequences_ids_candidates,
                                          comps_to_consensus=compatibilities_to_consensus_candidate),
                    consensus=SeqPath(consensus_candidate))
                children_nodes.append(affinity_node)
                not_assigned_sequences_ids = list(set(not_assigned_sequences_ids) - set(qualified_sequences_ids_candidates))
                child_ready = True
                so_far_cutoffs.append(affinity_node.mincomp)
            else:
                current_candidates = qualified_sequences_ids_candidates
                attempt += 1

    detailed_logger.info("Children nodes generated.")

    return children_nodes


def _get_min_comp(node_sequences_ids: List[SequenceID],
                  comps_to_consensus: Dict[SequenceID, structure.Compatibility]) -> structure.Compatibility:
    """Find minimum compatibility from the compatibilities of given sequences.

    Args:
        node_sequences_ids: List of sequences IDs that the search is limited to.
        comps_to_consensus: Source of compatibilities values.

    Returns:
        The minimum compatibility.

    Raises:
        AffinityTreeBuildException: If sequence IDs from the list can be found in the compatibilities dictionary.
    """

    compatibilities_of_node_sequences = [comp
                                         for seq_id, comp
                                         in comps_to_consensus.items()
                                         if seq_id in node_sequences_ids]
    if not compatibilities_of_node_sequences:
        raise AffinityTreeBuildException("Cannot provide mincomp."
                                         "No sequences assigned to this affinity node.")
    return min(compatibilities_of_node_sequences)


def _get_qualified_sequences_ids_and_cutoff(compatibilities_to_max_c: Dict[SequenceID, structure.Compatibility],
                                            so_far_cutoffs: List[structure.Compatibility], splitted_node_id) \
        -> Tuple[List[SequenceID], structure.Compatibility]:
    """Choose sequences qualified to be enclosed in single node based on their compatibilities values."""

    node_cutoff = _find_node_cutoff(compatibilities=[*compatibilities_to_max_c.values()],
                                    so_far_cutoffs=so_far_cutoffs)
    tresholds_logger.info(f"Splitting {splitted_node_id}; NODE; {compatibilities_to_max_c}; "
                          f"{node_cutoff.cutoff}; {node_cutoff.explanation}")
    compatibtle_sequences_ids = _get_sequences_ids_above_cutoff(compatibilities_to_max_c, node_cutoff.cutoff)
    detailed_logger.info(f"{len(compatibtle_sequences_ids)} sequences ({compatibtle_sequences_ids} are "
                         f"qualified to be enclosed in this node, mincomp = {node_cutoff.cutoff}.")
    return compatibtle_sequences_ids, node_cutoff.cutoff


def _node_is_ready(node: structure.AffinityNode, stop: parameters.Stop) -> bool:
    """Checks if the node should be further split based on Stop parameter and count of sequences assigned.

    Args:
        node: Node to be checked.
        stop: Stop parameter

    Returns:
        bool: Information whether the node should be further split.
    """

    if len(node.sequences) == 1 or node.mincomp.base_value() >= stop:
        detailed_logger.info(f"Node {node.id_} satisfied requirements and won't be split!")
        return True
    return False


class FindCutoffResult:
    """Result of cutoff finding.

    Args:
        cutoff: The minimum accepted Compatibility value.
        explanation: The explanation of the choice.

    Attributes:
        cutoff (Compatibility): The minimum accepted Compatibility value.
        explanation (str): The explanation of the choice.
    """
    def __init__(self, cutoff: structure.Compatibility, explanation: str):
        self.cutoff: structure.Compatibility = cutoff
        self.explanation: str = explanation


def _find_node_cutoff(compatibilities: List[structure.Compatibility],
                      so_far_cutoffs: List[structure.Compatibility]) -> FindCutoffResult:
    """Searches for cutoff.

    Args:
        compatibilities: List of compatibilities to be searched.
        so_far_cutoffs: Cutoffs from previous children from node being currently split.

    Returns:
         The cutoff and the explanationo as _FindCutoffResult.
    """

    if not so_far_cutoffs:
        cutoff = _find_max_distance(compatibilities)
        reason = "No so far cutoffs. Find max distance in sorted values."
    else:
        guard = min(so_far_cutoffs)
        sorted_comp = sorted(compatibilities)
        if guard <= sorted_comp[0]:
            cutoff = sorted_comp[0]
            reason = "guard < min(compatibilities). Return min(compatibilities)."
        elif guard >= sorted_comp[-1]:
            cutoff = _find_max_distance(compatibilities)
            reason = "guard > max(compatibilities). Find max distance in sorted values."
        else:
            first_comp_greater_than_guard_index = [i for i, c in enumerate(sorted_comp) if c > guard][0]
            cutoff = _find_max_distance(sorted_comp[0:first_comp_greater_than_guard_index + 1])
            reason = "Find max distance in sorted_comp[0:first_comp_greater_than_guard_index + 1]"
    return FindCutoffResult(cutoff, reason)


def _find_max_distance(compatibilities: List[structure.Compatibility]) -> structure.Compatibility:
    """Sorts compatibilities and searches for the largest gap.

    Args:
        compatibilities: List of compatibilities to be searched for the distance.

    Returns:
        The first compatibility value after the largest gap in sorted compatibilities.

    Raises:
        ValueError: If provided compatibilities list is empty.
    """

    def break_if_empty(compatibilities: List[structure.Compatibility]) -> None:
        if not list(compatibilities):
            raise ValueError("Empty compatibilities list. Cannot find cutoff.")

    break_if_empty(compatibilities)
    if len(compatibilities) == 1:
        return compatibilities[0]

    sorted_values = sorted(compatibilities)
    distances = np.array([sorted_values[i + 1] - sorted_values[i] for i in range(len(sorted_values) - 1)])
    max_distance_index: int = np.argmax(distances)
    return sorted_values[max_distance_index + 1]


def _get_sequences_ids_above_cutoff(compatibilities: Dict[SequenceID, structure.Compatibility],
                                    cutoff: structure.Compatibility) -> List[SequenceID]:
    """Filters the Seuqences IDs to find the ones with compatibility above required treshold.

    Args:
        compatibilities: Dictionary of sequences IDs and corresponding compatibilities.
        cutoff: Required minimum compatibility value of the qualified sequences.

    Returns:
        List of Sequences IDs that have greater compatibility than required cutoff value.
    """
    return [seq_id for seq_id, comp in compatibilities.items() if comp >= cutoff and seq_id != SequenceID("parent")]

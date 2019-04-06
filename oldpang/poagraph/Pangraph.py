from io import StringIO
from typing import List, Dict
import numpy as np

from datamodel.CompatibilityToPath import CompatibilityToPath
from datamodel.PangraphBuilders.PangraphBuilderBase import PangraphBuilderBase
from datamodel.PangraphBuilders.PangraphBuilderFromDAG import PangraphBuilderFromDAG
from datamodel.PangraphBuilders.PangraphBuilderFromMAF import PangraphBuilderFromMAF
from fasta_providers.FastaProvider import FastaProvider
from metadata.MultialignmentMetadata import MultialignmentMetadata
from datamodel.PangraphBuilders.PangraphBuilderFromPO import PangraphBuilderFromPO
from tools import loggingtools
from .Node import Node
from .custom_types import NodeID, SequenceID
from .DataType import DataType

global_logger = loggingtools.get_logger("")


class Pangraph:
    def __init__(self, datatype: DataType):
        self.nodes: List[Node] = []
        self.paths: Dict[SequenceID, List[List[NodeID]]] = {}
        self.datatype: DataType = datatype

    def __eq__(self, other):
        return (self.nodes == other.nodes and
                self.paths == other.paths and
                self.datatype == other.datatype)

    def build_from_maf_firstly_converted_to_dag(self,
                                                mafcontent: str,
                                                fasta_source: FastaProvider,
                                                genomes_info: MultialignmentMetadata,
                                                missing_nucleotide_symbol: str = "?"):
        global_logger.info("Building pangraph from MAF firstly converted to DAG...")
        builder: PangraphBuilderBase = PangraphBuilderFromDAG(genomes_info, missing_nucleotide_symbol, fasta_source)
        self._build(builder, mafcontent)

    def build_from_maf(self, mafcontent: str, genomes_info: MultialignmentMetadata):
        global_logger.info("Building pangraph from raw MAF")
        builder: PangraphBuilderBase = PangraphBuilderFromMAF(genomes_info)
        self._build(builder, mafcontent)

    def build_from_po(self, pocontent: str, genomes_info: MultialignmentMetadata, missing_nucleotide_symbol: str):
        global_logger.info("Building pangraph from PO...")
        builder: PangraphBuilderBase = PangraphBuilderFromPO(genomes_info, missing_nucleotide_symbol)
        self._build(builder, pocontent)

    def _build(self, builder: PangraphBuilderBase, build_input: str):
        builder.build(StringIO(build_input), self)

    def get_compatibilities(self, sequences_ids: List[SequenceID], consensus: List[NodeID], p: float) -> \
            Dict[SequenceID, CompatibilityToPath]:
        compatibilities = dict()
        for seq_id in sequences_ids:
            try:
                sequence_paths = self.paths[seq_id]
            except KeyError:
                raise Exception("No sequence with given ID in pangraph.")
            if len(sequence_paths) == 1:
                sequence_path = sequence_paths[0]
            else:
                sequence_path = [node_id for path in sequence_paths for node_id in path]
            compatibilities[seq_id] = CompatibilityToPath(len(set(sequence_path).intersection(set(consensus))) /
                                                          len(sequence_path), p)
        return compatibilities

    def get_sequence_nodes_count(self, seq_id):
        if seq_id not in self.paths:
            raise Exception("No sequence with given ID in pangraph.")
        return sum([len(path) for path in self.paths[seq_id]])

    def get_sequences_weights(self, sequences_ids):
        if not sequences_ids:
            return dict()

        a = np.zeros(len(self.nodes), dtype=np.int)
        unweighted_sources_weights = {}
        for seq_id in sequences_ids:
            for path in self.paths[seq_id]:
                a[path] += 1

        for seq_id in sequences_ids:
            sequence_nodes_ids = [node_id for path in self.paths[seq_id] for node_id in path]
            unweighted_sources_weights[seq_id] = np.mean(a[sequence_nodes_ids])

        max_weight = max(unweighted_sources_weights.values())
        min_weight = min(unweighted_sources_weights.values())
        diff_weight = max_weight - min_weight
        if diff_weight == 0:
            normalized_sources_weights_dict = {path_key: 100 for path_key in unweighted_sources_weights.keys()}
        else:
            normalized_sources_weights_dict = {path: int((weight - min_weight)/diff_weight*100)
                                               for path, weight in unweighted_sources_weights.items()}
        return normalized_sources_weights_dict

    def get_sequences_ids(self) -> List[SequenceID]:
        return [*self.paths.keys()]

    def path_is_empty(self, seq_id):
        return sum(len(path) for path in self.paths[seq_id]) == 0


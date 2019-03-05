from consensus.algorithm.FindCutoff import MAX1, MAX2, FindMaxCutoff, FindNodeCutoff, NODE1, NODE2, NODE3, NODE4
from graph2.FastaSource import EntrezFastaSource, FastaFileSystemSource
from metadata import reader as metadatareader
from consensus.algorithm import tree as consensustree
from consensus.algorithm import simple as consensussimple
from graph2.Pangraph import Pangraph
from userio import pathtools
from userio.PangenomeParameters import ConsensusAlgorithm, FastaComplementationOption, MaxCutoffOption, \
    NodeCutoffOption, PangenomeParameters


class Pangenome:
    def __init__(self, pangenome_parameters):
        self.params: PangenomeParameters = pangenome_parameters

        self.genomes_info = self._build_genomes_info()
        self.dagmaf = None
        self.pangraph = Pangraph()

    def build_from_maf_firstly_converted_to_dag(self):
        if self.params.fasta_complementation_option is FastaComplementationOption.NO:
            fasta_source = None
        elif self.params.fasta_complementation_option is FastaComplementationOption.NCBI:
            fasta_source = EntrezFastaSource()
        elif self.params.fasta_complementation_option is FastaComplementationOption.LOCAL:
            fasta_source = FastaFileSystemSource(self.params.local_fasta_dirpath)
        else:
            raise Exception("Not known fasta complementation option. Should be of type FastaComplementationOption."
                            "Cannot build pangraph.")

        self.genomes_info.feed_with_maf_data(self.params.multialignment_file_content)
        self.pangraph.build_from_maf_firstly_converted_to_dag(mafcontent=self.params.multialignment_file_content,
                                                              fasta_source=fasta_source,
                                                              genomes_info=self.genomes_info)

    def build_from_maf(self):
        self.genomes_info.feed_with_maf_data(self.params.multialignment_file_content)
        self.pangraph.build_from_maf(self.params.multialignment_file_content, self.genomes_info)

    def generate_fasta_files_to_directory(self):
        output_dir = pathtools.create_child_dir(self.params.output_path, 'fasta')
        raise NotImplementedError("Generate fasta files not implemented!")

    def generate_consensus(self):
        output_dir = pathtools.create_child_dir(self.params.output_path, 'consensus')

        if self.params.consensus_type == ConsensusAlgorithm.SIMPLE:
            self.pangraph = consensussimple.run(outputdir=output_dir,
                                                pangraph=self.pangraph,
                                                hbmin=self.params.hbmin,
                                                genomes_info=self.genomes_info,
                                                filename_prefix="simple")
        elif self.params.consensus_type == ConsensusAlgorithm.TREE:
            cutoffs_log_path = self._create_cutoffs_log_path(output_dir)
            max_cutoff_strategy = self._get_max_cutoff_strategy(cutoffs_log_path)
            node_cutoff_strategy = self._get_node_cutoff_strategy(cutoffs_log_path)
            self.pangraph = consensustree.run(outputdir=output_dir,
                                              cutoffs_log_path=cutoffs_log_path,
                                              pangraph=self.pangraph,
                                              genomes_info=self.genomes_info,
                                              max_node_strategy=max_cutoff_strategy,
                                              node_cutoff_strategy=node_cutoff_strategy,
                                              stop=self.params.stop,
                                              re_consensus=self.params.re_consensus
                                              )

    def _create_cutoffs_log_path(self, consensus_output_dir):
        return pathtools.get_child_file_path(consensus_output_dir, "cutoffs_log.csv")

    def _get_max_cutoff_strategy(self, cutoffs_log_path) -> FindMaxCutoff:
        if self.params.max_cutoff_option == MaxCutoffOption.MAX1:
            return MAX1(self.params.range, cutoffs_log_file_path=cutoffs_log_path)
        elif self.params.max_cutoff_option == MaxCutoffOption.MAX2:
            return MAX2(cutoffs_log_file_path=cutoffs_log_path)

    def _get_node_cutoff_strategy(self, cutoffs_log_path) -> FindNodeCutoff:
        if self.params.node_cutoff_option == NodeCutoffOption.NODE1:
            return NODE1(self.params.multiplier, cutoffs_log_file_path=cutoffs_log_path)
        elif self.params.node_cutoff_option == NodeCutoffOption.NODE2:
            return NODE2(self.params.multiplier, cutoffs_log_file_path=cutoffs_log_path)
        elif self.params.node_cutoff_option == NodeCutoffOption.NODE3:
            return NODE3(cutoffs_log_file_path=cutoffs_log_path)
        elif self.params.node_cutoff_option == NodeCutoffOption.NODE4:
            return NODE4(cutoffs_log_file_path=cutoffs_log_path)

    def _build_genomes_info(self):
        if not self.params.metadata_file_content:
            raise NotImplementedError("Metadata not given. Cannot build pangenome object.")
        # todo check if metadata given else generate
        return metadatareader.read(self.params.metadata_file_content)

    def run(self):
        """Creates Pangraph and runs required algorithms."""

        if self.params.not_dag:
            self.build_from_maf()
        else:
            self.build_from_maf_firstly_converted_to_dag()

        if self.params.generate_fasta:
            self.generate_fasta_files_to_directory()

        if self.params.consensus_type != ConsensusAlgorithm.NO:
            self.generate_consensus()



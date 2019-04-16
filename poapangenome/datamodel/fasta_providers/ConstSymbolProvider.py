from datamodel.Node import Base
from datamodel.Sequence import SequenceID
from datamodel.fasta_providers.FastaProvider import FastaProvider
from datamodel.input_types import MissingSymbol


class ConstSymbolProvider(FastaProvider):
    def __init__(self, missing_symbol: MissingSymbol):
        self.missing_symbol: Base = Base(missing_symbol.value)

    def get_base(self, sequence_id: SequenceID, i: int) -> Base:
        return self.missing_symbol
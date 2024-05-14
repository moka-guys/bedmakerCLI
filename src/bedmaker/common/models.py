"""
Models for the transcripts, regions, SNPs, genes, panels, and bedfiles tools
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    constr,
    root_validator,
    validator,
)


# TODO add these Enums to the models
class IdType(Enum):
    """
    Docstring
    """

    REFSEQ = "refseq"
    ENSEMBL = "ensembl"
    UNSUPPORTED = "unsupported"


class Assembly(Enum):
    """
    Docstring
    """

    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"


class CommonModel(BaseModel):
    """
    A common base class for all models to share common functionality.
    """

    @classmethod
    def from_dict(cls, data):
        """
        Create an instance of the model from a dictionary.
        """
        return cls(**data)

    def to_dict(self):
        """
        Convert model instance into a dictionary.
        """
        return self.model_dump()


class UserInput(CommonModel):
    """
    Model to hold user input data (a list of IDs read from the CLI or provided in a file)
    """

    batch_id: str  # primary key
    input_args_json: str
    requested_by: str
    requested_date: datetime
    request_type: str  # e.g. panel, gene, transcript, region, snp
    batch_log: str
    user_panel_name: str


class UserRequest(CommonModel):
    """
    Base class for all user requests (a request is the atomised version of a UserInput)
    For example if a list of IDs is provided in a file, the UserInput will be split into multiple UserRequests depending on the type of ID provided:
    - Each provided transcript ID in UserInput will have a 1:1 mapping to a UserRequest
    - Each provided region in UserInput will have a 1:1 mapping to a UserRequest
    - Each provided SNP in UserInput will have a 1:1 mapping to a UserRequest
    For genes and panels, the mapping will be 1:many:
    - Each provided panel will have a 1:many mapping being further split into multiple UserRequests with 1 UserRequest for each transcript represented by the panel
    - Each provided gene will have a 1:many mapping being further split into multiple UserRequests with 1 UserRequest for each transcript represented by the gene
    """

    request_id: str  # primary key
    batch_id: str
    input_arg: str
    request_log: Optional[str] = None
    request_status: Optional[str] = "draft"


class PanelApp(CommonModel):
    """
    Model to hold input data by PanelApp panels
    """

    panel_app_id: str
    batch_id: str
    genes: List[Gene]
    name: str
    hash_id: str
    version: str
    disease_sub_group: str
    relevant_disorders: str
    signed_off: str
    number_of_genes: str
    number_of_regions: str
    confidence_level: int  # 3 = green gene, 2 = amber gene, 1 = red gene


class Gene(CommonModel):
    """
    Model to hold input data by gene IDs
    """

    hgnc_symbol: str
    batch_id: str
    stable_id: str
    stable_id_version: int
    assembly: str
    gene_checksum: str
    transcripts: List[Transcript]


class Region(CommonModel):
    """
    Model to hold region data specified by genomic co-ordinates (genomic ranges or SNPs)
    """

    request_id: str
    region_name: str
    genomic_range: GenomicRange


class Snp(CommonModel):
    """
    Model to hold data specified by dbSNP IDs
    """

    request_id: str
    dbSNP_id: str
    genomic_range: GenomicRange


class GenomicRange(CommonModel):
    range_id: str
    loc_start: int
    loc_end: int
    loc_region: str  # Chromosome
    loc_strand: int
    loc_checksum: str


class Transcript(CommonModel):
    """
    Model to hold transcript specific information
    """

    request_id: str
    ens_stable_id: Optional[str] = None
    ens_stable_id_version: Optional[int] = None
    refseq_stable_id: Optional[str] = None
    refseq_stable_id_version: Optional[int] = None
    assembly: Optional[str] = None
    biotype: Optional[str] = None
    transcript_checksum: Optional[str] = None
    mane_type: Optional[str] = None
    gene_name: Optional[str] = None
    gene_id: Optional[str] = None
    gene_id_version: Optional[int] = None
    genomic_ranges: GenomicRange
    loc_checksum: Optional[str] = None
    exons: List[Exon] = []
    exon_set_checksum: Optional[str] = None
    utrs: List[Utr] = []

    # TODO: Add to the model
    # @validator("refseq_stable_id", pre=True)
    # def check_refseq_id(cls, v):
    #     if v and not v.startswith(("NM_", "NR_")):
    #         raise ValueError(
    #             "Invalid RefSeq ID format: RefSeq transcript must start with 'NM_' or 'NR_'"
    #         )
    #     return v

    # @validator("mane_transcript", pre=False)
    # def check_mane_id(cls, v):
    #     if v and not v.startswith(("NM_", "NR_")):
    #         raise ValueError("Invalid RefSeq ID format")
    #     return v

    # @validator("stable_id", pre=False)
    # def check_ensembl_id(cls, v):
    #     if v and not v.startswith("ENST"):
    #         raise ValueError("Invalid Ensembl ID format")
    #     return v


class ManeList(CommonModel):
    """
    Model to hold lookup table of MANE transcripts from TARK API
    Useful for checking if a MANE transcript is available for a given gene
    and in clinical plus transcript is also available
    """

    ens_stable_id: Optional[str] = None
    ens_stable_id_version: Optional[int] = None
    refseq_stable_id: str
    refseq_stable_id_version: Optional[int] = None
    mane_type: Optional[str] = None
    ens_gene_name: Optional[str] = None
    access_date: datetime


class Exon(CommonModel):
    """
    Model to hold exon specific information
    """

    exon_id: int | None = None
    exon_id_version: int | None = None
    transcript_stable_id: str | None = None
    genomic_ranges: GenomicRange
    exon_order: int | None = None
    exon_checksum: str | None = None


class Utr(CommonModel):
    """
    Model to hold UTR specific information
    """

    utr_id: int | None = None
    utr_type: str | None = None  # 5' or 3'
    ens_stable_id: str | None = None
    genomic_ranges: GenomicRange | None = None

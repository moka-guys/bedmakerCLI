# BedMakerCLI

`bedmaker` is built around several tools for creating and validating bedfiles for use in a clinical genetics department.  Bedmaker has several advantages over manually creating a bed file:

- BedMaker creates a clear audit trail for any bedfiles produced.
- BedMaker has inbuilt validation of output bedfiles against inputs and PanelApp panels.
- Bedmaker automates version control of produced files.

Each of the tools in the workflow has a clearly defined function within the workflow.

- Input tools:
  - `transcripts` - allows the input of transcripts via transcripts IDs.
  - `coordinates` - allows the input of genomic coordinates via dbSNP IDs or as genomic coordinates.
  - `genes` - returns the appropriate transcripts for input gene names or IDs.
- Consolidation tool:
  - `panels` - integrates and transforms gene, transcript, and coordinate data into a panel describing the requested genomic regions in preparation for writing to a bedfile.
- Output tools:
  - `bedfiles` - converts the output from the `panels` tool into bedfiles in line with the provided formatting file.
  - `validate` - validates the produced bedfile against the provided inputs to ensure no regions have been dropped during processing.  Allows the bedfile to be checked against PanelApp panels to ensure no regions have been dbSNP RefSNP ID missed.

These tools can be chained together on Unix-like operating systems using the pipe operator, `|`, with each tool taking the output of the previous tool as input. In this manner complex bedfiles can be produced from a multitude of inputs in a simple and transparent manner.

## User Tutorial

Clinical scientists use bedfiles to define regions of the genome ...

### Installing BedMakerCLI

`bedmaker` is available as a python package from....

### Typical Use Case for Bedmaker

In the example below we look at a typical use case for `bedmaker`.  A clinical scientist has provided several input files:

- A transcript CSV file where the first column is transcript IDs in either RefSeq or Ensembl format.  The majority of these are expected to have a MANE transcript, although some may be for protein-coding which do not have an agreed upon MANE transcript, or RNA-coding genes which are not covered by MANE transcripts.
- A genome co-ordinate csv file with the columns, `chr`, `start`, `stop`, `region_id` where the clinical scientist has requested specific genomic regions for inclusion in the bedfile. The regions should be specified in ....  The `region_id` will be used to name the region inm the created bedfile.  Examples of inputs include:
  - A SNP, ...
  - A range...
- A SNP csv file where the first column uses the dbSNP RefSNP ID.

## Developer Information

BedMaker is developed in python 3.12, using `Typer` and `Rich` to provide the CLI and utilizes a `TinyDB` database for storing the data.

### Deploying BedMaker

From within the BedMaker project run:

```
poetry install
```

### Pitfalls

The TARK API returns a field "stable_id" which can either be the refseq ID or the Ensembl ID to match the format of the query ID.


### Project Layout

Each of the tools has a separate folder in the project:

```bash
/bedmakerCLI/src/bedmaker
├── bedfiles
├── common
├── coordinates
├── genes
├── panels
├── transcripts
└── validate
```

Shared resources for all the tools relating to the database, exceptions, and 3rd party APIs are in the `common` folder:

```bash
/bedmakerCLI/src/bedmaker/common
├── db.py
├── exceptions.py
├── models.py
├── panel_app_api.py
├── requests.py
└── tark_api.py
```

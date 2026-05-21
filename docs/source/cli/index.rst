CLI Overview
============

``cis-gs`` is the command-line counterpart of the GUI. Every workflow
step has its own subcommand, plus a guided **wizard** that walks new
users through the whole pipeline.

.. code-block:: text

   usage: cis-gs [-h] {wizard,fetch,extract,search,feed,coexpr,
                       kmeans,enrich-kegg,id-convert} ...

   wizard         Step-by-step wizard (recommended for new users)
   fetch          Download a genome + annotation from NCBI
   extract        Extract promoter sequences from FASTA + GFF3
   search         Scan promoters for motif occurrences
   feed           Couple motif hits with an expression table
   coexpr         Build a co-expression network
   kmeans         K-means clustering with elbow / silhouette
   enrich-kegg    KEGG over-representation analysis
   id-convert     Convert gene IDs across namespaces (MyGene.info, batched)

Every subcommand accepts ``-i`` / ``--interactive`` for a step-by-step
prompt.

Conveniences
------------

* **Did-you-mean** — mistype a command and Cis-GS suggests the closest
  match using ``difflib.SequenceMatcher``.
* **Live KEGG dropdown** in interactive mode (11 700+ organisms).
* **Live NCBI Taxonomy search** in interactive mode.
* **Batched MyGene.info** — 10 000 gene IDs convert in ~60 s instead of
  ~60 min.

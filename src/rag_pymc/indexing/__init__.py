"""Sparse indexing contracts and implementation."""

from rag_pymc.indexing.bm25 import BM25Index
from rag_pymc.indexing.protocols import SparseIndex

__all__ = ["BM25Index", "SparseIndex"]

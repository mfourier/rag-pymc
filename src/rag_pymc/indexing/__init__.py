"""Sparse and dense indexing contracts and implementations."""

from rag_pymc.indexing.bm25 import BM25Index
from rag_pymc.indexing.dense import DenseIndexError, ExactCosineIndex
from rag_pymc.indexing.protocols import DenseIndex, SparseIndex

__all__ = ["BM25Index", "DenseIndex", "DenseIndexError", "ExactCosineIndex", "SparseIndex"]

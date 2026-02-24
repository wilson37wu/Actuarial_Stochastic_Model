"""
Term life insurance product.
"""
from dataclasses import dataclass
from typing import List

from .base import BaseInsuranceContract
from .data_classes import PolicyLoan
from ...enums import ProductType

@dataclass
class TermInsurance(BaseInsuranceContract):
    """Term life insurance contract."""

    def __init__(self,
                 face_amount: float,
                 term_length: int,
                 **kwargs):
        kwargs['product_type'] = ProductType.TERM
        super().__init__(
            face_amount=face_amount,
            term_length=term_length,
            **kwargs
        )
        self.loans: List[PolicyLoan] = []

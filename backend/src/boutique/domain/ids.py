from typing import NewType
from uuid import UUID

from boutique.domain.types import Identifier

AuthSubject = NewType("AuthSubject", Identifier)
CustomerID = NewType("CustomerID", Identifier)
OrderID = NewType("OrderID", Identifier)
ProductID = NewType("ProductID", Identifier)
UserID = NewType("UserID", UUID)

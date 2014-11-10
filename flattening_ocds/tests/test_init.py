from flattening_ocds  import decimal_default
from decimal import Decimal
import json

def test_decimal_default():
    assert json.dumps(Decimal('1.2'), default=decimal_default) == '1.2'
    assert json.dumps(Decimal('42'), default=decimal_default) == '42'

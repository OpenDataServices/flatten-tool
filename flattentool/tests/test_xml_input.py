from flattentool.json_input import JSONParser

def test_xml_empty():
    parser = JSONParser(
        json_filename='flattentool/tests/fixtures/empty.xml',
        root_list_path='iati-activity',
        schema_parser=None,
        root_id='',
        xml=True,
        id_name='iati-identifier')
    parser.parse()
    assert list(parser.main_sheet) == []
    assert parser.main_sheet.lines == []
    assert parser.sub_sheets == {}


def test_xml_basic_example():
    parser = JSONParser(
        json_filename='examples/iati/expected.xml',
        root_list_path='iati-activity',
        schema_parser=None,
        root_id='',
        xml=True,
        id_name='iati-identifier')
    parser.parse()
    assert list(parser.main_sheet) == ['iati-identifier', 'reporting-org/@ref', 'reporting-org/@type', 'reporting-org/narrative', 'title/narrative', 'description/narrative', 'participating-org/@ref', 'participating-org/@role', 'activity-status/@code', 'activity-date/@iso-date', 'activity-date/@type']
    assert parser.main_sheet.lines == [
        {'activity-date/@type': '1', 'reporting-org/narrative': 'Organisation name', 'participating-org/@ref': 'AA-AAA-123456789', 'title/narrative': 'A title', 'participating-org/@role': '1', 'reporting-org/@ref': 'AA-AAA-123456789', 'iati-identifier': 'AA-AAA-123456789-ABC123', 'reporting-org/@type': '40', 'description/narrative': 'A description', 'activity-date/@iso-date': '2011-10-01', 'activity-status/@code': '2'},
        {'activity-date/@type': '2', 'reporting-org/narrative': 'Organisation name', 'participating-org/@ref': 'AA-AAA-123456789', 'title/narrative': 'Another title', 'participating-org/@role': '1', 'reporting-org/@ref': 'AA-AAA-123456789', 'iati-identifier': 'AA-AAA-123456789-ABC124', 'reporting-org/@type': '40', 'description/narrative': 'Another description', 'activity-date/@iso-date': '2016-01-01', 'activity-status/@code': '3'}
    ]
    assert set(parser.sub_sheets.keys()) == set(['transaction', 'recipient-country'])
    assert list(parser.sub_sheets['transaction']) == ['iati-identifier', 'transaction/0/transaction-type/@code', 'transaction/0/transaction-date/@iso-date', 'transaction/0/value/@value-date', 'transaction/0/value']
    assert parser.sub_sheets['transaction'].lines == [
       {'transaction/0/value/@value-date': '2012-01-01', 'iati-identifier': 'AA-AAA-123456789-ABC123', 'transaction/0/transaction-date/@iso-date': '2012-01-01', 'transaction/0/value': '10', 'transaction/0/transaction-type/@code': '2'},
       {'transaction/0/value/@value-date': '2012-03-03', 'iati-identifier': 'AA-AAA-123456789-ABC123', 'transaction/0/transaction-date/@iso-date': '2012-03-03', 'transaction/0/value': '20', 'transaction/0/transaction-type/@code': '3'},
       {'transaction/0/value/@value-date': '2013-04-04', 'iati-identifier': 'AA-AAA-123456789-ABC124', 'transaction/0/transaction-date/@iso-date': '2013-04-04', 'transaction/0/value': '30', 'transaction/0/transaction-type/@code': '2'},
       {'transaction/0/value/@value-date': '2013-05-05', 'iati-identifier': 'AA-AAA-123456789-ABC124', 'transaction/0/transaction-date/@iso-date': '2013-05-05', 'transaction/0/value': '40', 'transaction/0/transaction-type/@code': '3'}
    ]
    assert list(parser.sub_sheets['recipient-country']) == ['iati-identifier', 'recipient-country/0/@code', 'recipient-country/0/@percentage']
    assert parser.sub_sheets['recipient-country'].lines == [
        {'iati-identifier': 'AA-AAA-123456789-ABC123', 'recipient-country/0/@code': 'AF', 'recipient-country/0/@percentage': '40'},
        {'iati-identifier': 'AA-AAA-123456789-ABC123', 'recipient-country/0/@code': 'XK', 'recipient-country/0/@percentage': '60'},
        {'iati-identifier': 'AA-AAA-123456789-ABC124', 'recipient-country/0/@code': 'AG', 'recipient-country/0/@percentage': '30'},
        {'iati-identifier': 'AA-AAA-123456789-ABC124', 'recipient-country/0/@code': 'XK', 'recipient-country/0/@percentage': '70'}
    ]

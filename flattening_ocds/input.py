from csv import DictReader
import os
import json

def un_flatten_line(line):
    unflattened = {}
    for k,v in line.items():
        if v == '':
            continue
        fields = k.split('.')
        unlattened_sub_dict = unflattened
        for parent_field in fields[:-1]:
            if parent_field not in unlattened_sub_dict:
                unlattened_sub_dict[parent_field] = {}
            unlattened_sub_dict = unlattened_sub_dict[parent_field]
        unlattened_sub_dict[fields[-1]] = v
    return unflattened


def read_csv_dir(folder, main_sheet_name='release'):
    sheets = os.listdir(folder)
    if not main_sheet_name+'.csv' in sheets:
        raise ValueError

    sheets.remove(main_sheet_name+'.csv')

    main_sheet_by_ocid = {}
    with open(os.path.join(folder, main_sheet_name+'.csv')) as main_sheet_file:
        for line in DictReader(main_sheet_file):
            if line['ocid'] in main_sheet_by_ocid:
                raise ValueError('Two lines in main spreadsheet with same ocid')
            main_sheet_by_ocid[line['ocid']] = un_flatten_line(line)

    for sheet_file_name in sheets:
        with open(os.path.join(folder, sheet_file_name)) as sheet_file:
            if not sheet_file_name.endswith('.csv'):
                raise ValueError
            sheet_name = sheet_file_name[:-4]
            for line in DictReader(sheet_file):
                main_sheet_by_ocid[line['ocid']][sheet_name] = un_flatten_line(line)

    print(json.dumps(list(main_sheet_by_ocid.values()), indent=2))

if __name__ == '__main__':
    read_csv_dir('release_input')

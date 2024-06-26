import warnings
import getpass
import os
import csv
import math
from presets import Presets, InvalidUsageError



def secure_input(message: str) -> str:
    password = getpass.getpass(message)
    return password


def deprecated(func):
    def wrapper(*args, **kwargs):
        warnings.warn(f"{func.__name__} is deprecated", category=DeprecationWarning)
        return func(*args, **kwargs)
    return wrapper


def set_environ(token: str) -> None:
    os.environ["REPLICATE_API_TOKEN"] = token


def selection(listing: dict[str, callable]) -> callable:
    print('Please select one of the following')
    for i, key in enumerate(listing):
        print(f'    {i + 1}. {key}')
    selection = input('> ')
    valid, response = _validate(selection, _isnumber=True, _max_size=i + 1, whitelist=list(listing))
    while (not valid):
        print(f"Could not select. ERROR: '{response}'")
        print('Please select one of the following')
        for i, key in enumerate(listing):
            print(f'    {i + 1}. {key}')
        selection = input('> ')
        valid, response = _validate(selection, _isnumber=True, _max_size=i + 1, whitelist=list(listing))
    if type(response) == int:
        return listing[
            list(listing)[response]
        ]
    if type(response) == str:
        return response
    return listing[response]


def _validate(inp: str, _isnumber: bool = False, _max_size: int = -1, whitelist: list = []) -> tuple[bool, str]:
    if inp.lower() in whitelist:
        return True, inp
    if _isnumber:
        try:
            if _max_size >= int(inp):
                return True, int(inp)
            return False, f'{inp} is too large, expected 1 - {_max_size}'
        except ValueError:
            return False, f'"{inp}" is not a member of the list [{",".join(whitelist)}] and cannot be converted to a number'
    return False, f'"{inp}" is not a member of the list [{",".join(whitelist)}]'


def safe_write(action: callable, param: tuple, path: str, display_outcome: bool = True) -> bool:
    try_again: bool = True
    while try_again:
        try:
            action(param[0], param[1])
            return True
        except PermissionError as e:
            print(f"Encountered permission error while triing to write to '{path}'.")
            print("Some process may be using this file... please close the process before trying again.")
            if input("  > try again? (y/n) ") not in ['y', 'yes', 'ye', 'yeah']:
                try_again = False
    if display_outcome: print(f'Failed to update "{path}"!')
    return False


def write_to_file(path: str, string: str, editing_mode: str = 'w') -> None:
    _validate_filepath(path)
    with open(path, editing_mode) as file_out:
        file_out.write(string)


def _validate_filepath(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def get_sheet_values(sheet) -> tuple[str, str]:
    return (sheet['properties']['title'], sheet['properties']['sheetId'])


def to_csv_safe(s: str, remove_newline: bool = True) -> str:
    if remove_newline:
        s = s.replace('\n',' ')
    return s.replace(',', Presets.COMMA_PLACEHOLDER).replace('“', '"').replace('”', '"').replace('’', "'")


def from_csv_safe(s: str) -> str:
    return s.replace(Presets.COMMA_PLACEHOLDER, ',')


def value_to_score(val: int) -> str:
    return f'Score {val}'


def update_adendum(adendum_location: str = 'adendum.gd', rubric_location: str = 'rubric.csv', length: int = 6):
    with open(adendum_location, 'r') as adendum:
        lines = adendum.read().split('\n')
    csv_add: str = '\n'
    for i, line in enumerate(lines):
        csv_add += f'{to_csv_safe(line)},'
        if i % length == length - 1:
            csv_add = csv_add[:-1] + '\n'
    write_to_file(rubric_location, csv_add, editing_mode='a')


def calc_volatility(scores: list[int], min: int, max: int, rounding: int = 2) -> float:
    if not scores:
        return 0
    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std_dev = math.sqrt(variance)
    max_std_dev = (max - min) / 2
    volatility = (std_dev / max_std_dev)
    return round(volatility, rounding)


def classification(Volatility: float) -> str:
    if Volatility < 15:
        return 'Very Consistent'
    if Volatility < 32:
        return 'Consistent'
    if Volatility < 55:
        return 'Somewhat Inconsistent'
    if Volatility < 70:
        return 'Very Inconsistent'
    return 'HIGHLY VOLATILE'


def comma_swap(s: str) -> str:
    """Replaces commas with the presets.Presets.COMMA_PLACEHOLDER string."""
    return s.replace(',', Presets.COMMA_PLACEHOLDER)


def time_formater(secs: float) -> str:
    hours: int = math.floor(secs / 3600)
    secs -= hours * 3600
    minutes: int = math.floor(secs / 60)
    secs -= minutes * 60
    seconds: int = int(secs)
    ms: str = f'{round(secs - seconds, 3)}'[2:]
    ms = ms + '0' * (3 - len(ms))
    h: str = f'{hours}'
    if hours < 10:
        h = '0' + h
    m: str = f'{minutes}'
    if minutes < 10:
        m = '0' + m
    s: str = f'{seconds}'
    if seconds < 10:
        s = '0' + s
    return f'{h}:{m}:{s}.{ms}'


def update_presets(presets_file: str, find: str, replace: str):
    with open(presets_file, 'r') as f:
        lines: list[str] = f.readlines()
    found: bool = False
    for i, line in enumerate(lines):
        if line.startswith(find):
            lines[i] = replace
            found = True
    if found:
        write_to_file(presets_file, ''.join(lines))
        print(f'> Updated Successfully')
    else:
        print(f'> Update Failed')


def id_strip(url: str) -> str:
    id = url.split('/d/', 1)[1]
    return id.split('/', 1)[0]


identity = lambda x: x



class Counter:
    def __init__(self, file: str = 'counter.txt'):
        self.file: str = file
        self.count: int = 0
        if not os.path.exists(self.file) or not os.path.isfile(self.file):
            self._reset()
        else:
            self._pull()
    
    def increment(self, incement_by: int = 1) -> None:
        self.count += incement_by
        self._update()

    def overwrite(self, value: int) -> None:
        self.count = value
        self._update()

    def _reset(self) -> None:
        self.count = 0
        self._update()

    def _pull(self) -> int:
        with open(self.file, 'r') as f:
            self.count = int(f.read())
    
    def _update(self) -> None:
        write_to_file(self.file, f'{self.count}')



class CSVFile:
    @staticmethod
    def reorder(file_name: str, column_number: int, err_msg: bool = False) -> bool:
        max_col: int = 0
        try:
            with open(file_name, 'r') as file:
                reader = csv.reader(file)
                data = list(reader)
                header = data[0]
                body = data[1:]
                max_col = len(header)
                if max_col < column_number or 0 > column_number:
                    raise IndexError()
                body.sort(key=lambda x: x[column_number])
                data = [header] + body
            
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
            return True
        
        except FileNotFoundError:
            if err_msg: print(f"File {file_name} not found.")
            return False
        except IndexError:
            if err_msg: print(f'Column {column_number} not found in file "{file_name}". Min=0, Max={max_col}')
            return False
        except Exception as e:
            if err_msg: print(f"An error occurred: {e}")
            return False
        
    @staticmethod
    def reorder_by_header(file_name: str, header_name: str, err_msg: bool = False) -> bool:
        try:
            with open(file_name, 'r') as file:
                reader = csv.reader(file)
                data: list = list(reader)
                header: str = data[0]
                if header_name not in header:
                    raise Exception(f'Header not found in file "{file_name}". Headers={header}')
                return CSVFile.reorder(file_name, header.index(header_name), err_msg=err_msg)
        except FileNotFoundError:
            if err_msg: print(f"File {file_name} not found.")
            return False
        except Exception as e:
            if err_msg: print(f"An error occurred: {e.__repr__()}")
            return False



if __name__ == '__main__':
    raise InvalidUsageError("This file should not be run. Only import this file and its contents. Do not run this file directly.")

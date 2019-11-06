# -*- coding: utf-8 -*-
# author: Yifan "William" Zhu


import os
import xlsxwriter
import re
from time import process_time
from datetime import datetime
from collections import deque


# Code maintenance and testing decorators

def print_updates(function):
    def wrapper(*args, **kwargs):
        print(function.__name__ + " in progress...")
        method = function(*args)
        print(function.__name__ + " completed.")
        return method

    return wrapper


def print_single_output(function):
    def wrapper(*args, **kwargs):
        print(function.__name__ + " is executed.")
        method = function(*args)
        print(function.__name__ + " returned " + str(method))
        return method

    return wrapper


def print_iterable_output(function):
    def wrapper(*args, **kwargs):
        print(function.__name__ + " is executed.")
        method = function(*args)
        print(function.__name__ + " returned: ")
        for output in method:
            print(str(output))
        return method

    return wrapper


def print_input(function):
    def wrapper(*args, **kwargs):
        method = function(*args)
        print(function.__name__ + " took the following arguments: ")
        for arg in args:
            print(arg)
        return method

    return wrapper


def measure_execution_time(function):
    def wrapper(*args, **kwargs):
        start = process_time()
        method = function(*args)
        end = process_time()
        print(function.__name__ + " completed within " + str(end - start) + "s")
        return method

    return wrapper


def pause_for_error(function):
    def wrapper(*args, **kwargs):
        try:
            method = function(*args)
            return method
        except:
            input("An error occurred")

    return wrapper


# Customized Errors

class Error(Exception):
    """Base class for other exceptions"""
    pass


class EmptyLineError(Error):

    def __str__(self):
        return "You have entered an empty line."
        """Raised when the line consists solely of whitespace."""


class InvalidCommandError(Error):

    def __str__(self):
        return "You have entered an invalid command."
        """Raised when the the first word in the input is not found in existing list of commands """


class InvalidLogCodeError(Error):

    def __str__(self):
        return "You have entered invalid log code(s)."

class MissingElementError(Error):

    def __str__(self):
        return "Command or log code(s) is missing from the input."

class TooManyElementsError(Error):

    def __str__(self):
        return "Too many elements found in the input."



# Extract files
@print_updates
def get_directory_files(path):
    files = {}
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            # Adjust scope of file and potentially include other log types including warnings
            files[file] = os.path.join(r, file)
            # The keys are the file names whereas the values are the files' path
    return files


# User Interface
def print_help():
    options = """Log Type Codes:
    --Error (ERROR)            - e
    --Warning (WARN/WARNING)   - w
    --Debug (DEBUG)            - d
    --Information (INFO)       - i\n\n"""
    commands = """Available commands:
    --include                  - Include the log type(s) corresponding to the inputted codes\n
    --analyze                  - Identify block(s) of one type and trace back a certain number of logs.\n\n """
    main_prompt = """To perform a function on one log type,
    enter the function's command and a space and then the log type's code.
    e.g.  analyze e
    #(identify and  only error block(s) in the logs of the folder)\n\n"""
    multiple_choice = """To perform a function on multiple log types,
    enter their corresponding codes separated by space after the function's command.
    e.g.  include e d
    #(include errors and debugs in your log compilation)\n"""
    print(options + commands + main_prompt + multiple_choice)


def pause_for_help(error):
    print(error())
    input("Press Enter key to return to the menu:\n")
    print_help()


# Parse logs

# Test validation methods here

class Log():

    def __init__(self, line, strip = False):
        self.line = line.strip() if strip else line
        self.time_decimal_place = 3
        self.categories = ["ERROR", "WARN", "DEBUG", "INFO"]
        self.type_method = True

    def switch_min_sec_separator(self, datetime, separator, decimal_place):
        if len(datetime) > decimal_place + 1:
            trailing_digits = datetime[- decimal_place:]
            leading_digits = datetime[: - decimal_place - 1]
            return leading_digits + separator + trailing_digits
        else:
            raise ValueError("Too short for datetime stamp")

    def validate_iso_datetime(self, string, switch_to_period=True):
        if switch_to_period:
            string = self.switch_min_sec_separator(string, ".", self.time_decimal_place)
        try:
            datetime.fromisoformat(string)
            return True
        except ValueError:
            return False

    def validate_timestamp(self):
        datetime_end_index = self.line.find(" ",self.line.find(" ") + 1)  # Find the second index for space
        if datetime_end_index < 0:  # If the index is -1 < 0, the second index is not found and thus no datetime is present
            return False
        else:
            return self.validate_iso_datetime(self.line[:datetime_end_index])

    def validate_type(self, categories = None):
        if categories is None:
            categories = self.categories
        type_start = self.line.find(" ", self.line.find(" ") + 1) + 1  # Find the second index for space, and then move to its right.
        type_end = self.line.find(" ", type_start)  # Find the third index of space from the second index
        if type_end < 0:  # If the index is -1 < 0, the third index of space is not found and thus no log type is present
            return False
        else:
            return self.line[type_start: type_end] in categories

    def validate(self):
        if self.type_method:
            return self.validate_type()
        else:
            return self.validate_timestamp()

    def format(self):  # If needed, set split to True will remove leading and trailing whitespace
        line = self.line.replace(" ", "T", 1)
        entries = re.split(" +", line, 2)
        print(entries)
        entries[0] = entries[0].replace("T", " ")
        return entries


class Text():
    def __init__(self, textfile, files):
        self.text = open(files[textfile], encoding='utf-8')
        self.code_log_dict = {"e": "ERROR", "w": "WARN", "d": "DEBUG", "i": "INFO"}


    def add_block(self, worksheet, block, row, col):
        for line in block:
            log = Log(line)
            if log.validate():
                line_array = log.format()
                for i in range(len(line_array)):
                    worksheet.write(row, col + i, line_array[col+ i])
            else:
                worksheet.write(row, col + 2, line)
            # begin the next line
            row += 1
        return row

    def collect_type(self, worksheet, categories):
        # Begin extracting logs in the 2nd row of the worksheet.
        row = 1
        for line in self.text:
            log = Log(line)
            if log.validate():
                log_array = log.format()
                if log_array[1] in categories:
                    for col in range(len(log_array)):
                        worksheet.write(row, col, log_array[col])
                    # begin the next line
                    row += 1
                else:
                    print(log_array[1])


    def collect_block(self, worksheet, focus_types=["ERROR"], recent_height=10):
        recent = deque([], recent_height)
        focus = deque([])
        row = 1
        col = 0
        block_count = 0
        for line in self.text:
            log = Log(line)
            prev = Log(recent[-1]) if len(recent) > 0 else None
            if log.validate_type(focus_types):
                focus.extend(recent)
                focus.append(line)
            else:
                if prev is not None and prev.validate_type(focus_types):
                    block_count += 1
                    worksheet.write(row, col, "Log Block %d" % block_count)
                    row += 1
                    row = self.add_block(worksheet, focus, row, col) + 1
                    focus.clear()
            recent.append(line)



    def evaluate_text(self, worksheet, command, args):
        print("command", command, "args: ",args)
        if command == "include":
            categories = [self.code_log_dict[arg] for arg in args]
            self.collect_type(worksheet, categories)
        elif command == "analyze":
            categories = [self.code_log_dict[arg] for arg in args[0:-1]]
            print("evaluate", categories)
            recent_height = int(args[-1])
            self.collect_block(worksheet, categories, recent_height)




class MyWorkbook(xlsxwriter.Workbook):

    def __init__(self, name = "Spreadsheet.xlsx"):
        self.myworkbook = xlsxwriter.Workbook(name)
        self.first_row = ["Datetime", "Log Type", "Message"]


    def format_worksheet(self, worksheet):
        # Widen the first column to make the text clearer.
        worksheet.set_column('A:A', 50)
        for i in range(len(self.first_row)):
            worksheet.write(0, i, self.first_row[i])

    def add_formatted_worksheet(self, name):
        worksheet = self.myworkbook.add_worksheet(name)
        print("Worksheet created.")
        self.format_worksheet(worksheet)
        return worksheet

    def export_workbook(self, files, command, args):

        for f in files:
            print(f)
            # Encode logs with UTF-8
            logfile = Text(f, files)
            # Adding new worksheet and naming it after the log file
            worksheet = self.add_formatted_worksheet(f)
            print("Exportation of logs in progress...")
            logfile.evaluate_text(worksheet, command, args)
            print("Exportation of completed.", f)
        self.myworkbook.close()
        return self.myworkbook



class Parse():
    def __init__(self, input):
        self.code_log_dict = {"e": "ERROR", "w": "WARN", "d": "DEBUG", "i": "INFO"}
        self.include_logs = ["ERROR", "WARN", "DEBUG", "INFO"]
        self.analyze_logs = ["ERROR", "WARN", "DEBUG"]
        self.input_arr = input.lower().strip().split()
        self.input_len = len(self.input_arr)
        self.max_len = 6


    def find_length_exception(self):
        if self.input_len == 0:
            raise EmptyLineError
        elif self.input_len == 1:
            raise MissingElementError


    def parse_categories(self, arr):
        output = []
        for code in arr:
            try:
                output.append(code_dict[code])
            except KeyError:
                raise InvalidLogCodeError
        return output


    def find_include_error(self):
        if self.input_len > len(self.include_logs) + 1:
            raise TooManyElementsError

    def find_analyze_error(self):
        if self.input_len < 3:
            raise MissingElementError
        elif self.input_len > len(self.analyze_logs) + 2:
            raise TooManyElementsError

    def pass_output(self, files, workbook_name):
        self.find_length_exception()
        command = self.input_arr[0]
        workbook = MyWorkbook(workbook_name)
        if command == "include":
            self.find_include_error()
        elif command == "analyze":
            self.find_analyze_error()
        else:
            raise InvalidCommandError
        content = self.input_arr[1:]
        workbook.export_workbook(files, command, content)




if __name__ == "__main__":
    path = input("Please enter the folder directory:\n")
    files = get_directory_files(path)
    while True:
        try:
            query = Parse(input("Enter your command:\n"))
            query.pass_output(files, input("Please declare the spreadsheet's name:\n") + ".xlsx")
            break
        except EmptyLineError:
            pause_for_help(EmptyLineError)
        except InvalidCommandError:
            pause_for_help(InvalidCommandError)
        except InvalidLogCodeError:
            pause_for_help(InvalidLogCodeError)

#!/usr/bin/env python

import argparse
import CppHeaderParser
import re
import yaml
import copy

class CppDefine(dict):
    def __init__(self):
        self["name"] = None
        self["parameters"] = []
        self["line_number"] = -1

class CppDefineParameter(dict):
    def __init__(self):
        self["name"] = None
        self["line_number"] = -1

class Application(object):
    def __init__(self):
        description='''A styler just target to naming conventions of source
        code'''

        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("-c", "--config",
            help="Configuration file path (In YAML format)",
            required=True)
        parser.add_argument("-o", "--output", help="Output file path")
        parser.add_argument("file_path", help="Source file path")

        self.__args = parser.parse_args()

        # If user does not specific output path, we default it to input file
        # path
        if self.__args.output is None:
            self.__args.output = self.__args.file_path

        self.__config = yaml.load(open(self.__args.config))

    def parse_define(self, adefine):
        matched = re.match(r"[^\w]*(\w+)(?:\((.*)\)|\s).*", adefine)
        name = matched.group(1)
        parameters = []
        if matched.group(2) is not None:
            parameter_names = matched.group(2).split(',')
            for parameter_name in parameter_names:
                aparameter = CppDefineParameter()
                aparameter["name"] = parameter_name.strip()
                parameters.append(aparameter)

        result = CppDefine()
        result["name"] = name
        result["parameters"] = parameters
        return result

    def _get_config(self, name):
        override_table = {
                "function_argument": "argument",
                "class_method_argument": "function_argument",
                "struct_method_argument": "function_argument",
                "define_function_argument": "function_argument",
                "define_function": "function",
                "class_method": "function",
                "struct_method": "function",
                "class_variant": "variant",
                "struct_variant": "variant",
            }

        my_config = dict()

        if name in override_table:
            base_name = override_table[name]
            my_config = copy.deepcopy(self._get_config(base_name))

        if name in self.__config:
            my_config.update(self.__config[name])

        return my_config

    def _validate_name(self, cpp_object, re_name):
        matched = re.match(self._get_config(re_name)["re"], cpp_object["name"])
        if matched:
            raise SyntaxError()

    def exec_(self):
        parsed_info = CppHeaderParser.CppHeader(self.__args.file_path)

        # Verify Define Names
        for define_text in parsed_info.defines:
            cpp_object = self.parse_define(define_text)

            if len(cpp_object["parameters"]) <= 0:
                # Normal Define Name
                self._validate_name(cpp_object, "define")
            else:
                # Function Liked Define Name
                self._validate_name(cpp_object, "define_function")

        # Verify Class Names
        for cpp_object in parsed_info.classes:
            self._validate_name(cpp_object, "class")

            for amethod in aclass.get_all_methods():
                self._validate_name(amethod, "class_method")

        for cpp_object in parsed_info.classes:
            self._validate_name(cpp_object, "class")

            for amethod in aclass.get_all_methods():
                self._validate_name(cpp_object, "class_method")

def main():
    a = Application()
    a.exec_()

if __name__ == "__main__":
    # Execute only if run as a script
    main()

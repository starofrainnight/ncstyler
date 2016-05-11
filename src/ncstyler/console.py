#!/usr/bin/env python

import argparse
import CppHeaderParser
import re
import yaml

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
                "function_argument_name": "argument_name",
                "class_function_argument_name": "function_argument_name",
                "struct_function_argument_name": "function_argument_name",
                "define_function_argument_name": "function_argument_name",
                "define_function_name": "function_name",
                "class_function_name": "function_name",
                "struct_function_name": "function_name",
                "class_variant_name": "variant_name",
                "struct_variant_name": "variant_name",
            }

        my_config = dict()
        if name in self.__config:
            my_config = self.__config[name]

        overrided_config = my_config
        if name in override_table:
            base_name = override_table[name]
            overrided_config = self._get_config(base_name).update(my_config)

        return overrided_config

    def exec_(self):
        parsed_info = CppHeaderParser.CppHeader(self.__args.file_path)
        defines = []
        for define_text in parsed_info.defines:
            adefine = self.parse_define(define_text)
            defines.append(adefine)

def main():
    a = Application()
    a.exec_()

if __name__ == "__main__":
    # Execute only if run as a script
    main()
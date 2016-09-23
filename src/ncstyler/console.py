#!/usr/bin/env python

import argparse
import CppHeaderParser
import re
import sys
import yaml
import copy
import six
import os.path
import traceback

class CppDefine(dict):
    def __init__(self):
        self["name"] = None
        self["parameters"] = []
        self["line_number"] = -1

class CppDefineParameter(dict):
    def __init__(self):
        self["name"] = None
        self["line_number"] = -1

class CppNamespace(dict):
    def __init__(self):
        self["name"] = None
        self["line_number"] = -1

class CppFileName(dict):
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
        parser.add_argument("-d", "--debug", action='store_true', help="Print trace stack")
        parser.add_argument("file_path", help="Source file path")

        self.__args = parser.parse_args()

        # If user does not specific output path, we default it to input file
        # path
        if self.__args.output is None:
            self.__args.output = self.__args.file_path

        self.__config = yaml.load(open(self.__args.config))
        old_base = self.__config["_base_"]
        self.__config["_base_"] = {
            "re":"[a-zA-Z0-9_]+",
            "error": "",
            }
        self.__config["_base_"].update(old_base)

    def parse_define(self, adefine):
        matched = re.match(r"[^\w]*(\w+)(?:\(([^\)]*)\)|\s*).*", adefine)
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

    def _is_special_method(self, amethod):
        if isinstance(amethod, six.string_types):
            amethod_name = amethod
        else:
            amethod_name = amethod["name"]

        founded = re.findall(r"(?:^|[^\w]+)operator[^\w]+", amethod_name)
        if len(founded) <= 0:
            if re.match(r"(?:^|.*\W)operator\W.*", amethod["debug"]) is not None:
                return True

            return False

        return True

    def _get_argument_name(self, an_argument):
        if isinstance(an_argument, six.string_types):
            return an_argument

        if len(an_argument["name"]) > 0:
            return an_argument["name"]

        # If it's a functor?? with "class name::function" style
        matched = re.match(r"^\w+\s*\(\w*::\*(\w+)\)\(.*$", an_argument["type"])
        if matched is None:
            # with normal "function" style
            matched = re.match(r"[^\(]*\([^\)]*\W(\w+)\W.*\).*", an_argument["type"])

        if matched is None:
            return ""
        else:
            return matched.group(1)

    def _get_config(self, name):
        override_table = {
                "class": "_base_",
                "function": "_base_",
                "variant": "_base_",
                "namespace": "_base_",
                "define": "_base_",
                "filename": "_base_", # Special config use to define filename rule

                "argument": "variant",
                "static_variant": "variant",
                "global_variant": "variant",
                "function_argument": "argument",
                "class_method_argument": "function_argument",
                "struct_method_argument": "class_method_argument",
                "define_function_argument": "function_argument",
                "define_function": "function",
                "class_method": "function",
                "struct_method": "class_method",
                "class_variant": "variant",
                "struct_variant": "class_variant",
                "typedef": "class",
                "struct": "class",
                "enum": "class",
                "enum_value": "define",
                "union": "struct",
            }

        my_config = dict()

        if name in override_table:
            base_name = override_table[name]
            my_config.update(self._get_config(base_name))

        if name in self.__config:
            my_config.update(self.__config[name])

        return my_config

    def _is_valid_variable(self, cpp_variable):
        if cpp_variable["type"] == "return":
            return False

        if len(cpp_variable["type"]) <= 0:
            return False

        return True

    def _get_cpp_method_re(self, name):
        prefix = "operator"
        if not name.startswith(prefix):
            return re.escape(name)

        # Operator methods
        chars = []
        for achar in name[len(prefix):]:
            chars.append("\\s*")
            if achar.isalnum():
                chars.append(achar)
            else:
                chars.append("\\")
                chars.append(achar)

        return "operator%s" % ''.join(chars)

    def _validate_codes_of_cpp_method(self, cpp_method):
        start_line_index = cpp_method["line_number"] - 1
        # Extract cpp method codes
        rest_lines = self._source_lines[start_line_index:]
        content = '\n'.join(rest_lines)
        code_lines = []
        name_re = self._get_cpp_method_re(cpp_method["name"])
        name_start_pos = re.search(name_re, content).span()[0]

        parameters_start_pos = content.index('(', name_start_pos)
        parameters_stop_pos = content.index(')', parameters_start_pos)

        stack = []

        try:
            i = content.index('{', parameters_stop_pos + 1)
        except ValueError:
            return;

        try:
            semicolonPos = content.index(';', parameters_stop_pos + 1)
            if semicolonPos <= i:
                return;
        except ValueError:
            # Not found a semicolon, just ignored.
            pass

        skipped_lines = cpp_method["line_number"] + content.count("\n", 0, i) - 2

        stack.append(i)
        i += 1
        first_i = i
        last_i = 0
        is_finding_block_comment = False
        is_finding_single_comment = False
        while (len(stack) > 0) and (i < len(content)):
            c = content[i]

            if is_finding_block_comment:
                # If finding block comment, then skip all other searching
                if (c == "*") and (content[i + 1] == "/"):
                    is_finding_block_comment = False
            elif (c == "/") and (content[i + 1] == "*"):
                is_finding_block_comment = True
            elif is_finding_single_comment:
                # If finding single comment, then skip all other searching
                if c == "\n":
                    is_finding_single_comment = False
            elif (c == "/") and (content[i + 1] == "/"):
                is_finding_single_comment = True
            elif c == "{":
                stack.append(i)
            elif c == "}":
                last_i = i
                del stack[len(stack) - 1]

            i += 1

        if len(stack) <= 0:
            content = content[first_i:last_i]
            founded = re.findall(r"\w+\W+(\w+)\s*=[^=]", content)
            for aname in founded:
                avariant = dict()
                avariant["name"] = aname
                avariant["line_number"] = cpp_method["line_number"]
                self._validate_name(avariant, "variant")

    def _validate_name(self, cpp_object, name_re):
        cpp_object_name = ""
        if isinstance(cpp_object, six.string_types):
            cpp_object_name = cpp_object
            cpp_object = dict()
            cpp_object["name"] = cpp_object_name
            cpp_object["line_number"] = -1
        else:
            cpp_object_name = cpp_object["name"]
            if ('<' in cpp_object_name) and ("debug" in cpp_object):
                matched = re.match(".*?(\w+)\W+$", cpp_object["debug"])
                if matched is not None:
                    cpp_object_name = matched.group(1)

        # Parse union like names
        splitted = cpp_object_name.split()
        if len(splitted) > 1:
            cpp_object_name = splitted[-1]

        if len(cpp_object_name) <= 0:
            # Does not have valid name, we must not check it .
            return


        matched = re.match(self._get_config(name_re)["re"], cpp_object_name)
        if matched is None:
            filename = os.path.basename(self.__args.file_path)
            error_message = self._get_config(name_re)["error"]
            if len(error_message) > 0:
                error_message = "%s %s" % (
                    ' '.join([rule_name.capitalize() for rule_name in name_re.split("_")]),
                    error_message)

            if self.__args.debug:
                traceback.print_stack()

            raise SyntaxError("%s:%s:error: Name '%s' isn't matched with rule : %s! %s" % (
                filename,
                cpp_object["line_number"],
                cpp_object_name,
                name_re,
                error_message))

    def _get_class_realname(self, class_name):
        return re.match("(\w+).*", class_name).group(1)

    def _validate_cpp_object(self, cpp_object):
        cpp_object_type = type(cpp_object)

        if cpp_object_type == CppDefine:
            if len(cpp_object["parameters"]) <= 0:
                # Normal Define Name
                self._validate_name(cpp_object, "define")
            else:
                # Function Liked Define Name
                self._validate_name(cpp_object, "define_function")
                for aparameter in cpp_object["parameters"]:
                    self._validate_name(aparameter, "define_function_argument")
        elif cpp_object_type == CppHeaderParser.CppClass:
            if "struct" in cpp_object["declaration_method"]:
                class_re = "struct"
                class_method_re = "struct_method"
                class_method_argument_re = "struct_method_argument"
                class_variant_re = "struct_variant"
            else:
                class_re = "class"
                class_method_re = "class_method"
                class_method_argument_re = "class_method_argument"
                class_variant_re = "class_variant"
            self._validate_name(cpp_object, class_re)

            for amethod in cpp_object.get_all_methods():
                matched = re.match(r".*typedef\W[^\(]*\([^\)]*\W(\w+)\W.*\).*", amethod["debug"])
                if matched is None:
                    self._validate_codes_of_cpp_method(amethod)
                    if not self._is_special_method(amethod):
                        if amethod["name"] != self._get_class_realname(cpp_object["name"]):
                            try:
                                self._validate_name(amethod, class_method_re)
                            except SyntaxError:
                                is_need_reraise = True
                                try:
                                    self._validate_name(amethod, "define_function")
                                    is_need_reraise = False
                                except SyntaxError:
                                    pass

                                if is_need_reraise:
                                    raise

                    for aparameter in amethod["parameters"]:
                        an_object = dict()
                        an_object["line_number"] = aparameter["line_number"]
                        if (aparameter["type"].endswith("::*")
                            and (")" in aparameter["name"])):
                            an_object["name"] = re.match(r"(\w+).*", aparameter["name"]).group(1)
                            try:
                                self._validate_name(an_object,
                                                    class_method_re)
                            except SyntaxError:
                                is_need_reraise = True
                                try:
                                    self._validate_name(amethod, "define_function")
                                    is_need_reraise = False
                                except SyntaxError:
                                    pass

                                if is_need_reraise:
                                    raise
                        else:
                            an_object["name"] = self._get_argument_name(aparameter)
                            self._validate_name(an_object,
                                                class_method_argument_re)
                else:
                    self._validate_name(
                        {"name":matched.group(1), "line_number":amethod["line_number"]},
                        "typedef")

            for access_specifier in CppHeaderParser.supportedAccessSpecifier:
                for amember in cpp_object["properties"][access_specifier]:
                    if amember["static"]:
                        self._validate_name(amember, "static_variant")
                    else:
                        self._validate_name(amember, class_variant_re)

                for amember in cpp_object["structs"][access_specifier]:
                    self._validate_cpp_object(amember)

                for amember in cpp_object["enums"][access_specifier]:
                    self._validate_cpp_object(amember)

        elif cpp_object_type == CppHeaderParser.CppStruct:
            self._validate_name(cpp_object, "struct")

        elif cpp_object_type == CppHeaderParser.CppEnum:
            self._validate_name(cpp_object, "enum")

            for amember in cpp_object["values"]:
                self._validate_name(amember, "enum_value")

        elif cpp_object_type == CppHeaderParser.CppVariable:
            if cpp_object["type"] != "return":
                if cpp_object["static"]:
                    self._validate_name(cpp_object, "static_variant")
                elif cpp_object["type"] not in ["class", "struct", "union"]:
                    self._validate_name(cpp_object, "global_variant")

        elif cpp_object_type == CppHeaderParser.CppMethod:
            # Exclude "main" function while parsing global function
            while True:
                self._validate_codes_of_cpp_method(cpp_object)
                if cpp_object["name"] == "main":
                    break

                if self._is_special_method(cpp_object):
                    break

                if (cpp_object["class"] is None) or (len(cpp_object["class"]) <= 0):
                    if ">" in cpp_object["name"]:
                        regex = r"^[^<:]*?(?:(\w+)::)?(\w+)\s*<"
                        matched = re.search(regex, cpp_object["debug"])
                        if matched.group(1) is not None:
                            cpp_object["class"] = matched.group(1)

                        cpp_object["name"] = matched.group(2)
                        self._validate_name(cpp_object, "class_method")
                    elif len(cpp_object["returns"]) > 0:
                        # If a function does not have return value(at least
                        # "void"), it maybe macro invokes.

                        # FIXME: We just ignored this situation:
                        # Code Snippets: static RSignal<void(int)> sReceived;
                        if "<" not in cpp_object["name"]:
                            self._validate_name(cpp_object, "function")

                    break

                if self._get_class_realname(cpp_object["class"]) == cpp_object["name"]:
                    # Constructor / Destructor will the same with class name
                    break

                self._validate_name(cpp_object, "class_method")
                break

        elif cpp_object_type == CppHeaderParser.CppUnion:
            self._validate_name(cpp_object, "union")

        elif cpp_object_type == CppNamespace:
            self._validate_name(cpp_object, "namespace")

        elif cpp_object_type == CppFileName:
            self._validate_name(cpp_object, "filename")

    def exec_(self):
        try:

            with open(self.__args.file_path, "r") as source_file:
                # For later parse by _validate_codes_of_cpp_method()
                self._source_lines = source_file.readlines()

            parsed_info = CppHeaderParser.CppHeader(self.__args.file_path)

            # Verify File Names
            filename = os.path.basename(self.__args.file_path)
            cpp_object = CppFileName()
            cpp_object["name"] = filename
            self._validate_cpp_object(cpp_object)

            # Verify Define Names
            for define_text in parsed_info.defines:
                self._validate_cpp_object(self.parse_define(define_text))

            # Verify Function Names
            for cpp_object in parsed_info.functions:
                self._validate_cpp_object(cpp_object)

            # Verify Class Names
            for cpp_object in parsed_info.classes_order:
                self._validate_cpp_object(cpp_object)

            # Verify Struct Names
            for cpp_object in parsed_info.structs_order:
                self._validate_cpp_object(cpp_object)

            # Verify Enum Names
            for cpp_object in parsed_info.enums:
                self._validate_cpp_object(cpp_object)

            # Verify Variable Names
            for cpp_object in parsed_info.variables:
                self._validate_cpp_object(cpp_object)

            for namespace in parsed_info.namespaces:
                cpp_object = CppNamespace()
                cpp_object["name"] = namespace
                self._validate_cpp_object(cpp_object)

            # Verify Typdef Names
            for cpp_object in parsed_info.typedefs:
                self._validate_cpp_object(cpp_object)
        except SyntaxError as e:
            print(str(e))
            return 1

        return 0

def main():
    a = Application()
    sys.exit(a.exec_())

if __name__ == "__main__":
    # Execute only if run as a script
    main()

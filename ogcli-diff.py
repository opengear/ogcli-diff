import argparse
import difflib

class ConfigEntry:
    def __init__(self):
        self.ogcliCmd = ""
        self.comments = []
        self.section = []
        
    def has_content(self):
        return len(self.section) > 0

    def __eq__(self, other):
        return self.ogcliCmd == other.ogcliCmd and self.comments == other.comments and self.section == other.section

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        result = ""
        for comment in self.comments:
            result += comment + "\n"
        result += self.ogcliCmd + "\n"
        for entry in self.section:
            if "END" in entry:
                result += entry + " " + "\n"
            else:
                result += "  " + entry + " " + "\n"
        result += "\n\n"
        return result

    def push_back(self, line):
        self.section.append(line)

    def print_section(self):
        print(self)

    def set_ogcli_cmd(self, command):
        self.ogcliCmd = command

    def set_comment(self, comment):
        self.comments.append(comment)


def parse_config_line_array(lines_from_file):
    sections = []
    in_section = False
    section = ConfigEntry()

    for line in lines_from_file:
        if line.startswith('#'):
            if not in_section:
                section.set_comment(line)
            else:
                in_section = False
                if section.has_content():
                    sections.append(section)
                section = ConfigEntry()

        if in_section:
            if line:
                section.push_back(line)

        if "ogcli" in line:
            if not in_section:
                in_section = True
                section.set_ogcli_cmd(line)
                if len(line) >= 5 and line[-5:] != "'END'":
                    in_section = False
                    sections.append(section)
                    section = ConfigEntry()
            else:
                in_section = False
                if section.has_content():
                    sections.append(section)
                section = ConfigEntry()

        if line.startswith("END"):
            in_section = False
            if section.has_content():
                sections.append(section)
            section = ConfigEntry()

    if section.has_content():
        sections.append(section)

    return sections


def read_lines_from_file(filename):
    lines_from_file = []
    with open(filename, 'r') as file:
        for line in file:
            lines_from_file.append(line.rstrip())
    return lines_from_file


def generate_diff(map1, map2, file1_name, file2_name):
    diffs = []

    for key, section1 in map1.items():
        if key in map2:
            section2 = map2[key]
            if section1 != section2:
                section1_lines = [section1.ogcliCmd] + section1.comments + section1.section
                section2_lines = [section2.ogcliCmd] + section2.comments + section2.section
                diff = difflib.unified_diff(
                    section2_lines,
                    section1_lines,
                    fromfile=file2_name,
                    tofile=file1_name,
                    lineterm=''
                )
                diffs.extend(diff)

    for key in map2:
        if key not in map1:
            section2 = map2[key]
            section2_lines = [section2.ogcliCmd] + section2.comments + section2.section
            diff = difflib.unified_diff(
                [],
                section2_lines,
                fromfile=file2_name,
                tofile=file1_name,
                lineterm=''
            )
            diffs.extend(diff)

    for key in map1:
        if key not in map2:
            section1 = map1[key]
            section1_lines = [section1.ogcliCmd] + section1.comments + section1.section
            diff = difflib.unified_diff(
                section1_lines,
                [],
                fromfile=file2_name,
                tofile=file1_name,
                lineterm=''
            )
            diffs.extend(diff)

    filtered_diffs = []
    skip = False
    for line in diffs:
        if line.startswith('@@'):
            skip = True
            continue
        if skip and (line.startswith('-') or line.startswith('+') or line.startswith(' ')):
            filtered_diffs.append(line)
        else:
            skip = False

    print('\n'.join(filtered_diffs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare two ogcli configuration files.')

    parser.add_argument('config1', metavar='config1.txt', type=str, help='path to the first configuration file')
    parser.add_argument('config2', metavar='config2.txt', type=str, help='path to the second configuration file')

    args = parser.parse_args()

    lines_from_file1 = read_lines_from_file(args.config1)
    lines_from_file2 = read_lines_from_file(args.config2)

    file1_sections = parse_config_line_array(lines_from_file1)
    file2_sections = parse_config_line_array(lines_from_file2)

    file1_dictionary = {section.ogcliCmd: section for section in file1_sections}
    file2_dictionary = {section.ogcliCmd: section for section in file2_sections}

    # Generate diff
    generate_diff(file1_dictionary, file2_dictionary, args.config1, args.config2)

import glob
import os.path


class Link:
    LINK = 1
    HARDLINK = 2
    NETLINK = 3

    def __init__(self, type, link):
        self.type = type
        self.link = link

    def __str__(self):
        type = 'link'
        if self.type == Link.HARDLINK:
            type = 'hardlink'
        if self.type == Link.NETLINK:
            type = 'netlink'
        return f'{type}: "{self.link}"'

    @staticmethod
    def make_link(link):
        return Link(Link.LINK, link)

    @staticmethod
    def make_hardlink(link):
        return Link(Link.HARDLINK, link)

    @staticmethod
    def make_netlink(link):
        return Link(Link.NETLINK, link)


class Note:
    def __init__(self, name: str):
        self.name = name.strip()
        self.links = []
        self.write_issues = []

    def add_link(self, link):
        self.links.append(link)

    def add_write_issue(self, issue):
        self.write_issues.append(issue)


def check_instruction(instruction, line):
    start = f'({instruction} '
    if line.startswith(start) and line.endswith(')') and line != start + ')':
        return line[len(start):-1]
    return None


class NoteThread:
    def __init__(self, path: str, name: str, group_path: list):
        self.path = path
        self.name = name.strip()
        self.group_path = group_path
        self.notes = []

    def __str__(self):
        return f'{{{self.name} in {"/".join(self.group_path)} notes {len(self.notes)}}}'

    @staticmethod
    def get(filepath):
        if not os.path.isfile(filepath) or not filepath.endswith('.md'):
            return None
        dir, filename = os.path.split(filepath)
        name = filename[:-3]
        groups = []
        while dir:
            dir, group = os.path.split(dir)
            groups.append(group)
        groups.reverse()
        thread = NoteThread(path=filepath, name=name, group_path=groups)

        note = None
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    continue
                if line.startswith('## ') and note is not None:
                    thread.notes.append(note)
                if line.startswith('## '):
                    note = Note(line[3:])
                if note is None:
                    continue

                link = check_instruction('link', line)
                if link:
                    note.add_link(Link.make_link(link))
                hardlink = check_instruction('hardlink', line)
                if hardlink:
                    note.add_link(Link.make_hardlink(hardlink))
                netlink = check_instruction('netlink', line)
                if netlink:
                    note.add_link(Link.make_netlink(netlink))
                write = check_instruction('write', line)
                if write:
                    note.add_write_issue(write)

        if note is not None:
            thread.notes.append(note)
        return thread

    def print_links(self):
        for note in self.notes:
            print(note.name)
            for link in note.links:
                print(' *', link)


class GlossaryItem:
    def __init__(self, name):
        self.references = 0
        self.name = name


class Glossary:
    def __init__(self):
        self.topics = dict()

    def add_topic(self, name):
        if name in self.topics:
            print(f'topic ambiguos {name}')
        else:
            self.topics[name] = []

        item = GlossaryItem(name)
        self.topics[name].append(item)

    def init(self):
        for file in glob.glob('glossary/**/*.md', recursive=True):
            note_thread = NoteThread.get(file)
            self.add_topic(note_thread.name)
            for note in note_thread.notes:
                self.add_topic(note.name)


class NoteManager:
    def __init__(self):
        self.dictionary = dict()

    def add_note(self, path, note):
        self.dictionary[os.path.join(path, note.name)] = note
    
    def add_note_thread(self, note_thread):
        self.dictionary[note_thread.path] = note_thread
        for note in note_thread.notes:
            self.add_note(note_thread.path, note)


if __name__ == '__main__':
    glossary = Glossary()
    glossary.init()
    missed_links = []
    write_issues = []
    note_manager = NoteManager()

    note_threads = [NoteThread.get(file) for file in glob.glob('**/*.md', recursive=True)]
    for note_thread in note_threads:
        note_manager.add_note_thread(note_thread)

    for note_thread in note_threads:
        for note in note_thread.notes:
            for link in note.links:
                if link.type == Link.NETLINK:
                    continue
                if link.type == Link.HARDLINK:
                    if link.link not in note_manager.dictionary:
                        missed_links.append(link)
                elif link.link not in glossary.topics:
                    missed_links.append(link)
            for write_issue in note.write_issues:
                if ' ' in write_issue:
                    write_issue = f'"{write_issue}"' 
                write_issues.append('/'.join((*note_thread.group_path, note_thread.name, note.name, write_issue)))
        
    if missed_links:
        print(f'Found {len(missed_links)} missed links')
        for link in missed_links:
            print(' *', link)
    if glossary.topics:
        print(f'Found {len(glossary.topics)} topics')
        for topic in glossary.topics.keys():
            print(' *', topic)
    if write_issues:
        print(f'Fount {len(write_issues)} write issues')
        for issue in write_issues:
            print(' *', issue)

        
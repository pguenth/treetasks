import xml.etree.ElementTree as ET
import json
import logging
from datetime import date
from .task import Task, TaskState
from .tree import TaskTree

def convert_parser(path_in, path_out, parser_in, parser_out):
    tree = TaskTree(path_in, None, parser_in)
    tree.path = path_out
    tree.parser = parser_out
    tree.save()

class TaskTreeParserXML:
    @staticmethod
    def _parse_recursive(elem, parent):
        if not elem.tag == 'todo':
            raise ValueError("No Todo given")

        # find title and create tree node
        title_element = elem.find('title')
        if title_element is None:
            raise ValueError("Given Todo has no title")

        title = title_element.text
        node = Task(title, parent)

        # parse attributes
        if 'collapse' in elem.attrib:
            node.collapsed = True if elem.attrib['collapse'] == "yes" else False

        if 'done' in elem.attrib and elem.attrib['done'] == "yes":
            node.state = TaskState.DONE

        if 'cancelled' in elem.attrib and elem.attrib['cancelled'] == "yes":
            node.state = TaskState.CANCELLED

        # parse children
        for child in elem:
            if child.tag == "text":
                if child.text is None:
                    node.text = ""
                else:
                    node.text = child.text

            elif child.tag == "category":
                node.add_category(child.text)

            elif child.tag == "todo":
                TaskTreeParserXML._parse_recursive(child, node)

            elif child.tag == "deadline":
                node.due = date(int(child.find("year").text), int(child.find("month").text), int(child.find("day").text))

            elif child.tag == "scheduled":
                node.scheduled = date(int(child.find("year").text), int(child.find("month").text), int(child.find("day").text))

            elif child.tag == "priority":
                node.priority = int(child.text)

        return node

    @staticmethod
    def _encode_recursive(task, this_element):
        this_element.set('collapse', 'yes' if task.collapsed else 'no')
        if task.state == TaskState.DONE:
            this_element.set('done', 'yes')
            this_element.set('cancelled', 'no')
        elif task.state == TaskState.CANCELLED:
            this_element.set('done', 'no')
            this_element.set('cancelled', 'yes')
        elif task.state == TaskState.PENDING:
            this_element.set('done', 'no')
            this_element.set('cancelled', 'no')

        ET.SubElement(this_element, 'title').text = task.title
        ET.SubElement(this_element, 'text').text = task.text
        
        for cat in task.categories:
            ET.SubElement(this_element, 'category').text = cat

        for child in task.children:
            c_elem = ET.SubElement(this_element, 'todo')
            TaskTreeParserXML._encode_recursive(child, c_elem)

        if not task.due is None:
            deadline_elem = ET.SubElement(this_element, 'deadline')
            ET.SubElement(deadline_elem, 'day').text = str(task.due.day)
            ET.SubElement(deadline_elem, 'month').text = str(task.due.month)
            ET.SubElement(deadline_elem, 'year').text = str(task.due.year)

        if not task.scheduled is None:
            schedule_elem = ET.SubElement(this_element, 'scheduled')
            ET.SubElement(schedule_elem, 'day').text = str(task.scheduled.day)
            ET.SubElement(schedule_elem, 'month').text = str(task.scheduled.month)
            ET.SubElement(schedule_elem, 'year').text = str(task.scheduled.year)
            ET.SubElement(schedule_elem, 'position').text = str(1) # dont know what this tag means for tudu

        if not task.priority is None:
            ET.SubElement(this_element, 'priority').text = str(task.priority)

        return this_element

    @staticmethod
    def _get_hidden_categories(filter_node, tasktree):
        showonly = []
        hidden = []

        for child in filter_node:
            if child.tag == 'showonly':
                showonly.append(child.text)
            elif child.tag == 'hidden':
                hidden.append(child.text)

        tasktree.show_only_categories = showonly
        tasktree.hidden_categories = hidden

    @staticmethod
    def _write_hidden_categories(filter_node, tasktree):
        for h in tasktree.hidden_categories:
            ET.SubElement(filter_node, 'hidden').text = h

        for c in tasktree.show_only_categories:
            ET.SubElement(filter_node, 'showonly').text = c
        

    @staticmethod
    def load(path, tasktree):
        tree = ET.parse(path)
        root = tree.getroot()

        for child in root:
            if child.tag == "filter":
                TaskTreeParserXML._get_hidden_categories(child, tasktree)
            else:
                TaskTreeParserXML._parse_recursive(child, tasktree.root)

    @staticmethod
    def save(path, tasktree):
        root = ET.Element('todo')
        for child in tasktree.root.children:
            c_elem = ET.SubElement(root, 'todo')
            TaskTreeParserXML._encode_recursive(child, c_elem)

        filter_node = ET.SubElement(root, 'filter')
        TaskTreeParserXML._write_hidden_categories(filter_node, tasktree)


        with open(path, mode='w') as f:
            f.write(ET.tostring(root, encoding='unicode'))

class TaskTreeParserJSON:
    @staticmethod
    def _task_to_dict(task):
        tdict = {
            'title' : task.title,
            'text' : task.text,
            'priority' : task.priority,
            'collapsed' : task.collapsed,
            'categories' : list(task.categories),
            'due' : task.due,
            'scheduled' : task.scheduled
        }

        if not task.due is None:
            tdict['due'] = task.due.isoformat()

        if not task.scheduled is None:
            tdict['scheduled'] = task.scheduled.isoformat()

        if task.state is TaskState.PENDING:
            tdict['state'] = 'pending'
        elif task.state is TaskState.DONE:
            tdict['state'] = 'done'
        elif task.state is TaskState.CANCELLED:
            tdict['state'] = 'cancelled'

        tdict['children'] = []
        for c in task.children:
            tdict['children'].append(TaskTreeParserJSON._task_to_dict(c))

        return tdict

    @staticmethod
    def _task_from_dict(tdict, parent_task):
        task = Task(tdict['title'], parent=parent_task)
        task.text = tdict['text']
        task.priority = tdict['priority']
        task.collapsed = tdict['collapsed']

        for cat in tdict['categories']:
            task.add_category(cat)

        if tdict['due'] is None:
            task.due = None
        else:
            task.due = date.fromisoformat(tdict['due'])

        if tdict['scheduled'] is None:
            task.scheduled = None
        else:
            task.scheduled = date.fromisoformat(tdict['scheduled'])

        if tdict['state'] == 'pending':
            task.state = TaskState.PENDING
        elif tdict['state'] == 'done':
            task.state = TaskState.DONE
        elif tdict['state'] == 'cancelled':
            task.state = TaskState.CANCELLED

        for c in tdict['children']:
            TaskTreeParserJSON._task_from_dict(c, task)

        return task

    @staticmethod 
    def load(path, tasktree):
        with open(path, mode="r") as f:
            jsondata = json.load(f)

        if 'show_only_categories' in jsondata['filter']:
            tasktree.show_only_categories = jsondata['filter']['show_only_categories']

        if 'hidden_categories' in jsondata['filter']:
            tasktree.hidden_categories = jsondata['filter']['hidden_categories']

        for c in jsondata['tasks']:
            TaskTreeParserJSON._task_from_dict(c, tasktree.root)

    @staticmethod
    def save(path, tasktree):
        tdicts = []
        for c in tasktree.root.children:
            tdicts.append(TaskTreeParserJSON._task_to_dict(c))

        jsondata = {
                'tasks' : tdicts,
                'filter' : {
                    'show_only_categories' : list(tasktree.show_only_categories),
                    'hidden_categories' : list(tasktree.hidden_categories)
                    }
                }

        with open(path, mode="w") as f:
            json.dump(jsondata, f)


class TaskTreeParserAuto:
    @staticmethod
    def _choose_parser(path):
        if path[-3:] == "xml":
            return TaskTreeParserXML
        elif path[-4:] == "json":
            return TaskTreeParserJSON

    @staticmethod
    def load(path, tasktree):
        return TaskTreeParserAuto._choose_parser(path).load(path, tasktree)

    @staticmethod
    def save(path, tasktree):
        return TaskTreeParserAuto._choose_parser(path).save(path, tasktree)

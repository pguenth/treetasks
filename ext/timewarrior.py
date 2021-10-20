import subprocess
from subprocess import PIPE, STDOUT
from anytree import AnyNode
import json
from datetime import timedelta, datetime, timezone

def get_tags_categories(task):
    tags = [task.title]
    cats = set()
    for c in task.categories:
        cats.add(c)

    return tags, cats

def get_tags(task, parents_as_tags=True):
    tags, cats = get_tags_categories(task)

    if parents_as_tags:
        p = task.parent
        while not isinstance(p, AnyNode):
            t, c = get_tags_categories(p)
            tags += t
            cats |= c
            p = p.parent

    return tags + list(cats)

def _start_or_stop_task(task, start=True, parents_as_tags=True):
    start_or_stop = 'start' if start else 'stop'
    cp = subprocess.run(['timew', start_or_stop] + get_tags(task, parents_as_tags) + [':yes', ':quiet'], check=False, stdout=PIPE, stderr=STDOUT)
    return cp.stdout.decode("utf-8")

def start_task(task, parents_as_tags=True):
    _start_or_stop_task(task, True, parents_as_tags)

# stops whatever is running. doing otherwise easily leads to inconsitencies
def stop():
    cp = subprocess.run('timew stop :quiet'.split(), check=False, stdout=PIPE, stderr=STDOUT)
    return cp.stdout.decode("utf-8")


def get_events(task, parents_as_tags=True, with_children=False):
    tags = get_tags(task, parents_as_tags)
    exported = subprocess.check_output('timew export from 2000-01-01 to now :quiet'.split() + tags)
    info = json.loads(exported.decode('utf-8'))
    exp = []
    for event in info:
        if sorted(event['tags']) == sorted(tags) or with_children:
            exp.append(event)

    return exp

def get_duration(task, parents_as_tags=True, with_children=False):
    info = get_events(task, parents_as_tags, with_children)

    dt = timedelta()
    fmt = '%Y%m%dT%H%M%SZ'
    for event in info:
        s = datetime.strptime(event['start'], fmt).replace(tzinfo=timezone.utc)
        if 'end' in event:
            e = datetime.strptime(event['end'], fmt).replace(tzinfo=timezone.utc)
        else:
            e = datetime.now(timezone.utc)
        dt += e - s

    return dt

def get_ids(task, parents_as_tags=True):
    info = get_events(task, parents_as_tags)

    ids = []
    for event in info:
        ids.append(event['id'])

    return ids

def get_current_event():
    exported = subprocess.check_output('timew export :quiet'.split())
    info = json.loads(exported.decode('utf-8'))
    task = [event for event in info if event['id'] == 1][0]

    if 'end' in task:
        return None
    else:
        return task

def _is_tracking_task(task, current_event, parents_as_tags=True):
    tags = sorted(get_tags(task, parents_as_tags))

    if current_event is None:
        return False
    elif tags == sorted(current_event['tags']):
        return True
    else:
        return False


def _has_tracking_children(task, current_event, parents_as_tags=True):
    if _is_tracking_task(task, current_event, parents_as_tags):
        return True
    
    for child in task.children:
        if _has_tracking_children(child, current_event, parents_as_tags):
            return True

    return False

def is_tracking_task(task, parents_as_tags=True, include_children=False):
    current_event = get_current_event()
    if include_children:
        return _has_tracking_children(task, current_event, parents_as_tags)
    else:
        return _is_tracking_task(task, current_event, parents_as_tags)



def modify_hook(task_old, task_new, parents_as_tags=True):
    ids = get_ids(task_old, parents_as_tags)
    old_tags = get_tags(task_old, parents_as_tags)
    new_tags = get_tags(task_new, parents_as_tags)

    for t_id in ids:
        subprocess.call(['timew', 'untag', '@' + str(t_id)] + old_tags + [':yes', ':quiet'])
        subprocess.call(['timew', 'tag', '@' + str(t_id)] + new_tags + [':yes', ':quiet'])

    



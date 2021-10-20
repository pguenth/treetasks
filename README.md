# Treetasks - Organize tasks in an hierarchical format

*This application is in development. There will be missing features and bugs. Please report them.*

## Dependencies
* python3
* [python-anytree](https://anytree.readthedocs.io/)

## Usage
The application is inspired by tudu and uses similar concepts and workflows.
For keybindings reference, take a look at the cheatsheet provided in the repository.        

### Getting started
Run `./treetasks.py` and you will see an empty task tree.

Edit the empty task's title by pressing `i` to append or `C` to replace.
Append new tasks as siblings by using `o` or `O` or as children using `A` or `I`.
Move around the tree with `j`, `k`, `h` and `l`.
Tasks can be marked as done with `g` or cancelled with `v`.
Tasks with children can be collapsed with `f`.

For more keybindings and information take a look at the cheatsheet at `doc/cheatsheet/cheatsheet.pdf`.

### Files

If treetasks is invoked without arguments it looks for a config file at `~/.treetasks.ini` and a default tree file at `~/.treetasks.xml`.
The latter is created if it is not existing and is called `def` in treetasks' tab bar.
To change configuration options either create `~/.treetasks.ini` or copy the provided file at `data/default.ini`.

Both paths can be overridden using command line options, run `./treetasks.py -h` for more information.

### Movement
 
You can traverse the tree in two ways:
* **Flat:** The next/previous tasks are the tasks on the next/previous line, regardless of hierarchy
* **Hierarchically:** Traversing only traverses the siblings, visiting children/parents need explicit operations.
Treetasks always keeps both ways at your hands: there is a primary and a secondary mode of movement, the primary is mapped on the well-known `j` and `k` keys per default, and the secondary is mapped on `Y` and `U` keys per default.
By pressing `u` (default) the primary and secondary modes are swapped.
The default order can be set by the config variable `behaviour.primary_movement_hierarchic`.
When `True` the primary mode is hierarchical movement, when `False` the primary mode is flat movement.

For making hierarchical movement more practical there is the option `behaviour.auto_move_up` which when set to `True` (default) moves the cursor as in flat movement for one step when reaching the end of a set of children.

When `behaviour.roundtrip` is set the cursor can go around the ends of the list. If `behaviour.auto_move_up` is not set, children are also traversed in roundtrips.

### Schedule

The schedule shows tasks that are not marked as done or cancelled and have a scheduled date or due date assigned. 
They are sorted by the earlier date of those two.
Tasks whose scheduled date or due date lies in the past are printed in red, tasks that are scheduled or due today are printed in yellow.

The schedule has its own independent cursor which is controlled by `n` and `m` by default. You can directly skip to the top using `M` and to today using `N`.

* `behaviour.follow_schedule`: If set to `True` cursor movements in the schedule result in the tree cursor jumping to the task selected in the schedule (only if the task is currently shown in the tree). Default: `True`.
* `behaviour.filter_categories_schedule`: If set to `True`, the schedule is filtered by the same category filters that apply to the tree. Default: `False`.
* `behaviour.global_schedule`: If set to `True`, the schedule is generated from all tasks from all open tabs. If set to `False`, every tab has its own schedule. If a global schedule is used, a + sign denotes tasks that are not in the currently shown tab. If the cursor follows the schedule cursor, tabs are automatically switched, too. Default: `True`.


### Timewarrior

Treetasks has rudimentary support for [timewarrior](https://timewarrior.net/) which is activated by setting `plugins.timewarrior` to `True`.
Using `w` treetasks calls timewarrior to start tracking the currently highlighted task.
In detail treetasks collects the titles of the selected task and its categories and uses them as tags for timewarrior.
If `plugins.timewarrior_parents_as_tags` is set (which is the default and maybe the most sensible way to use treetasks with timewarrior) the titles and categories of all parents are also appended to the list of tags recursively.
This makes sense since work on *child_task* should also be shown if work on *parent_task* is considered.
Treetasks categories are implicitly used on children as well, for example if the category of *parent_task* is hidden *child_task* will not be shown, too.
If `plugins.timewarrior_propagate_modifications` is set to `True` editing the task's title or category will also edit those information in timewarrior to keep things in sync.
This is a bit experimental and may produce unwanted results in timewarrior.

If `plugins.timewarrior_show_state` is set to `True` treetasks
* highlights the task that is currently tracking in timewarrior and its parents by adding a green `R`
* shows the time spent on the task and its children in the description area.

These features are deactivated by default, because it results in loads of subprocess calls to timewarrior at the moment since at every cursor movement the task tree and task description are redrawn and therefore treetasks queries timewarrior for every task to see if it is active.
Maybe a better solution is implemented in the future. 
If you have an easy-to-implement idea how to implement this feature with less subprocess calls please do get in touch.




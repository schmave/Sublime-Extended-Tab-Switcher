import os
import random

import sublime
import sublime_plugin

last_highlighted_view = None

class ExtendedSwitcherListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        def test(a):
            if operator == sublime.OP_EQUAL:
                return a == operand
            if operator == sublime.OP_NOT_EQUAL:
                return a != operand
            return False

        if key == "extended_switcher_active":
            return test(last_highlighted_view is not None)


class ExtendedSwitcherCommand(sublime_plugin.WindowCommand):
    # declarations
    open_files = []
    open_views = []
    window = []
    settings = []

    # lets go
    def run(self, list_mode='window', cmd='show_switcher'):
        if cmd == 'close_view':
            if last_highlighted_view and not last_highlighted_view.is_dirty():
                window = last_highlighted_view.window()
                if window:
                    active = window.active_view_in_group(window.active_group())
                    window.focus_view(last_highlighted_view)
                    window.run_command('close')
                    window.focus_view(active)
            return

        # self.view.insert(edit, 0, "Hello, World!")
        self.group = self.window.active_group()
        self.open_files = []
        self.open_views = []
        self.window = sublime.active_window()
        self.settings = sublime.load_settings('ExtendedSwitcher.sublime-settings')
        folders = self.window.folders()

        for f in self.getViews(list_mode):
            # if skip the current active is enabled do not add the current file it for selection
            if self.settings.get('skip_current_file') == True:
                if f.id() == self.window.active_view().id():
                    continue

            self.open_views.append(f) # add the view object
            file_name = f.file_name() # get the full path
            file_path = ''

            if file_name:
                for folder in folders:
                    if os.path.commonprefix([folder, file_name]) == folder:
                        file_path = os.path.relpath(file_name, folder)

                # if there are any unsaved changes to the file, add a mark character
                if f.is_dirty():
                    file_name += self.settings.get('mark_dirty_file_char')
                    file_path += self.settings.get('mark_dirty_file_char')

                if self.settings.get('show_full_file_path'):
                    self.open_files.append([os.path.basename(file_name), file_path])
                else:
                    self.open_files.append([os.path.basename(file_name), ''])
            elif f.name():
                if f.is_dirty():
                    self.open_files.append([f.name() + self.settings.get('mark_dirty_file_char'), ''])
                else:
                    self.open_files.append([f.name(), ''])
            else:
                if f.is_dirty():
                    self.open_files.append(["Untitled"+self.settings.get('mark_dirty_file_char'), ''])
                else:
                    self.open_files.append(["Untitled", ''])
            # Add a random number as the third element within each open_files element so
            # that the view (added next), is never used for sorting
            self.open_files[-1].extend([random.random(), f])

        if self.check_for_sorting():
            self.open_files.sort()
            self.open_views = [x[3] for x in self.open_files]

        # Strip off the random number and view reference
        self.open_files = [x[:2] for x in self.open_files]

        if self.settings.get('show_full_file_path') == "first":
            self.open_files = [[x[1], x[0]] if x[1] else [x[0], x[1]] for x in self.open_files]

        quick_panel_list = self.open_files
        if self.settings.get('compact_panel'):
            quick_panel_list = [x[0] if x[0] else x[1] for x in self.open_files]

        # show the file list
        self.window.show_quick_panel(quick_panel_list, self.tab_selected,
                                     False, -1, self.tab_highlighted)

    def tab_highlighted(self, selected):
        global last_highlighted_view
        last_highlighted_view = self.open_views[selected]

    # display the selected open file
    def tab_selected(self, selected):
        global last_highlighted_view
        last_highlighted_view = None

        if selected > -1:
            if self.settings.get('move_to_current_pane') == True:
                self.window.set_view_index(self.open_views[selected], self.group, 0)
            self.window.focus_view(self.open_views[selected])

        return selected

    # flags for sorting
    def check_for_sorting(self):
        if self.settings.has("sort"):
            return self.settings.get("sort", False)


    def getViews(self, list_mode):
        views = []
        # get only the open files for the active_group
        if list_mode == "active_group":
            views = self.window.views_in_group(self.window.active_group())

        # get all open view if list_mode is window or active_group doesn't have any files open
        if (list_mode == "window") or (len(views) < 1):
            views = self.window.views()

        return views

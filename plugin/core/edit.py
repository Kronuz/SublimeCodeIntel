import os
import sublime
import sublime_plugin

from .url import uri_to_filename
from .protocol import Range
from .logging import debug
from .workspace import get_project_path
from .views import range_to_region


def apply_workspace_edit(window, params):
    edit = params.get('edit', dict())
    window.run_command('code_intel_apply_workspace_edit', {'changes': edit.get('changes'),
                                                          'documentChanges': edit.get('documentChanges')})


class CodeIntelApplyWorkspaceEditCommand(sublime_plugin.WindowCommand):
    def run(self, changes=None, documentChanges=None):
        # debug('workspace edit', changes)
        documentsChanged = 0
        if changes:
            for uri, file_changes in changes.items():
                path = uri_to_filename(uri)
                self.open_and_apply_edits(path, file_changes)
                documentsChanged += 1
        elif documentChanges:
            for document in documentChanges:
                uri = document.get('textDocument').get('uri')
                path = uri_to_filename(uri)
                self.open_and_apply_edits(path, document.get('edits'))
                documentsChanged += 1

        if documentsChanged > 0:
            message = 'Applied changes to {} documents'.format(documentsChanged)
            self.window.status_message(message)
        else:
            self.window.status_message('No changes to apply to workspace')

    def open_and_apply_edits(self, path, file_changes):
        view = self.window.open_file(path)
        if view:
            if view.is_loading():
                # TODO: wait for event instead.
                sublime.set_timeout_async(
                    lambda: view.run_command('code_intel_apply_document_edit', {'changes': file_changes}),
                    500
                )
            else:
                view.run_command('code_intel_apply_document_edit',
                                 {'changes': file_changes,
                                  'show_status': False})
        else:
            debug('view not found to apply', path, file_changes)


class CodeIntelApplyDocumentEditCommand(sublime_plugin.TextCommand):
    def run(self, edit, changes=None, show_status=True):

        # Sort changes due to issues with self.view.get_regions
        # See https://github.com/tomv564/LSP/issues/325
        changes = self.changes_sorted(changes)

        regions = list(self.create_region(change) for change in changes)
        replacements = list(change.get('newText') for change in changes)

        # TODO why source.python here?
        self.view.add_regions('code_intel_edit', regions, "source.python")

        index = 0
        last_region_count = len(regions)
        for newText in replacements:
            # refresh updated regions after each edit.
            updated_regions = self.view.get_regions('code_intel_edit')
            region = updated_regions[index]  #
            self.apply_change(region, newText, edit)
            if len(self.view.get_regions('code_intel_edit')) == last_region_count:
                index += 1  # no regions lost, move to next region.
            else:
                # current region was removed, don't advance index.
                last_region_count = len(self.view.get_regions('code_intel_edit'))

        self.view.erase_regions('code_intel_edit')
        if show_status:
            window = self.view.window()
            if window:
                base_dir = get_project_path(window)
                file_path = self.view.file_name()
                relative_file_path = os.path.relpath(file_path, base_dir) if base_dir else file_path
                message = 'Applied {} change(s) to {}'.format(len(changes), relative_file_path)
                window.status_message(message)

    def changes_sorted(self, changes):
        # changes looks like this:
        # [
        #   {
        #       'newText': str,
        #       'range': {
        #            'start': {'line': int, 'character': int},
        #            'end': {'line': int, 'character': int}
        #       }
        #   }
        # ]

        # Maps a change to the tuple (range.start.line, range.start.character)
        def get_start_position(change):
            r = change.get('range')
            start = r.get('start')
            line = start.get('line')
            character = start.get('character')
            return (line, character)  # Return tuple so comparing/sorting tuples in the form of (1, 2)

        # Sort by start position
        return sorted(changes, key=get_start_position)

    def create_region(self, change):
        return range_to_region(Range.from_lsp(change['range']), self.view)

    def apply_change(self, region, newText, edit):
        if region.empty():
            self.view.insert(edit, region.a, newText)
        else:
            if len(newText) > 0:
                self.view.replace(edit, region, newText)
            else:
                self.view.erase(edit, region)

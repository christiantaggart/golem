import os
import tempfile
from copy import deepcopy

from apps.core.task.coretaskstate import (TaskDefinition,
                                          TaskDefaults, Options)
from apps.dummy.dummyenvironment import DummyTaskEnvironment
from golem.core.common import get_golem_path
from golem.resource.dirmanager import symlink_or_copy


# moved it to dir_manager and created tests, in PR#1297
def ls_R(dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(dir, followlinks=True):
        for name in filenames:
            files.append(os.path.join(dirpath, name))
    return files


class DummyTaskDefaults(TaskDefaults):
    """ Suggested default values for dummy task"""

    def __init__(self):
        super(DummyTaskDefaults, self).__init__()
        self.options = DummyTaskOptions()
        self.options.difficulty = 0xffff0000  # magic number

        self.shared_data_files = ["in.data"]
        self.out_file_basename = "out"
        self.default_subtasks = 5
        self.code_dir = os.path.join(get_golem_path(),
                                     "apps", "dummy", "resources", "code_dir")
        self.result_size = 256  # length of result hex number

        @property
        def full_task_timeout(self):
            return self.default_subtasks * self.subtask_timeout

        @property
        def subtask_timeout(self):
            return 1200


class DummyTaskDefinition(TaskDefinition):
    def __init__(self, defaults=None):
        TaskDefinition.__init__(self)

        self.options = DummyTaskOptions()

        # subtask data
        self.shared_data_files = []

        # subtask code
        self.code_dir = os.path.join(get_golem_path(),
                                     "apps", "dummy", "resources", "code_dir")
        self.code_files = []

        self.result_size = 256  # length of result hex number
        self.out_file_basename = "out"

        if defaults:
            self.set_defaults(defaults)

    def add_to_resources(self):
        super().add_to_resources()

        # TODO create temp in task directory
        # but for now TaskDefinition doesn't know root_path
        # task_root_path = ""
        # self.tmp_dir = DirManager().get_task_temporary_dir(self.task_id, True)

        self.tmp_dir = tempfile.mkdtemp()

        self.shared_data_files = list(self.resources)
        self.code_files = ls_R(self.code_dir)

        symlink_or_copy(self.code_dir, os.path.join(self.tmp_dir, "code"))

        # makes sense when len(..) > 1
        # common_data_path = os.path.commonpath(self.shared_data_files)
        # but we only have 1 file here
        data_path = os.path.join(self.tmp_dir, "data")
        data_file = list(self.shared_data_files)[0]
        if os.path.exists(data_path):
            raise Exception("Error adding to resources: data path: {} exists"
                            .format(data_path))

        os.mkdir(data_path)
        symlink_or_copy(data_file,
                        os.path.join(data_path, os.path.basename(data_file)))

        self.resources = set(ls_R(self.tmp_dir))

    # TODO maybe move it to the CoreTask?
    def set_defaults(self, defaults: DummyTaskDefaults):
        self.shared_data_files = deepcopy(defaults.shared_data_files)
        self.out_file_basename = defaults.out_file_basename
        self.code_dir = defaults.code_dir
        self.result_size = defaults.result_size
        self.total_subtasks = defaults.default_subtasks
        self.options = deepcopy(defaults.options)


class DummyTaskOptions(Options):
    def __init__(self):
        super(DummyTaskOptions, self).__init__()
        self.environment = DummyTaskEnvironment()
        self.subtask_data_size = 128  # # length of subtask-specific hex number

        # The difficulty is a 4 byte int; 0xffffffff is the greatest
        # and 0x00000000 is the least difficulty.
        # For example difficulty 0xffff0000 requires
        # 0xffffffff /(0xffffffff - 0xffff0000) = 65537
        # hash computations on average.
        self.difficulty = 0xffff0000

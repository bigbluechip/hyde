import sys
from file_system import Folder
from django.conf import settings

def load_processor(name):
    (module_name, _ , processor) = name.rpartition(".")
    __import__(module_name)
    module = sys.modules[module_name]
    return getattr(module, processor)


class HydeFolder(Folder):    
    def __init__(self, path, processors, ignore_root=False):
        super(HydeFolder, self).__init__(path)
        self.processors = processors
        self.default_processors = processors["*"]
        self.ignore_root = ignore_root
        self.previous_folder = None
        
    def visit_folder(self, visitor, folder):
        if not self.previous_folder or \
                not folder.is_child_of(self.previous_folder):
                self.current_processors = {}
                self.current_processors.update(self.default_processors)
        fragment = folder.get_fragment(self.path)
        if len(fragment) and self.processors.has_key(fragment):
            self.current_processors.update(self.processors[fragment])
        super(HydeFolder, self).visit_folder(visitor, folder)
    
    def visit_file(self, visitor, a_file):
        target = a_file.parent.create_mirror_folder(
                                self, settings.TMP_DIR, 
                                self.ignore_root)
        a_file = a_file.copy_to(target)
        self.process_file(a_file)
        super(HydeFolder, self).visit_file(visitor, a_file)
        
    def process_file(self, a_file):
        if a_file and a_file.exists and \
        self.current_processors.has_key(a_file.extension):
            a_file_processors = self.current_processors[a_file.extension]
            for processor_name in a_file_processors:
                if a_file and a_file.exists:
                    processor = self.load_processor(processor_name)
                    a_file = processor.process(a_file)
                    
    def load_processor(self, processor_name):
        return load_processor(processor_name)

class MediaFolder(HydeFolder):
    def __init__(self):
        super(MediaFolder, self).__init__(settings.MEDIA_DIR,
                                            settings.MEDIA_PROCESSORS)
        
class ContentFolder(HydeFolder):
    def __init__(self):
        super(ContentFolder, self).__init__(settings.CONTENT_DIR,
                                            settings.CONTENT_PROCESSORS)
        self.ignore_root = True
        
class TempFolder(Folder):
    def __init__(self):
        super(TempFolder, self).__init__(settings.TMP_DIR)
        
    def visit_folder(self, visitor, folder):
        fragment = folder.get_fragment(self.path)
        if len(fragment) and settings.SITE_POST_PROCESSORS.has_key(fragment):
            processors = settings.SITE_POST_PROCESSORS[fragment]
            for processor_name, params in processors.iteritems():
                processor = load_processor(processor_name)
                processor.process(folder, params)
import json
import os

class JObject(object):

    def __init__(self):
        self.file_path = None
        self.content   = None
        self.jcontent  = None

    def get_field(self, key, data_types=None, optional=False, default=None):
        if key not in self.jcontent:
            if optional:
                return default
            raise Exception('field {field} not found'.format(field=key))

        jvalue = self.jcontent[key]

        data_types = data_types or (str, unicode)

        if data_types is not None and not isinstance(jvalue, data_types):
            raise Exception('field {field} must be of type {type}'.format(field=key, type='|'.join(map(lambda x: x.__name__, data_types))))

        return jvalue

    def parse(self):
        raise Exception('JObject::parseo method must be implemented by child class')

    def parsej(self, jcontent):
        self.jcontent = jcontent
        self.parse()

    def parsec(self, content):
        self.content = content

        try:
            jcontent = json.loads(self.content)
        except ValueError:
            raise Exception('invalid json content:\n{content}'.format(content=self.content))
        else:
            self.parsej(jcontent)

    def parsef(self, file_path):
        self.file_path = file_path

        if not os.path.exists(self.file_path):
            raise Exception('path does not exist: {file_path}'.format(file_path=self.file_path))

        if not os.path.isfile(self.file_path):
            raise Exception('path is not a file: {file_path}'.format(file_path=self.file_path))

        try:
            ftr = open(self.file_path)
        except IOError:
            raise Exception('unable to read file: {file_path}'.format(file_path=self.file_path))
        else:
            content = ftr.read()
            ftr.close()

        self.parsec(content)

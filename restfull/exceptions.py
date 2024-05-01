##
##

import os
import inspect
import logging
import json


class APIException(Exception):

    def __init__(self, message, response, code):
        self.code = code
        try:
            self.body = json.loads(response)
        except json.decoder.JSONDecodeError:
            self.body = {'message': response}
        logger = logging.getLogger(self.__class__.__name__)
        frame = inspect.currentframe().f_back
        (filename, line, function, lines, index) = inspect.getframeinfo(frame)
        filename = os.path.basename(filename)
        self.message = f"{message} [{function}]({filename}:{line})"
        logger.debug(self.message)
        super().__init__(self.message)

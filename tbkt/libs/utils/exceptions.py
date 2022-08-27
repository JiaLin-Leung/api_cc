#coding=utf-8

class CustomError(Exception):
    def __init__(self, msg, code=''):
        """

        :param code: error code
        :param message: error message
        :return:
        """
        Exception.__init__(self)
        self.message = msg
        self.error_code = code

    def __str__(self):
        return "%s %s" % (
            self.error_code,
            self.message,
        )

    def set_error_code(self, code):
        self.error_code = code

    def set_error_msg(self, msg):
        self.message = msg

    def get_error_code(self):
        return self.error_code

    def get_error_msg(self):
        return self.message
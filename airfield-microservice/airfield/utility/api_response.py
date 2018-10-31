# -*- coding: utf-8 -*-
"""Standard response object to use in the app's routes."""

#  standard imports
from enum import Enum


class ApiResponseStatus(Enum):
    SUCCESS = 200
    INTERNAL_ERROR = 500


class ApiResponse(object):
    def __init__(self,
                 status: ApiResponseStatus = None,
                 data: dict = None,
                 error_message: str = None):
        self.status = status
        self.data = data
        self.error_message = error_message

    def to_json(self):
        if self.status != ApiResponseStatus.SUCCESS:
            return {
                "status": self.status.value,
                "error": self.error_message
            }
        else:
            return {
                "data": self.data
            }


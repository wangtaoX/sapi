#!/usr/bin/env python
# encoding: utf-8

class SapiException(Exception):
    message = "unknown exception."

    def __init__(self, message):
        super(SapiException, self).__init__(message)
        self.msg = message

class SapiNotFound(SapiException):
    message = "404 Not Found"

class SapiBadRequest(SapiException):
    message = "Bad Request"

class SapiTorConfigError(SapiException):
    message = "Tor config error"

class SapiNoAvaVlanError(SapiException):
    message = "No avaliable vlan id"

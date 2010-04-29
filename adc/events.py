import types

class Event:
  def __init__(self):
    if type(self.__signals__) != list:
      raise ValueError, "self.__signals__ is not a list"

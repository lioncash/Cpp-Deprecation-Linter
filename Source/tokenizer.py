# TODO: Seriously rework this to actually do tokenizing work.

class Token:
	def __init__(self, lineNumber, string):
		self.lineNumber = lineNumber
		self.string = string

	def __str__(self):
		return self.string

	def __repr__(self):
		return self.string
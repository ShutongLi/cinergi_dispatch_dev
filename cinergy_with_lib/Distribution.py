class DistObj:
    def __init__(self, aname):
        self.name = aname
        self.url = ''
        self.description = ''
        self.protocol = ''
        self.appprofile = ''
        self.functioncode = ''
        self.functiontext = ''
        self.distorg = ''
        self.formatlist = []

    def dump(self):
        return {"adistobj": {'name': self.name,
                             'url': self.url,
                             'description': self.description,
                             'protocol': self.protocol,
                             'appprofile': self.appprofile,
                             'functioncode': self.functioncode,
                             'functiontext': self.functiontext,
                             'distorg': self.distorg,
                             'formatlist': self.formatlist
                             }}
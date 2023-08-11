class _HTTP:
    def __init__(self, data):
        try:
            self.data = data.decode('utf-8')
        except:
            self.data = data

    def __repr__(self):
        return 'HTTP'

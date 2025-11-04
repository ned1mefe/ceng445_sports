class Catalog:
    def __init__(self):
        self.attachDict = {} # user (or userID) -> [objectId]
        self.objectDict = {} # objectId -> object

    def create(self, **kw):
        #TODO:: implement this after object implementations
        pass

    def list(self):
        #should also return description?? with ids
        return list(self.objectDict.keys()) 

    def listattached(self, user):
        if (user not in self.attachDict):
            raise ValueError()

        return [self.objectDict[objId] for objId in self.attachDict[user]] 

    def attach(self, id, user):
        if user in self.attachDict:
            if id not in self.attachDict[user]:
                self.attachDict[user].append(id)
        else:
            self.attachDict[user] = [id]

    def detach(self, id, user):
        if user in self.attachDict:
            if id in self.attachDict[user]:
                self.attachDict[user].remove(id)
            else:
                raise ValueError()
        else:
            raise ValueError()

    def delete(self, id):
        if id not in self.objectDict:
            raise ValueError()
        
        isAttached = False

        for objIds in self.attachDict.values():
            if id in objIds:
                isAttached = True
                break
        
        if isAttached:
            raise ValueError()

        obj = self.objectDict.pop(id)
        
        #not sure if its necessary
        # del(obj)


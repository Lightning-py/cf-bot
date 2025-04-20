import Participant
import User

import csv
from copy import deepcopy

from codeforces import api




class Monitor:

    def __init__(
        self,
        api_key,
        api_secret,
        participantsFile="participants.csv",
        datafile="data.txt",
    ):
        self.datafile=datafile
        self.api_key = api_key
        self.api_secret = api_secret

        self.users = {}
        self.contestIDsTOUserIDs = {}
        self.participants = {}

        self.submissions = {}
        self.old_submissions = {}
        self.new_submissions = {}

        self.uploadParticipants(participantsFile)
        self.uploadData()

    def uploadParticipants(self, file):
        try:
            with open(file, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                first = True
                for p in reader:
                    if first:
                        first = False
                        continue
                    handle, name, group, grade = (
                        p[10],
                        " ".join([p[0], p[1], p[2]]),
                        p[7],
                        p[6],
                    )

                    if group.lower() != 'python' and handle != '-':
                        participant = Participant.Participant(handle, name, group, grade)

                        self.participants[handle] = participant
        except:
            pass

    def uploadData(self):
        # данные в файле хранятся следующим образом
        # {количество пользователей}
        # {чат-id пользователя}
        # [ список контестов для мониторинга ]


        try:
            with open(self.datafile, "r") as file:
                usersCount = int(file.readline().strip())
                for i in range(usersCount):
                    chatId = int(file.readline().strip())
                    contestsIds = list(map(int, file.readline().strip().split()))

                    self.users[chatId] = User.User(chatId, contestsIds)

                    for c in contestsIds:
                        if c in self.contestIDsTOUserIDs:
                            self.contestIDsTOUserIDs[c].add(chatId)
                        else:
                            self.contestIDsTOUserIDs[c] = set([chatId])
        except:
            pass

    def unloadData(self):
        try:
            with open(self.datafile, "w") as file:
                userCount = len(self.users)
                file.write(str(userCount) + '\n')

                for user_id in self.users.keys():
                    file.write(str(user_id) + '\n')
                    file.write(' '.join(list(map(str, self.users[user_id].contests))) + '\n')
        except:
            pass

    def updateSubmissions(self, firstTime=False):
        try:
            self.old_submissions = deepcopy(self.submissions)
            self.submissions.clear()
            self.new_submissions.clear()

            for contest in self.contestIDsTOUserIDs.keys():
                self.submissions[contest] = api.call(
                    "contest.status",
                    key=self.api_key,
                    secret=self.api_secret,
                    contestId=contest,
                    asManager=True,
                )
            
                # теперь сравним с прошлыми

                if contest in self.old_submissions.keys():
                    old_submissions = self.old_submissions[contest]

                    self.new_submissions[contest] = []
                    if len(old_submissions) < len(self.submissions[contest]):
                        new_subs = []
                        for i in range(len(self.submissions[contest]) - len(old_submissions)):
                            new_subs.append(self.submissions[contest][i])
                        self.new_submissions[contest] = new_subs
                else:
                    self.new_submissions[contest] = self.submissions[contest]
        except:
            pass
    

    def deleteUser(self, userId):
        try:
            if userId in self.users.keys():
                for c in self.users[userId].contests:
                    self.contestIDsTOUserIDs[c].remove(userId)

                self.users.pop(userId)
        except:
            pass

    def addUser(self, user):
        try:
            chatId = user.chat_id
            contestsIds = user.contests

            self.users[chatId] = User.User(chatId, contestsIds)

            for c in contestsIds:
                if c in self.contestIDsTOUserIDs:
                    self.contestIDsTOUserIDs[c].add(chatId)
                else:
                    self.contestIDsTOUserIDs[c] = set([chatId])
        except:
            pass
    
    def addUserContests(self, chatId, contests):
        try:
            if chatId in self.users.keys():
                # self.users[chatId] = User.User(chatId, self.users[chatId].contests + contests)
                self.users[chatId].contests = self.users[chatId].contests + contests

                for c in contests:
                    if c in self.contestIDsTOUserIDs:
                        self.contestIDsTOUserIDs[c].add(chatId)
                    else:
                        self.contestIDsTOUserIDs[c] = set([chatId])
        except:
            pass
    
    def removeUserContest(self, chatId, contests):
        try:
            if chatId in self.users.keys():
                contests_ = self.users[chatId].contests

                for c in contests:
                    if c in contests_:
                        contests_.remove(c)
                
                self.users[chatId].contests = contests_
        except:
            pass
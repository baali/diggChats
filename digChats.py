# This is simple program to Download, parse/iterate over all chat
# conversation I had on gtalk, based on this stackoverflow
# conversation
# http://stackoverflow.com/questions/8146970/accessing-chat-folder-in-python-using-imaplib
import email
import getpass, imaplib
import os
import sys
from lxml import etree

def extractBody(payload):
    if isinstance(payload,str):
        return payload
    else:
        return '\n'.join([extractBody(part.get_payload()) for part in payload])

def sortInt(a, b):
    return cmp(int(a), int(b))

def numOfLinesPerDay(userName):
    # histogram of number of lines of conversation per day
    from dateutil import parser
    import datetime
    from pylab import plot, savefig, array, sort, xlabel, ylabel
    from lxml import etree
    from lxml.etree import XMLSyntaxError    
    dateDict = {}
    chatIds = sorted(os.listdir('chats/'), sortInt)
    dateList = []
    for chatId in chatIds:
        chatData = open('chats/'+chatId).read()
        msg = email.message_from_string(chatData)
        payloads = [msgBlock.get_payload() for msgBlock in msg.get_payload()]
        htmlParser = etree.HTMLParser(encoding='utf-8', recover=True)
        dt = parser.parse(msg['date']).date()
        if dt == datetime.date(1969, 12, 31):
            print 'This is message from past...'
            print msg['To'], msg['From']
            for payload in payloads:
                payload =  payload.replace('=\r\n','')
                tree = etree.fromstring(payload, htmlParser)
                for el in tree.iter():
                    if el.tag == 'body' and el.text:
                        print el.text
            continue
        if dt not in dateDict:
            dateDict[dt] = {}
        for payload in payloads:
            # I don't know why google chat payload has this string =\r\n
            # sprinkled all across the conversation
            payload =  payload.replace('=\r\n','')
            try:
                tree = etree.fromstring(payload, htmlParser)
                for el in tree.iter():
                    if el.tag == 'message':
                        sender = el.get('from')
                        if userName in sender:
                            # line sent by me
                            if 'me' in dateDict[dt]:
                                dateDict[dt]['me'] += 1
                            else:
                                dateDict[dt]['me'] = 1
                        else:
                            # line sent to me
                            if sender in dateDict[dt]:
                                dateDict[dt][sender] += 1
                            else:
                                dateDict[dt][sender] = 1
                        # print el.get('to'), el.get('from')
                    # if 'body' == el.tag and el.text:
                        # text = el.text.replace('=\r\n', '')
                        # print text
            except XMLSyntaxError:
                print "lxml can't process this block"
        # print 'done chatId:', chatId
    # order of keys in dictionary is not guaranteed not sure how is
    # this working :-/
    for item in dateDict:
        # this is sum of lines sent to and by me
        dateList.append((item, sum(dateDict[item].values())))
    dateArray = array(dateList)
    plot(dateArray[:,0], dateArray[:,1], 'o')
    xlabel('Date')
    ylabel('Length of conversation in number of lines')
    savefig('NumberOfLinesPerDay.png')
    
def numOfPeoplePerDay(userName):
    # parsing all chat conversations to get number of different users
    # vs per day plot.
    from dateutil import parser
    import datetime
    from pylab import plot, savefig, array, sort, xlabel, ylabel
    dateDict = {}
    chatIds = sorted(os.listdir('chats/'), sortInt)
    dateList = []
    for chatId in chatIds:
        chatData = open('chats/'+chatId).read()
        msg = email.message_from_string(chatData)
        # we just have to count number of conversation with different
        # people on this date
        dt = parser.parse(msg['date']).date()
        # I have no idea how I have conversation on this date
        if dt == datetime.date(1969, 12, 31):
            continue
        # print dt
        if dt in dateDict:
            if msg['To'] not in dateDict[dt] and userName not in msg['To']:
                dateDict[dt].append(msg['To'])
            elif msg['From'] not in dateDict[dt] and userName not in msg['From']:
                dateDict[dt].append(msg['From'])
                # peers.append(msg['From'])
        else:
            if userName in msg['From']:
                dateDict[dt] = [msg['To']]
            else:
                dateDict[dt] = [msg['From']]
    # print peers, dateDict    
    # order of keys in dictionary is not guaranteed not sure how is
    # this working :-/
    for item in dateDict:
        dateList.append((item, len(dateDict[item])))
    dateArray = array(dateList)
    # sortedArray = sort(dateArray, axis=0)
    # plot(sortedArray[:,0], sortedArray[:,1], 'o')
    plot(dateArray[:,0], dateArray[:,1], 'o')
    xlabel('Date')
    ylabel('Number of different peers')
    savefig('NumperOfPeoplePerDay.png')

def diggLinks(emailId):
    # Iterating over all chat logs from emailId for links.
    from lxml import etree
    from lxml.etree import XMLSyntaxError
    from urlparse import urlparse
    chatIds = sorted(os.listdir('chats/'), sortInt)
    linkFile = open('links'+emailId+'.txt', 'w')
    for chatId in chatIds:
        chatData = open('chats/'+chatId).read()
        msg = email.message_from_string(chatData)
        if emailId in msg['From'] or emailId in msg['To']:
            payloads = [msgBlock.get_payload() for msgBlock in msg.get_payload()]
            parser = lxml.etree.HTMLParser(encoding='utf-8', recover=True)
            for payload in payloads:
                # I don't know why google chat payload has this string =\r\n
                # sprinkled all across the conversation
                payload =  payload.replace('=\r\n','')
                try:
                    tree = etree.fromstring(payload, parser)
                    for el in tree.iter():
                        if 'body' == el.tag and el.text:
                            text = el.text.replace('=\r\n', '')
                            # print text
                            for word in text.split():
                                urlParse = urlparse(word)
                                if bool(urlParse.netloc):
                                    print msg['date']
                                    print 'url...', urlParse.geturl()
                                    linkFile.write('on '+msg['date']+' '+urlParse.geturl()+'\n')
                except XMLSyntaxError:
                    print "lxml can't process this block"
    linkFile.close()

def downloadChats(imapSession):
    # this function download all chat conversations and store them
    # inside subfolder named 'chats'    
    if 'attachments' not in os.listdir('.'):
        os.mkdir('chats')
    try:
        imapSession.select('[Gmail]/Chats', True)
        typ, data = imapSession.search(None, 'ALL')
        if typ != 'OK':
            print 'Error searching Chats.'
            raise
        # Iterating over all chat logs
        for chatId in data[0].split():
            if os.path.isfile('chats/'+chatId):
                continue
            typ, messageParts = imapSession.fetch(chatId, '(RFC822)')
            if typ != 'OK':
                print 'Error fetching chat log.'
                raise
            msg = email.message_from_string(messageParts[0][1])
            print 'Chat conversation with', msg['From'], 'on', msg['Date']
            fp = open('chats/'+chatId, 'w')
            fp.write(messageParts[0][1])
            fp.close()
    except :
        print 'Failed to download all chats.'
    
if __name__ == "__main__":
    userName = raw_input('Enter your GMail username:')
    passwd = getpass.getpass('Enter your password: ')
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
        typ, accountDetails = imapSession.login(userName, passwd)
        if typ != 'OK':
            print 'Not able to sign in!'
            raise
        downloadChats(imapSession)
    except :
        print 'Failed to log in.'
    imapSession.close()
    imapSession.logout()    
    numOfPeoplePerDay(userName)
    numOfLinesPerDay(userName)

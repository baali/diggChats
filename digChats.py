import email
import getpass, imaplib
import os
import sys
from lxml import etree

def extract_body(payload):
    if isinstance(payload,str):
        return payload
    else:
        return '\n'.join([extract_body(part.get_payload()) for part in payload])

def sortInt(a, b):
    return cmp(int(a), int(b))

def numOfPeoplePerDay():
    from dateutil import parser
    import datetime
    from pylab import plot, savefig, array, sort
    dateDict = {}
    chatIds = sorted(os.listdir('chats/'), sortInt)
    dateList = []
    for chatId in chatIds:
        chatData = open('chats/'+chatId).read()
        msg = email.message_from_string(chatData)
        # we just have to count number of conversation with different
        # people on this date
        dt = parser.parse(msg['date']).date()
        if dt == datetime.date(1969, 12, 31):
            continue
        # print dt
        if dt in dateDict:
            if msg['To'] not in dateDict[dt] and 'choudhary.shantanu' not in msg['To']:
                dateDict[dt].append(msg['To'])
            elif msg['From'] not in dateDict[dt] and 'choudhary.shantanu' not in msg['From']:
                dateDict[dt].append(msg['From'])
                # peers.append(msg['From'])
        else:
            if 'choudhary.shantanu' in msg['From']:
                dateDict[dt] = [msg['To']]
            else:
                dateDict[dt] = [msg['From']]
    # print peers, dateDict
    for item in dateDict:
        dateList.append((item, len(dateDict[item])))
    dateArray = array(dateList)
    # sortedArray = sort(dateArray, axis=0)
    # plot(sortedArray[:,0], sortedArray[:,1], 'o')
    plot(dateArray[:,0], dateArray[:,1], 'o')
    savefig('chatNumbers.pdf')
    # return dateArray

def digLinks(emailId):
    # Iterating over all chat logs for extracting links.
    from lxml import etree
    from lxml.etree import XMLSyntaxError
    from StringIO import StringIO
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
    numOfPeoplePerDay()

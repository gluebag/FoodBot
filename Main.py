__author__ = 'gluebag'

# import facebot open source API
import time
from facebot import Facebook


# setup facebook constants
FACEBOOK_USERID = '100000605485635'
FACEBOOK_GENIE_USERID = '708914472545164'
FACEBOOK_DTSG = 'AQGpKj4g31Ga:AQGs9zDgoS4V'
FACEBOOK_COOKIES_DICT = {
    'datr': '65mHVEWhckhJYqK1NGmjanO5',
    'sb': '5xQTV2c31vv26X6eX_sIg9F4',
    'c_user': '100000605485635',
    'fr': '0xZp3vNI1cSznnQRW.AWVKM40IiC5ZojJrp--TgOupHPY.BXExTn.q8.AAA.0.AWVaGwIP',
    'xs': '109:7gwRepTXYxZhAA:2:1460868327:19808',
    'csm': '2',
    's': 'Aa7Rn-F_IL2jiNqQ.BXExTn',
    'pl': 'n',
    'lu': 'TisfV88GYaSoS2ryiEehnECw'
}

# setup facebook object
facebook_object = Facebook(FACEBOOK_USERID, FACEBOOK_DTSG)

# add in cookies we need
for k in FACEBOOK_COOKIES_DICT:
    facebook_object.add_session_cookie(k, FACEBOOK_COOKIES_DICT[k], domain='.facebook.com')

# constantly check for new messages/convos
while True:

    # get all the conversations for the genie page
    convos = facebook_object.get_all_conversations(FACEBOOK_GENIE_USERID)

    # loop through each conversation and get the messages for it
    for convo in convos:
        conversation_id = convo["thread_fbid"]
        # print 'Pulling messages for conversation: [%s]' % conversation_id

        messages = facebook_object.get_all_messages_for_conversation_id(FACEBOOK_GENIE_USERID, conversation_id)
        for message in messages:
            is_new = message["is_unread"]
            if not is_new:
                continue

            print 'NEW MESSAGE:'
            print '----------------------'
            print '[%s]: %s' % (message['author'], message['body'])

            # mark it as read
            facebook_object.mark_message_read(FACEBOOK_GENIE_USERID, conversation_id)

            # reply to it
            facebook_object.send_message(FACEBOOK_GENIE_USERID, conversation_id, FACEBOOK_GENIE_USERID, conversation_id, 'This is an automated reply')

    # sleep for 5 seconds
    time.sleep(5)
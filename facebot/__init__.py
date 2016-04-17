# -*- encoding: utf-8 -*-
import re
import logging
import json
import time

import requests
from lxml import etree
from random import randint
from facebot.message import (
    send_group, send_person, group_typing, person_typing,
    read)
from facebot.sticker import get_stickers

logging.basicConfig()
log = logging.getLogger('facebook')
log.setLevel(logging.WARN)

USER_AGENT = 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0'

LOGIN_URL = 'https://www.facebook.com/login.php'
ACCESS_TOKEN_URL = 'https://developers.facebook.com/tools/explorer/{}/permissions?version=v2.1&__user={}&__a=1&__dyn=5U463-i3S2e4oK4pomXWo5O12wAxu&__req=2&__rev=1470714'
PING_URL = 'https://0-channel-proxy-06-ash2.facebook.com/active_ping?channel=p_{user_id}&partition=-2&clientid=5ae4ed0b&cb=el2p&cap=0&uid={user_id}&viewer_uid={user_id}&sticky_token=479&state=active'


class LoginError(Exception):
    pass


class Facebook:

    def __init__(self, user_id, fb_dtsg):
        # create a session instance
        self.session = requests.Session()
        # use custom user-agent
        self.session.headers.update({'User-Agent': USER_AGENT})

        # login with email and password
        # GLUE UPDATE --> on failure, still setup object
        # self._login(email, password)

        self.user_id = str(user_id)
        log.debug('user_id: %s', self.user_id)

        # get facebook dtsg
        self.dtsg = str(fb_dtsg)
        log.debug('fb_dtsg: %s', self.dtsg)

        log.debug('we\'re ready')

    def add_session_cookie(self, name, value, **kwargs):
        self.session.cookies.set(name, value)

    # this method will pull all the conversations for a particular page
    def get_all_conversations(self, page_id):

        post_data = {
            'client': 'mercury',
            'inbox[offset]': '0',
            'inbox[limit]': '21',
            'inbox[filter]': '',
            'request_user_id': page_id,
            '__user': self.user_id,
            '__a': '1',
            '__req': '19',
            '__be': '0',
            'fb_dtsg': self.dtsg,
            '__rev': '2288795'
        }

        url = 'https://www.facebook.com/ajax/mercury/threadlist_info.php?dpr=2'

        res = self.session.post(url, data=post_data, timeout=60)
        src = str(res.text)
        src = src.replace('for (;;);', '')

        # remove for (;;); so we can turn them into dictionaries
        return json.loads(src)["payload"]["threads"]

    # method to get all the messages within a facebook conversation based on a conversation id
    def get_all_messages_for_conversation_id(self, page_id, conversation_id):

        post_data = {
            'messages[user_ids][' + conversation_id + '][offset]': '0',
            'messages[user_ids][' + conversation_id + '][timestamp]': '',
            'messages[user_ids][' + conversation_id + '][limit]': '200',
            'client': 'mercury',
            'request_user_id': page_id,
            '__user': self.user_id,
            '__a': '1',
            '__req': '19',
            '__be': '0',
            'fb_dtsg': self.dtsg,
            '__rev': '2288795'
        }

        url = 'https://www.facebook.com/ajax/mercury/thread_info.php?dpr=2'

        res = self.session.post(url, data=post_data, timeout=60)
        src = str(res.text)
        src = src.replace('for (;;);', '')

        # remove for (;;); so we can turn them into dictionaries
        return json.loads(src)["payload"]["actions"]


    # marks a conversation as read
    def mark_message_read(self, page_id, conversation_id):

        # ids[100009492322860]=true
        # &source=message_dialog_shown
        # &watermarkTimestamp=1460871082261
        # &shouldSendReadReceipt=true&

        post_data = {
            'ids[' + conversation_id + ']': 'true',
            'source': 'message_dialog_shown',
            'shouldSendReadReceipt': 'true',
            'client': 'mercury',
            'request_user_id': page_id,
            '__user': self.user_id,
            '__a': '1',
            '__req': '19',
            '__be': '0',
            'fb_dtsg': self.dtsg,
            '__rev': '2288795'
        }

        url = 'https://www.facebook.com/ajax/mercury/change_read_status.php?dpr=1'

        res = self.session.post(url, data=post_data, timeout=60)
        src = str(res.text)
        src = src.replace('for (;;);', '')

    def send_message(self, page_id, conversation_id, sender_id, recipient_id, message_content):

        #message_batch[0][action_type]	ma-type:user-generated-message

        # timestamp = =

        message_id = str(randint(1000000000, 9999999999)) + str(randint(100000000, 999999999))

        post_data = {
            'message_batch[0][action_type]': 'ma-type:user-generated-message',
            'message_batch[0][thread_id]': '',
            'message_batch[0][author]': 'fbid:%s' % sender_id,
            'message_batch[0][author_email]': '',
            'message_batch[0][timestamp]': str(int(time.time())), # set me to epoch timestamp
            'message_batch[0][timestamp_absolute]': 'Today',
            'message_batch[0][timestamp_relative]': str(time.strftime("%I:%M%p")).lower(), # set me
            'message_batch[0][timestamp_time_passed]': '0',
            'message_batch[0][is_unread]': 'false',
            'message_batch[0][is_forward]': 'false',
            'message_batch[0][is_filtered_content]': 'false',
            'message_batch[0][is_filtered_content_bh]': 'false',
            'message_batch[0][is_filtered_content_account]': 'false',
            'message_batch[0][is_filtered_content_quasar]': 'false',
            'message_batch[0][is_filtered_content_invalid_app]': 'false',
            'message_batch[0][is_spoof_warning]': 'false',
            'message_batch[0][source]': 'source:titan:web',
            'message_batch[0][body]': message_content,
            'message_batch[0][has_attachment]': 'false',
            'message_batch[0][html_body]': 'false',
            'message_batch[0][specific_to_list][0]': 'fbid:%s' % conversation_id,
            'message_batch[0][specific_to_list][1]': 'fbid:%s' % page_id,
            'message_batch[0][creator_info]': '',
            'message_batch[0][status]': '0',
            'message_batch[0][offline_threading_id]': message_id,
            'message_batch[0][message_id]': message_id,
            'message_batch[0][ephemeral_ttl_mode]': '0',
            'message_batch[0][manual_retry_cnt]': '0',
            'message_batch[0][other_user_fbid]': recipient_id,

            'client': 'mercury',
            'request_user_id': page_id,
            '__user': self.user_id,
            '__a': '1',
            '__req': '19',
            '__be': '0',
            'fb_dtsg': self.dtsg,
            '__rev': '2288795'
        }

        url = 'https://www.facebook.com/ajax/mercury/send_messages.php?dpr=2'

        res = self.session.post(url, data=post_data, timeout=60)
        src = str(res.text)
        src = src.replace('for (;;);', '')

    def pull_message(self, sticky, pool, seq='0'):
        '''
        Call pull api with seq value to get message data.
        '''
        url = 'https://0-edge-chat.facebook.com/pull?channel=p_{user_id}&partition=-2&clientid=3396bf29&cb=gr6l&idle=0&cap=8&msgs_recv=0&uid={user_id}&viewer_uid={user_id}&state=active&seq={seq}&sticky_token={sticky}&sticky_pool={pool}'

        # call pull api, and set timeout as one minute
        res = self.session.get(
            url.format(user_id=self.user_id, seq=seq, sticky=sticky, pool=pool),
            timeout=60)

        # remove for (;;); so we can turn them into dictionaries
        content = json.loads(re.sub('for \(;;\); ', '', res.text))

        # get seq from response
        seq = content.get('seq', '0')
        log.debug('seq: %s', seq)

        return content, seq

    def _login(self, email, password):
        log.debug('loging in')

        # get login form datas
        res = self.session.get(LOGIN_URL)

        # check status code is 200 before proceeding
        if res.status_code != 200:
            raise LoginError('Status code is {}'.format(res.status_code))

        # get login form and add email and password fields
        datas = self._get_login_form(res.text)
        datas['email'] = email
        datas['pass'] = password

        # call login API with login form
        res = self.session.post(LOGIN_URL, data=datas)

        # get user id
        self.user_id = self._get_user_id(res.text)
        log.debug('user_id: %s', self.user_id)

        # get facebook dtsg
        self.dtsg = self._get_dtsg(res.text)
        log.debug('dtsg: %s', self.dtsg)

        log.info('welcome %s', self.user_id)


    def get_sticky(self):
        '''
        Call pull api to get sticky and pool parameter,
        newer api needs these parameter to work.
        '''
        url = 'https://0-edge-chat.facebook.com/pull?channel=p_{user_id}&partition=-2&clientid=3396bf29&cb=gr6l&idle=0&cap=8&msgs_recv=0&uid={user_id}&viewer_uid={user_id}&state=active&seq=0'

        # call pull api, and set timeout as one minute
        res = self.session.get(url.format(user_id=self.user_id), timeout=60)

        # remove for (;;); so we can turn them into dictionaries
        content = json.loads(re.sub('for \(;;\); ', '', res.text))

        # check existence of lb_info
        if 'lb_info' not in content:
            raise Exception('Get sticky pool error')

        sticky = content['lb_info']['sticky']
        pool = content['lb_info']['pool']

        return sticky, pool


    def _get_login_form(self, content):
        '''Scrap post datas from login page.'''
        # get login form
        root = etree.HTML(content)
        form = root.xpath('//form[@id="login_form"][1]')

        # can't find form tag
        if not form:
            raise LoginError('No form datas')

        fields = {}
        # get all input tags in this form
        for input in form[0].xpath('.//input'):
            name = input.xpath('@name[1]')
            value = input.xpath('@value[1]')
            log.debug('name: %s, value: %s' % (name, value))

            # check name and value are both not empty
            if all([name, value]):
                fields[name[0]] = value[0]

        return fields

    def _get_user_id(self, content):
        '''Find user id in the facebook page.'''
        m = re.search('\"USER_ID\":\"(\d+)\"', content)
        if m:
            # if user_id is 0, there is something wrong
            if m.group(1) == '0':
                raise LoginError('User id is 0')
            else:
                return m.group(1)
        else:
            raise LoginError('No user id')

    def _get_dtsg(self, content):
        '''Find dtsg value in the facebook page.'''
        m = re.search('name=\"fb_dtsg\" value=\"(.*?)\"', content)
        if m:
            return m.group(1)
        else:
            raise LoginError('No facebook dtsg')

    def get_access_token(self, app_id='145634995501895'):
        '''Register an access token in graph api console.'''
        # get response of registering access token
        res = self.session.get(ACCESS_TOKEN_URL.format(app_id, self.user_id))
        # remove for (;;); so we can load content in json format
        content = json.loads(re.sub('for \(;;\);', '', res.text))

        # try to get access token inside a complex structure
        try:
            token = content['jsmods']['instances'][2][2][2]
        except KeyError:
            token = ''

        return token

    def send_group(self, *args, **kwargs):
        '''Send message to specific group.'''
        send_group(self, *args, **kwargs)

    def send_person(self, *args, **kwargs):
        '''Send message to specific user.'''
        send_person(self, *args, **kwargs)

    def ping(self):
        '''Tell facebook that client is alive.'''
        res = self.session.get(PING_URL.format(user_id=self.user_id))
        log.debug(res.text)
        # check pong is in response text
        return 'pong' in res.text

    def get_stickers(self, *args, **kwargs):
        '''Get all stickers by giving one sticker bundle id.'''
        return get_stickers(self, *args, **kwargs)

    def group_typing(self, *args, **kwargs):
        '''Tell everyone in group that current user is typing.'''
        return group_typing(self, *args, **kwargs)

    def person_typing(self, *args, **kwargs):
        '''Tell specific user that current user is typing.'''
        return person_typing(self, *args, **kwargs)

    def read(self, *args, **kwargs):
        '''Read messages of this conversation.'''
        return read(self, *args, **kwargs)

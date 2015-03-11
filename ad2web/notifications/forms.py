# -*- coding: utf-8 -*-

import json
from flask.ext.wtf import Form
from flask.ext.wtf.html5 import URLField, EmailField, TelField
import wtforms
from wtforms import (ValidationError, HiddenField, TextField, HiddenField,
        PasswordField, SubmitField, TextAreaField, IntegerField, RadioField,
        FileField, DecimalField, BooleanField, SelectField, FormField, FieldList,
        SelectMultipleField)
from wtforms.validators import (Required, Length, EqualTo, Email, NumberRange,
        URL, AnyOf, Optional)
from wtforms.widgets import ListWidget, CheckboxInput
from .constants import (NOTIFICATIONS, NOTIFICATION_TYPES, SUBSCRIPTIONS, DEFAULT_SUBSCRIPTIONS, EMAIL, GOOGLETALK, PUSHOVER)
from .models import NotificationSetting
from ..widgets import ButtonField, MultiCheckboxField


class NotificationButtonForm(wtforms.Form):
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications'")
    submit = SubmitField(u'Save')
    test = SubmitField(u'Save & Test')


class CreateNotificationForm(Form):
    type = SelectField(u'Notification Type', choices=[nt for t, nt in NOTIFICATIONS.iteritems()])

    submit = SubmitField(u'Next')
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications'")


class EditNotificationMessageForm(Form):
    id = HiddenField()
    text = TextAreaField(u'Message Text', [Required(), Length(max=255)])

    submit = SubmitField(u'Save')
    cancel = ButtonField(u'Cancel', onclick="location.href='/settings/notifications/messages'")


class EditNotificationForm(Form):
    type = HiddenField()
    description = TextField(u'Description', [Required(), Length(max=255)], description=u'Brief description of this notification')
    subscriptions = MultiCheckboxField(u'Notify on..', choices=[(str(k), v) for k, v in SUBSCRIPTIONS.iteritems()])

    def populate_settings(self, settings, id=None):
        settings['subscriptions'] = self.populate_setting('subscriptions', json.dumps({str(k): True for k in self.subscriptions.data}))

    def populate_from_settings(self, id):
        subscriptions = self.populate_from_setting(id, 'subscriptions')
        if subscriptions:
            self.subscriptions.data = [k if v == True else False for k, v in json.loads(subscriptions).iteritems()]

    def populate_setting(self, name, value, id=None):
        if id is not None:
            setting = NotificationSetting.query.filter_by(notification_id=id, name=name).first()
        else:
            setting = NotificationSetting(name=name)

        setting.value = value

        return setting

    def populate_from_setting(self, id, name, default=None):
        ret = default

        setting = NotificationSetting.query.filter_by(notification_id=id, name=name).first()
        if setting is not None:
            ret = setting.value

        return ret


class EmailNotificationForm(EditNotificationForm):
    source = TextField(u'Source Address', [Required(), Length(max=255)], default='root@localhost', description=u'Emails will originate from this address')
    destination = TextField(u'Destination Address', [Required(), Length(max=255)], description=u'Emails will be sent to this address')

    subject = TextField(u'Email Subject', [Required(), Length(max=255)], default='AlarmDecoder: Alarm Event', description=u'Emails will contain this text as the subject')

    server = TextField(u'Email Server', [Required(), Length(max=255)], default='localhost')
    port = IntegerField(u'Server Port', [Required(), NumberRange(1, 65535)], default=25)
    tls = BooleanField(u'Use TLS?', default=False)
    authentication_required = BooleanField(u'Authenticate with email server?', default=False)
    username = TextField(u'Username', [Optional(), Length(max=255)])
    password = PasswordField(u'Password', [Optional(), Length(max=255)])

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        EditNotificationForm.populate_settings(self, settings, id)

        settings['source'] = self.populate_setting('source', self.source.data)
        settings['destination'] = self.populate_setting('destination', self.destination.data)
        settings['subject'] = self.populate_setting('subject', self.subject.data)
        settings['server'] = self.populate_setting('server', self.server.data)
        settings['port'] = self.populate_setting('port', self.port.data)
        settings['tls'] = self.populate_setting('tls', self.tls.data)
        settings['authentication_required'] = self.populate_setting('authentication_required', self.authentication_required.data)
        settings['username'] = self.populate_setting('username', self.username.data)
        settings['password'] = self.populate_setting('password', self.password.data)

    def populate_from_settings(self, id):
        EditNotificationForm.populate_from_settings(self, id)

        self.source.data = self.populate_from_setting(id, 'source')
        self.destination.data = self.populate_from_setting(id, 'destination')
        self.subject.data = self.populate_from_setting(id, 'subject')
        self.server.data = self.populate_from_setting(id, 'server')
        self.tls.data = self.populate_from_setting(id, 'tls')
        self.port.data = self.populate_from_setting(id, 'port')
        self.authentication_required.data = self.populate_from_setting(id, 'authentication_required')
        self.username.data = self.populate_from_setting(id, 'username')
        self.password.widget.hide_value = False
        self.password.data = self.populate_from_setting(id, 'password')


class GoogleTalkNotificationForm(EditNotificationForm):
    source = TextField(u'Source Address', [Required(), Length(max=255)], default='root@localhost', description=u'Messages will originate from this address')
    password = PasswordField(u'Password', [Required(), Length(max=255)], description=u'Password for the source account')
    destination = TextField(u'Destination Address', [Required(), Length(max=255)], description=u'Messages will be sent to this address')

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        settings['source'] = self.populate_setting('source', self.source.data)
        settings['password'] = self.populate_setting('password', self.password.data)
        settings['destination'] = self.populate_setting('destination', self.destination.data)

    def populate_from_settings(self, id):
        self.source.data = self.populate_from_setting(id, 'source')
        self.password.widget.hide_value = False
        self.password.data = self.populate_from_setting(id, 'password')
        self.destination.data = self.populate_from_setting(id, 'destination')

class PushoverNotificationForm(EditNotificationForm):
    token = TextField(u'API Token', [Required(), Length(max=30)], description=u'Your Application\'s API Token')
    user_key = TextField(u'User/Group Key', [Required(), Length(max=30)], description=u'Your user or group key')
    title = TextField(u'Title of Message', [Length(max=255)], description=u'Title of Notification Messages')

    buttons = FormField(NotificationButtonForm)

    def populate_settings(self, settings, id=None):
        settings['token'] = self.populate_setting('token', self.token.data)
        settings['user_key'] = self.populate_setting('user_key', self.user_key.data)
        settings['title'] = self.populate_setting('title', self.title.data)

    def populate_from_settings(self, id):
        self.token.data = self.populate_from_setting(id, 'token')
        self.user_key.data = self.populate_from_setting(id, 'user_key')
        self.title.data = self.populate_from_setting(id, 'title')

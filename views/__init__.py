# coding=utf-8
from tornado.web import RequestHandler
from tornado import gen

from models.user import User


class BaseHandler(RequestHandler):

    def initialize(self):
        self.db_session = self.application.db_pool()
        self.async_do = self.application.thread_pool.submit
        # session related
        self.session = self.application.session_manager.make_session(self)
        self.session_remove_flag = False

    @gen.coroutine
    def prepare(self):
        """ NOTE: We need to get current_user in prepare(),
                because get_current_user() cannot be a coroutine!
        """
        user_id = yield self.session.get_user_id()
        if user_id:
            user = yield self.async_do(User.get_user_by_id, 
                self.db_session, user_id)
            if user:
                self.current_user = user

    @gen.coroutine
    def login_user(self, user):
        self.session.generate_sessionid(user)
        yield self.session.save()

    def logout_user(self):
        self.session_remove_flag = True
        self.session.remove_sessionid()

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('errors/404.html')

    @gen.coroutine
    def on_finish(self):
        if self.db_session:
            self.db_session.close()
        if self.session_remove_flag:
            yield self.session.remove()
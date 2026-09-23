from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.session import Session


class SessionWebsite(Session):

    @http.route()
    def authenticate(self, db, login, password, base_location=None):
        # JDE reads the session id from the JSON body instead of the cookie.
        # Core already rotates and saves the session inside authenticate(), so
        # request.session.sid is the final value here.
        res = super().authenticate(db, login, password, base_location=base_location)
        if isinstance(res, dict) and res.get('uid'):
            res['session_id'] = request.session.sid
        return res

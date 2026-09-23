# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
# Migrated to Odoo 19.0 by Plennix Technologies for its licensee.
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    setup_provider(env, 'applepay')


def uninstall_hook(env):
    reset_payment_provider(env, 'applepay')

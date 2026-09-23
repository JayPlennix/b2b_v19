# -*- coding: utf-8 -*-
import collections
import json
import logging

from odoo import SUPERUSER_ID, api
from odoo.http import JsonRPCDispatcher

_logger = logging.getLogger(__name__)


class PlennixSystemMonitor(JsonRPCDispatcher):
    """ Record every error returned to a JSON-RPC call (web client, website, APIs). """

    def handle_error(self, exc: Exception) -> collections.abc.Callable:
        result = super().handle_error(exc)
        try:
            self._log_system_error(result)
        except Exception:  # noqa: BLE001
            # Monitoring must never replace the original error sent to the user.
            _logger.exception("System Monitor: could not log the error")
        return result

    def _log_system_error(self, result):
        env = self.request.env
        if env is None:
            return  # no database for this request
        req = self.jsonrequest or {}
        params = req.get('params') or {}
        if not isinstance(params, dict):
            params = {}
        kwargs = params.get('kwargs')
        context = (kwargs.get('context') if isinstance(kwargs, dict) else None) or {}
        response = json.loads(result.data)
        error_data = response.get('error', {}).get('data', {})

        # The request transaction failed (and may be read-only): log in a transaction of its own.
        with env.registry.cursor() as cr:
            monitor_env = api.Environment(cr, SUPERUSER_ID, {})
            company_ids = context.get('allowed_company_ids') or []
            monitor_env['system.monitor.log'].create({
                # Request Params
                'method': params.get('method'),
                'method_args': str(params['args']) if params.get('args') is not None else False,
                'model': params.get('model'),
                'allowed_companies_ids': [(6, 0, monitor_env['res.company'].browse(company_ids).exists().ids)],
                'lang': context.get('lang'),
                'tz': context.get('tz'),
                'user_id': env.uid or False,
                # Response Params
                'stacktrace': error_data.get('debug'),
                'exception': error_data.get('name'),
                'description': error_data.get('message'),
                # Raw
                'request': json.dumps(req, indent=4, sort_keys=True, default=str),
                'response': json.dumps(response, indent=4, sort_keys=True, default=str),
            })

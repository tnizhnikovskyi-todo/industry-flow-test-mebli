from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError

SLOT_HOURS = 2  # a measurement visit with the road


class TdMebliMeasureBooking(models.TransientModel):
    """Position 9: free windows of the measurer and the booking of a visit.

    The windows are the working hours of the company calendar (standard resource.calendar) minus the meetings of the
    measurer (standard calendar.event). The booking is a standard meeting of the opportunity (crm: calendar.event
    .opportunity_id) with the customer as an attendee and the standard e-mail alarm a day before: the reminder to the
    customer is sent by the standard calendar alarm (calendar_template_meeting_reminder). Nothing is kept here."""
    _name = 'td.mebli.measure.booking'
    _description = 'Booking of a Measurement Visit'

    lead_id = fields.Many2one('crm.lead', string='Opportunity', required=True)
    partner_id = fields.Many2one(related='lead_id.partner_id', string='Customer')
    measurer_id = fields.Many2one('res.users', string='Measurer', required=True,
                                  default=lambda self: self._td_default_measurer())
    date_from = fields.Date(string='From', required=True, default=lambda self: fields.Date.context_today(self) + timedelta(days=1))
    days = fields.Integer(string='Days', default=5)
    slot_ids = fields.One2many('td.mebli.measure.slot', 'booking_id', string='Free Windows')
    no_slot_text = fields.Char(string='No Windows', compute='_compute_no_slot_text')

    @api.depends('slot_ids')
    @api.depends_context('lang')
    def _compute_no_slot_text(self):
        """AC-003: the calendar of the measurer is busy for the whole period — say so; nothing can be booked."""
        for booking in self:
            booking.no_slot_text = False if booking.slot_ids else self.env._(
                "No free windows in the chosen period — increase the number of days or choose another measurer")

    @api.model
    def _td_default_measurer(self):
        """The first measurer of the company (group «Measurer»), else the user who books."""
        group = self.env.ref('td_mebli_measure.group_td_mebli_measurer', raise_if_not_found=False)
        # sudo: read only: the members of the group «Measurer» (res.groups is admin only)
        measurers = group.sudo().all_user_ids.filtered(
            lambda u: u.active and not u.share and self.env.company in u.company_ids) if group else self.env['res.users']
        return measurers.sorted('id')[:1] or self.env.user

    def _td_tz(self):
        return pytz.timezone(self.measurer_id.tz or self.env.user.tz or 'Europe/Kyiv')

    def _td_free_slots(self):
        """[(start, stop)] in UTC, naive: working intervals of the company calendar minus the meetings of the measurer."""
        self.ensure_one()
        tz = self._td_tz()
        start = tz.localize(datetime.combine(self.date_from, time.min))
        end = start + timedelta(days=max(self.days, 1))
        now = pytz.utc.localize(fields.Datetime.now())
        calendar = self.measurer_id.resource_calendar_id or self.env.company.resource_calendar_id
        work = calendar._work_intervals_batch(start, end, tz=tz)[False]
        # sudo: read only: the busy time of the measurer, also the private events the salesperson does not see
        busy = self.env['calendar.event'].sudo().search([
            ('partner_ids', 'in', self.measurer_id.partner_id.ids), ('start', '<', end.astimezone(pytz.utc).replace(tzinfo=None)),
            ('stop', '>', start.astimezone(pytz.utc).replace(tzinfo=None))])
        busy_intervals = [(pytz.utc.localize(e.start), pytz.utc.localize(e.stop)) for e in busy]
        slots = []
        for begin, finish, _records in work:
            cursor = begin
            while cursor + timedelta(hours=SLOT_HOURS) <= finish:
                stop = cursor + timedelta(hours=SLOT_HOURS)
                if cursor > now and not any(b0 < stop and b1 > cursor for b0, b1 in busy_intervals):
                    slots.append((cursor.astimezone(pytz.utc).replace(tzinfo=None), stop.astimezone(pytz.utc).replace(tzinfo=None)))
                cursor = stop
        return slots

    def _td_fill_slots(self):
        for booking in self:
            booking.slot_ids = [(5, 0, 0)] + [(0, 0, {'start': a, 'stop': b}) for a, b in booking._td_free_slots()]

    @api.onchange('measurer_id', 'date_from', 'days')
    def _onchange_td_slots(self):
        self._td_fill_slots()

    def action_refresh(self):
        self._td_fill_slots()
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'target': 'new', 'name': self.env._("Book a Measurement")}

    def _td_book(self, slot):
        self.ensure_one()
        lead = self.lead_id
        # the window was free when the list was shown: another salesperson may have booked it since
        # sudo: read only: the busy time of the measurer, also the private events the salesperson does not see
        busy = self.env['calendar.event'].sudo().search_count([
            ('partner_ids', 'in', self.measurer_id.partner_id.ids), ('start', '<', slot.stop), ('stop', '>', slot.start)],
            limit=1)
        if busy:
            raise UserError(self.env._("The window %(day)s %(when)s of %(who)s is already taken: refresh the free windows "
                                       "and choose another one.", day=slot.day.strftime('%d.%m.%Y'), when=slot.label,
                                       who=self.measurer_id.name))
        partners = self.measurer_id.partner_id | lead.partner_id
        alarm = self.env.ref('td_mebli_measure.alarm_mail_measure_1day', raise_if_not_found=False)
        event = self.env['calendar.event'].with_context(default_opportunity_id=lead.id).create({
            'name': self.env._("Measurement: %s", lead.partner_id.name or lead.contact_name or lead.name),
            'start': slot.start, 'stop': slot.stop, 'user_id': self.measurer_id.id,
            'partner_ids': [(6, 0, partners.ids)], 'opportunity_id': lead.id,
            'location': ', '.join(filter(None, [lead.partner_id.street, lead.partner_id.city])) or False,
            'alarm_ids': [(6, 0, alarm.ids)],
            'description': self.env._("Measurement of the room: niches, appliances, utilities."),
        })
        lead.message_post(body=self.env._("Measurement booked: %(day)s %(when)s, %(who)s.", day=slot.day.strftime('%d.%m.%Y'),
                                          when=slot.label, who=self.measurer_id.name))
        return event


class TdMebliMeasureSlot(models.TransientModel):
    _name = 'td.mebli.measure.slot'
    _description = 'Free Window of the Measurer'
    _order = 'start'

    booking_id = fields.Many2one('td.mebli.measure.booking', required=True, ondelete='cascade')
    start = fields.Datetime(string='Start', required=True)
    stop = fields.Datetime(string='End', required=True)
    day = fields.Date(string='Day', compute='_compute_label')
    label = fields.Char(string='Window', compute='_compute_label')

    @api.depends('start', 'stop')
    def _compute_label(self):
        for slot in self:
            tz = slot.booking_id._td_tz() if slot.booking_id.measurer_id else pytz.timezone('Europe/Kyiv')
            if not slot.start:
                slot.label = slot.day = False
                continue
            begin = pytz.utc.localize(slot.start).astimezone(tz)
            end = pytz.utc.localize(slot.stop).astimezone(tz)
            slot.day = begin.date()
            slot.label = f"{begin.strftime('%H:%M')}–{end.strftime('%H:%M')}"

    def action_book(self):
        self.ensure_one()
        if not self.booking_id.lead_id:
            raise UserError(self.env._("No opportunity to book the measurement for."))
        event = self.booking_id._td_book(self)
        return {'type': 'ir.actions.act_window', 'res_model': 'calendar.event', 'res_id': event.id, 'view_mode': 'form',
                'views': [(False, 'form')], 'target': 'current'}
